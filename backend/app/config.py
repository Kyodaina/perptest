from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_ROOT = BASE_DIR.parent
UPLOAD_DIR = APP_ROOT / "uploads"
MODEL_CACHE_DIR = APP_ROOT / "models"
STATIC_DIR = BASE_DIR / "static"

MAX_WORKERS = 2
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
QWEN_MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
