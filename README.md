# Ad Image Analyzer (Qwen2.5-VL, Local Inference)

Production-ready local web app for analyzing advertisement creatives with **Qwen 2.5 VL**.

## Features

- Multi-file drag & drop upload (`jpg`, `png`, `webp`)
- Upload progress + background threaded processing
- Live processing logs and progress API
- Result cards per image with:
  - `visible_text`
  - `prices`
  - `marketing_intent` (`discount | urgency | branding | awareness`)
  - `importance_score` (1-5)
- Local inference only (no external APIs)

## Project Structure

```text
backend/
  app/
    api/
      routes.py
    services/
      analyzer.py
      job_manager.py
      model_loader.py
    static/
      index.html
      styles.css
      app.js
    uploads/
    models/
    config.py
    schemas.py
    main.py
  download_models.py
  requirements.txt
README.md
```

## Run Locally

1. Create environment and install dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Download Qwen2.5-VL into a dedicated folder (`backend/app/models`):

```bash
python download_models.py
```

3. Start server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open dashboard:

```text
http://localhost:8000
```

## API

- `POST /api/upload` - upload multiple image files and start async analysis job
- `GET /api/jobs/{job_id}` - polling endpoint for global + per-image progress, logs, and outputs

