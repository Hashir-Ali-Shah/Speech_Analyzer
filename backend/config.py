"""
SpeakBetter Local — Centralized Configuration
All tunable parameters live here. No hardcoded values elsewhere.
"""

# ─── Whisper Models ───────────────────────────────────────────────
AVAILABLE_MODELS = ["base", "medium"]
DEFAULT_MODEL = "base"

WHISPER_DEVICE = "auto"              # "cpu", "cuda", or "auto"
WHISPER_COMPUTE_TYPE = "int8"        # int8 is fastest on CPU; use float16 for GPU

# Keep for backward compat (used at startup log)
WHISPER_MODEL_SIZE = DEFAULT_MODEL

# ─── Recording Constraints ────────────────────────────────────────
MIN_RECORDING_SECONDS = 30
MAX_RECORDING_SECONDS = 120

# ─── Filler Words ─────────────────────────────────────────────────
# Single-word fillers (case-insensitive matching)
SINGLE_FILLERS = ["uh", "um", "like", "basically", "actually"]

# Multi-word fillers (matched as phrases)
MULTI_FILLERS = ["you know"]

# "so" is only a filler when it starts a sentence
SENTENCE_START_FILLERS = ["so"]

# Combined for display purposes
ALL_FILLER_LABELS = SINGLE_FILLERS + MULTI_FILLERS + SENTENCE_START_FILLERS

# ─── Pause Analysis ───────────────────────────────────────────────
PAUSE_THRESHOLD_SECONDS = 1.0       # Pauses longer than this are counted

# ─── Repetition Analysis ──────────────────────────────────────────
MIN_PHRASE_LENGTH = 2               # Minimum words in a repeated phrase
MAX_PHRASE_LENGTH = 3               # Maximum words in a repeated phrase

# ─── Server ───────────────────────────────────────────────────────
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8690

# ─── Paths ────────────────────────────────────────────────────────
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
MODEL_CACHE_DIR = os.path.join(PROJECT_ROOT, "models")
