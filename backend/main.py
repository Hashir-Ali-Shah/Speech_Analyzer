from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
from io import BytesIO
from backend.transcription import transcribe_audio, transcribe_audio_chunk
from backend.metrics import compute_all_metrics
from backend.topics import get_random_topic, get_topic_by_category, get_all_categories
from backend.config import FRONTEND_DIR, AVAILABLE_MODELS, DEFAULT_MODEL, PROJECT_ROOT
from backend.audio_chunks import AudioChunker
import os
import json
import asyncio

app = FastAPI(
    title="SpeechLab",
    description="Offline speech analysis and fluency feedback tool.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/topic")
def api_get_topic(category: str = None):
    try:
        if category:
            return get_topic_by_category(category)
        return get_random_topic()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/categories")
def api_get_categories():
    return {"categories": get_all_categories()}


@app.get("/api/models")
def api_get_models():
    return {
        "models": AVAILABLE_MODELS,
        "default": DEFAULT_MODEL,
    }


def _compute_audio_duration(audio_bytes: bytes) -> float:
    audio_seg = AudioSegment.from_file(BytesIO(audio_bytes))
    return len(audio_seg) / 1000.0


def _merge_chunk_results(chunk_results: list) -> dict:
    chunk_results.sort(key=lambda x: x["start_time"])

    merged_transcript_parts = []
    merged_word_timestamps = []
    model_used = None

    for chunk in chunk_results:
        result = chunk["result"]
        offset_seconds = chunk["start_time"] / 1000.0
        model_used = result.get("model_used", model_used)

        merged_transcript_parts.append(result["transcript"])

        for wt in result.get("word_timestamps", []):
            merged_word_timestamps.append({
                "word": wt["word"],
                "start": round(wt["start"] + offset_seconds, 3),
                "end": round(wt["end"] + offset_seconds, 3),
            })

    return {
        "transcript": " ".join(merged_transcript_parts),
        "word_timestamps": merged_word_timestamps,
        "model_used": model_used or DEFAULT_MODEL,
    }


@app.post("/api/analyze")
async def api_analyze(
    audio: UploadFile = File(...),
    model: str = Query(default=DEFAULT_MODEL, description="Whisper model size"),
    duration: float = Form(default=0),
):
    if model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model: {model}. Available: {AVAILABLE_MODELS}",
        )

    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        actual_duration = _compute_audio_duration(audio_bytes)

        if actual_duration > 30:
            chunker = AudioChunker()
            chunks, _ = chunker.split_audio_bytes(audio_bytes)

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=min(len(chunks), 4)) as executor:
                chunk_results = list(await asyncio.gather(
                    *[loop.run_in_executor(executor, transcribe_audio_chunk, chunk)
                      for chunk in chunks]
                ))

            merged = _merge_chunk_results(chunk_results)
            transcript = merged["transcript"]
            word_timestamps = merged["word_timestamps"]
            model_used = merged["model_used"]
        else:
            result = transcribe_audio(audio_bytes, model_size=model)
            transcript = result["transcript"]
            word_timestamps = result["word_timestamps"]
            model_used = result["model_used"]

        if not transcript.strip():
            raise HTTPException(status_code=422, detail="No speech detected in the audio.")

        metrics = compute_all_metrics(transcript, actual_duration, word_timestamps)

        return {
            "transcript": transcript,
            "duration_seconds": actual_duration,
            "word_timestamps": word_timestamps,
            "metrics": metrics,
            "model_used": model_used,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


SESSION_FILE = os.path.join(PROJECT_ROOT, "sessions.json")


@app.get("/api/sessions")
def api_get_sessions():
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, IOError):
        return []


@app.post("/api/sessions")
async def api_save_sessions(request: Request):
    try:
        sessions = await request.json()
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        return {"status": "ok", "count": len(sessions)}
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save sessions: {str(e)}")


@app.delete("/api/sessions")
def api_clear_sessions():
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        return {"status": "ok"}
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear sessions: {str(e)}")


app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
