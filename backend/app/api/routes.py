from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from app.services.job_manager import job_manager

router = APIRouter(prefix="/api", tags=["analysis"])


def _save_upload(file: UploadFile) -> Path:
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file: {file.filename}")

    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        f.write(file.file.read())
    return dest


@router.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    paths = [_save_upload(file) for file in files]
    job_id = job_manager.create_job(paths)
    return {"job_id": job_id, "files": [p.name for p in paths]}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    items = [
        {
            "file_name": state.file_name,
            "status": state.status,
            "progress": state.progress,
            "logs": state.logs,
            "output": state.output.model_dump() if state.output else None,
            "error": state.error,
        }
        for state in job.items.values()
    ]

    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "logs": job.logs,
        "items": items,
    }
