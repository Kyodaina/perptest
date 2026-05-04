from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.config import ALLOWED_EXTENSIONS, EXPORT_DIR, UPLOAD_DIR
from app.services.job_manager import job_manager

router = APIRouter(prefix="/api", tags=["transcription"])


def _save_upload(file: UploadFile) -> Path:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Nem támogatott fájlformátum. Csak wav, mp3, m4a.")

    destination = UPLOAD_DIR / file.filename
    with destination.open("wb") as out:
        out.write(file.file.read())
    return destination


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    path = _save_upload(file)
    job_id = job_manager.create_job(path)
    return {"job_id": job_id, "file_name": path.name}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nem található")

    return {
        "job_id": job.job_id,
        "file_name": job.file_name,
        "status": job.status,
        "progress": job.progress,
        "logs": job.logs,
        "result": job.result.model_dump() if job.result else None,
        "error": job.error,
    }


@router.get("/export/{job_id}/txt")
async def export_txt(job_id: str):
    job = job_manager.get(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="Nincs exportálható leirat")

    txt_path = EXPORT_DIR / f"{job_id}.txt"
    txt_path.write_text(job.result.formatted_transcript, encoding="utf-8")
    return FileResponse(txt_path, filename=f"{Path(job.file_name).stem}.txt", media_type="text/plain")


@router.get("/export/{job_id}/pdf")
async def export_pdf(job_id: str):
    job = job_manager.get(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="Nincs exportálható leirat")

    pdf_path = EXPORT_DIR / f"{job_id}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    y = height - 40

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont("DejaVu", font_path))
    c.setFont("DejaVu", 11)

    for line in job.result.formatted_transcript.splitlines():
        if y < 40:
            c.showPage()
            c.setFont("DejaVu", 11)
            y = height - 40
        c.drawString(40, y, line[:130])
        y -= 16

    c.save()
    return FileResponse(pdf_path, filename=f"{Path(job.file_name).stem}.pdf", media_type="application/pdf")
