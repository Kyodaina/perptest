from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
APP_ROOT = BASE_DIR.parent
UPLOAD_DIR = APP_ROOT / "uploads"
MODEL_CACHE_DIR = APP_ROOT / "models"
STATIC_DIR = BASE_DIR / "static"

MAX_WORKERS = 2
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
# 3B is the default for better local memory fit.
# Override with env var MODEL_ID when you want to use 7B.
QWEN_MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-VL-3B-Instruct")
MAX_IMAGE_EDGE = int(os.getenv("MAX_IMAGE_EDGE", "1280"))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
