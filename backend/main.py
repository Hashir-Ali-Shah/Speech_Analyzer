"""
SpeakBetter Local — FastAPI Application
Single API server with /analyze, /topic, and /models endpoints.
Serves the frontend as static files.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.transcription import transcribe_audio
from backend.metrics import compute_all_metrics
from backend.topics import get_random_topic, get_topic_by_category, get_all_categories
from backend.config import FRONTEND_DIR, AVAILABLE_MODELS, DEFAULT_MODEL, PROJECT_ROOT

import os
import json

app = FastAPI(
    title="SpeakBetter Local",
    description="Offline speech analysis and fluency feedback tool.",
    version="1.0.0",
)

# CORS — allow local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── API Endpoints ────────────────────────────────────────────────

@app.get("/api/topic")
def api_get_topic(category: str = None):
    """Return a random speaking topic, optionally filtered by category."""
    try:
        if category:
            return get_topic_by_category(category)
        return get_random_topic()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/categories")
def api_get_categories():
    """Return all available topic categories."""
    return {"categories": get_all_categories()}


@app.get("/api/models")
def api_get_models():
    """Return available STT model options."""
    return {
        "models": AVAILABLE_MODELS,
        "default": DEFAULT_MODEL,
    }


@app.post("/api/analyze")
async def api_analyze(
    audio: UploadFile = File(...),
    model: str = Query(default=DEFAULT_MODEL, description="Whisper model size"),
):
    """
    Accept an audio file, transcribe it, and return metrics.
    Supports model selection via ?model=base|medium query param.
    """
    # Validate model choice
    if model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model: {model}. Available: {AVAILABLE_MODELS}",
        )

    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        # Step 1: Transcribe with selected model
        result = transcribe_audio(audio_bytes, model_size=model)
        transcript = result["transcript"]
        duration = result["duration_seconds"]
        word_timestamps = result["word_timestamps"]

        if not transcript.strip():
            raise HTTPException(status_code=422, detail="No speech detected in the audio.")

        # Step 2: Compute metrics
        metrics = compute_all_metrics(transcript, duration, word_timestamps)

        return {
            "transcript": transcript,
            "duration_seconds": duration,
            "word_timestamps": word_timestamps,
            "metrics": metrics,
            "model_used": result["model_used"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ─── Session History (file-based) ─────────────────────────────────

SESSION_FILE = os.path.join(PROJECT_ROOT, "sessions.json")


@app.get("/api/sessions")
def api_get_sessions():
    """Load sessions from disk."""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, IOError):
        return []


@app.post("/api/sessions")
async def api_save_sessions(request: Request):
    """Save sessions to disk (replaces file contents)."""
    try:
        sessions = await request.json()
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        return {"status": "ok", "count": len(sessions)}
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save sessions: {str(e)}")


@app.delete("/api/sessions")
def api_clear_sessions():
    """Delete sessions file."""
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        return {"status": "ok"}
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear sessions: {str(e)}")


# ─── Static File Serving ──────────────────────────────────────────

# Serve frontend static assets (CSS, JS)
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


@app.get("/")
def serve_frontend():
    """Serve the main HTML page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
