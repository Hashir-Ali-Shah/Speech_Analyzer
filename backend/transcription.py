import tempfile
import os
from dotenv import load_dotenv
from typing import Optional
from faster_whisper import WhisperModel
from backend.config import AVAILABLE_MODELS, DEFAULT_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE

load_dotenv()


class TranscriptionService:

    _instance: Optional["TranscriptionService"] = None
    _models: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._models = {}
        return cls._instance

    def _ensure_model(self, model_size: str):
        if model_size not in AVAILABLE_MODELS:
            raise ValueError(
                f"Unknown model: {model_size}. Available: {AVAILABLE_MODELS}"
            )

        if model_size not in self._models:
            print(f"[TranscriptionService] Loading whisper model: {model_size}")
            model_path = os.getenv(model_size.upper())
            self._models[model_size] = WhisperModel(
                model_path,
                device=WHISPER_DEVICE,
                compute_type=WHISPER_COMPUTE_TYPE,
            )
            print(f"[TranscriptionService] Model '{model_size}' loaded successfully.")

    def get_loaded_models(self) -> list[str]:
        return list(self._models.keys())

    def transcribe(self, audio_bytes: bytes, model_size: str = DEFAULT_MODEL) -> dict:
        self._ensure_model(model_size)
        model = self._models[model_size]

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            segments, info = model.transcribe(
                tmp_path,
                beam_size=5,
                word_timestamps=True,
                vad_filter=False,
                initial_prompt="Um, uh, like, you know, basically, actually, so,",
            )

            transcript_parts = []
            word_timestamps = []

            for segment in segments:
                transcript_parts.append(segment.text.strip())
                if segment.words:
                    for word_info in segment.words:
                        word_timestamps.append({
                            "word": word_info.word.strip(),
                            "start": round(word_info.start, 3),
                            "end": round(word_info.end, 3),
                        })

            transcript = " ".join(transcript_parts)
            duration = round(info.duration, 2)

            return {
                "transcript": transcript,
                "duration_seconds": duration,
                "word_timestamps": word_timestamps,
                "model_used": model_size,
            }

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)


def transcribe_audio(audio_bytes: bytes, model_size: str = DEFAULT_MODEL) -> dict:
    service = TranscriptionService()
    return service.transcribe(audio_bytes, model_size)


def transcribe_audio_chunk(chunk: dict) -> dict:
    service = TranscriptionService()
    result = service.transcribe(chunk["audio_bytes"])

    return {
        "result": result,
        "start_time": chunk["start_time"],
        "end_time": chunk["end_time"],
    }
