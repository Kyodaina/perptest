from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
UPLOADS_DIR = BASE_DIR / "storage" / "uploads"
RESULTS_DIR = BASE_DIR / "storage" / "results"
STATIC_DIR = BASE_DIR / "static"

QWEN_MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"
QWEN_LOCAL_DIR = MODELS_DIR / "qwen2_5_vl"
WHISPER_MODEL_SIZE = "small"
WHISPER_LOCAL_DIR = MODELS_DIR / "whisper"

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}

for folder in (MODELS_DIR, UPLOADS_DIR, RESULTS_DIR, STATIC_DIR, QWEN_LOCAL_DIR, WHISPER_LOCAL_DIR):
    folder.mkdir(parents=True, exist_ok=True)
