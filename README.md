# Ad Intelligence Analyzer (Local AI)

Production-ready local web application for advertisement image analysis powered by:
- **Qwen 2.5 VL** for vision-language extraction
- **Whisper** for audio transcription support
- **FastAPI** backend with async-compatible threaded jobs and progress tracking
- **Modern dashboard UI** served by the backend

## Project structure

```text
.
├── app/
│   ├── config.py                  # Paths, model IDs, feature flags
│   ├── main.py                    # FastAPI app + API routes + static hosting
│   ├── schemas.py                 # Pydantic schemas for API contracts
│   ├── models/
│   │   ├── qwen_loader.py         # Qwen 2.5 VL model loading + image analysis
│   │   └── whisper_loader.py      # Whisper model loading + transcription
│   └── services/
│       ├── job_manager.py         # Threaded jobs, progress, logs, result persistence
│       └── pipeline.py            # Per-file processing orchestration
├── static/
│   ├── index.html                 # Dashboard views (upload, processing, results)
│   ├── app.js                     # Drag & drop upload, progress polling, result rendering
│   └── styles.css                 # Modern card-based UI styles
├── models/                        # Local model cache/download target
├── storage/
│   ├── uploads/                   # Uploaded files
│   └── results/                   # Saved structured output JSON files
└── requirements.txt
```

## Run locally

1. Create and activate virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open UI:

```text
http://localhost:8000
```

## Notes

- First run downloads Qwen and Whisper models into `./models/`.
- All inference is local (no external inference APIs).
- Image output follows strict JSON fields:
  - `visible_text`
  - `prices`
  - `key_messages`
  - `cta`
  - `marketing_intent` (`discount | urgency | branding | awareness`)
  - `importance_score` (`1-5`)

- Transformers is pinned to a Qwen2.5-VL-compatible version (`4.57.0`) to avoid image processor mismatches.
