import os


AVAILABLE_MODELS = ["base", "medium"]
DEFAULT_MODEL = "base"

WHISPER_DEVICE = "auto"
WHISPER_COMPUTE_TYPE = "int8"

WHISPER_MODEL_SIZE = DEFAULT_MODEL


SINGLE_FILLERS = ["uh", "um", "like", "basically", "actually"]

MULTI_FILLERS = ["you know"]

SENTENCE_START_FILLERS = ["so"]
ALL_FILLER_LABELS = SINGLE_FILLERS + MULTI_FILLERS + SENTENCE_START_FILLERS

PAUSE_THRESHOLD_SECONDS = 1.0

MIN_PHRASE_LENGTH = 2
MAX_PHRASE_LENGTH = 3

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8690


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
