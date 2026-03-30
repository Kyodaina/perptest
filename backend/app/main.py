from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import configure, router
from app.services.job_manager import JobManager

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
STAGING_DIR = DATA_DIR / "staging"
OUTPUT_DIR = DATA_DIR / "outputs"
MODEL_DIR = BASE_DIR.parent / "models"

for d in [UPLOAD_DIR, STAGING_DIR, OUTPUT_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Ad Analyzer")
manager = JobManager(upload_dir=UPLOAD_DIR, output_dir=OUTPUT_DIR, model_root=MODEL_DIR)
configure(manager, STAGING_DIR)
app.include_router(router)

app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
