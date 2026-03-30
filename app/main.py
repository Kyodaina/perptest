import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR, SUPPORTED_IMAGE_EXTENSIONS, UPLOADS_DIR
from app.schemas import JobResponse, JobState, StartJobRequest, UploadItem, UploadResponse
from app.services.job_manager import job_manager

app = FastAPI(title="Ad Intelligence Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/uploads", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)) -> UploadResponse:
    items: list[UploadItem] = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

        dest = UPLOADS_DIR / f"{Path(file.filename).stem}_{id(file)}{ext}"
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        registered = job_manager.register_file(file.filename, dest, file.content_type or "application/octet-stream")
        items.append(
            UploadItem(
                file_id=registered.file_id,
                filename=registered.filename,
                media_type=registered.media_type,
            )
        )
    return UploadResponse(items=items)


@app.post("/api/jobs", response_model=JobResponse)
def start_job(payload: StartJobRequest) -> JobResponse:
    missing = [file_id for file_id in payload.file_ids if not job_manager.get_file(file_id)]
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown file_ids: {missing}")

    job_id = job_manager.create_job(payload.file_ids, payload.precision)
    return JobResponse(job_id=job_id)


@app.get("/api/jobs/{job_id}", response_model=JobState)
def get_job(job_id: str) -> JobState:
    try:
        return job_manager.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/files/{file_id}")
def get_file(file_id: str) -> FileResponse:
    file_data = job_manager.get_file(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path=file_data.path, media_type=file_data.media_type, filename=file_data.filename)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
