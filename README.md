# Local Ad Analyzer (Vision + Audio)

Production-ready local web app that analyzes advertisement images and videos using local VLMs + Whisper.

## Tech
- Backend: FastAPI, threaded background job processor
- AI: Hugging Face Transformers (Qwen2.5-VL / LLaVA), openai-whisper
- Media: OpenCV frame extraction + dedup
- Frontend: modern dashboard (drag/drop, progress, logs, timeline/results)

## Project Structure

```
backend/
  app/
    api/
      routes.py
    services/
      job_manager.py
      media_processor.py
      model_loader.py
      schemas.py
    static/
      css/styles.css
      js/app.js
      index.html
    main.py
  requirements.txt
models/                # downloaded model artifacts
```

## Features
- Multi-file drag/drop upload with progress
- Supports: jpg/png/webp/mp4/mov/avi
- Video pipeline:
  - frame extraction every 1-2 seconds (configurable)
  - perceptual deduplication (hash + SSIM)
  - frame-level structured marketing extraction (strict JSON schema)
  - audio transcription via Whisper with timestamps
- Image pipeline:
  - direct model inference
- Async background processing with live progress and logs
- Results dashboard:
  - timeline-like frame cards with timestamps
  - text, prices, CTA, intent, importance badge
  - audio transcript

## Run locally

1. Create venv and install dependencies:
```bash
cd /workspace/perptest
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2. Start server:
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Open:
- http://localhost:8000

## Notes
- Models are downloaded and cached under `models/<family>/<size>/` and `models/whisper/`.
- Uses only local inference (no external inference APIs).
- For very large models (`large`), ensure enough VRAM/RAM.
