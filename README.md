# Ad Image Analyzer (Local AI)

Production-ready local web app for advertisement image analysis using:
- **Qwen-VL** for visual + text marketing interpretation
- **Whisper** for local audio transcription
- **FastAPI** backend with threaded async job handling and progress APIs
- **Modern dashboard UI** with drag/drop upload, progress tracking, logs, and result cards

## Project Structure

```text
backend/
  app/
    main.py                  # FastAPI app + routes
    config.py                # Runtime settings
    schemas.py               # Pydantic request/response models
    services/
      model_manager.py       # Qwen-VL/Whisper loading + precision configs
      pipeline.py            # Image/audio processing logic
      job_manager.py         # Threaded job queue, progress, logs, persistence
    utils/
      json_parser.py         # Strict JSON extraction/validation
frontend/
  index.html                 # Dashboard UI
  styles.css                 # Modern card-based theme
  app.js                     # Upload flow, polling, rendering
storage/
  uploads/                   # Uploaded media files
  results/                   # Job output JSON files
models/                      # Downloaded local model weights/cache
requirements.txt
```

## Local Run

1. **Create venv and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run API server**
   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Open dashboard**
   - http://localhost:8000

## Notes

- Models are downloaded automatically into `models/qwen_vl` and `models/whisper` on first use.
- Default vision model is `Qwen/Qwen2-VL-2B-Instruct` for `transformers` compatibility.
- Processing modes:
  - `fast`: shorter generation, low latency
  - `balanced`: default middle ground
  - `precise`: longer generation for richer extraction
- Strict image JSON schema is validated server-side before returning/storing.
- `visible_text` is configured to return all readable text from the image without interpretation/filtering.
