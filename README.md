# Magyar Audio Transcriber (CPU-only)

Teljes, lokálisan futtatható webalkalmazás magyar nyelvű hangfájlok leiratozására.
A rendszer kizárólag CPU-t használ, a beszédfelismerést `faster-whisper` végzi.

## Projekt struktúra

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
    temp/
    exports/
    models/
    config.py
    schemas.py
    main.py
  download_models.py
  requirements.txt
README.md
```

## Funkciók

- Feltöltés: `.wav`, `.mp3`, `.m4a`
- CPU-only ASR: `faster-whisper` (`large-v3`, `int8`)
- Automatikus modell letöltés első futtatáskor
- Előfeldolgozás:
  - zajcsökkentés (`noisereduce`)
  - normalizálás
  - enyhe dinamika-kompresszió (hangerő kiegyenlítés)
- Időbélyeges, jól olvasható leirat
- Progress polling API
- Export: `.txt` és formázott `.pdf`
- Hibakezelés nem támogatott fájlokra és feldolgozási hibákra

## Telepítés és futtatás

### 1) Előfeltételek

- Python 3.10+
- FFmpeg (különösen mp3/m4a támogatáshoz)

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### 2) Virtuális környezet + függőségek

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Modell előtöltés (opcionális, de ajánlott)

```bash
python download_models.py
```

Ha ezt kihagyod, az app az első transzkripciónál automatikusan letölti a modellt.

### 4) Szerver indítás

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5) UI megnyitása

Böngészőben:

```text
http://localhost:8000
```

## Használat

1. Válassz ki egy támogatott hangfájlt.
2. Kattints a **Feldolgozás** gombra.
3. Kövesd a státuszt és progress bart.
4. A kész leirat megjelenik időbélyegekkel.
5. Exportáld TXT vagy PDF formátumba.

