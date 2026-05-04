from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
EXPORT_DIR = BASE_DIR / "exports"
MODEL_DIR = BASE_DIR / "models"

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a"}
MODEL_SIZE = "large-v3"
SAMPLE_RATE = 16000

for folder in (UPLOAD_DIR, TEMP_DIR, EXPORT_DIR, MODEL_DIR):
    folder.mkdir(parents=True, exist_ok=True)
