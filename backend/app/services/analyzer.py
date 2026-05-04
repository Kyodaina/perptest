from __future__ import annotations

from pathlib import Path

import librosa
import noisereduce as nr
import numpy as np
import soundfile as sf

from app.config import SAMPLE_RATE, TEMP_DIR
from app.schemas import TranscriptResult, TranscriptSegment
from app.services.model_loader import get_model


def _format_ts(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def preprocess_audio(source: Path, target: Path) -> tuple[Path, float]:
    audio, sr = librosa.load(source, sr=SAMPLE_RATE, mono=True)
    denoised = nr.reduce_noise(y=audio, sr=sr, stationary=True)

    peak = np.max(np.abs(denoised))
    normalized = denoised / peak if peak > 0 else denoised
    compressed = np.tanh(normalized * 1.7)

    sf.write(target, compressed, SAMPLE_RATE)
    duration = len(compressed) / SAMPLE_RATE
    return target, duration


def transcribe_audio(
    source: Path,
    progress_cb: callable | None = None,
) -> TranscriptResult:
    model = get_model()
    cleaned_path = TEMP_DIR / f"{source.stem}_clean.wav"
    prepared_path, duration = preprocess_audio(source, cleaned_path)

    segments_iter, info = model.transcribe(
        str(prepared_path),
        language="hu",
        vad_filter=True,
        beam_size=5,
        best_of=5,
        word_timestamps=True,
        condition_on_previous_text=True,
    )

    segments: list[TranscriptSegment] = []
    lines: list[str] = []
    for idx, seg in enumerate(segments_iter, start=1):
        item = TranscriptSegment(start=seg.start, end=seg.end, text=seg.text.strip())
        segments.append(item)
        lines.append(f"[{_format_ts(item.start)}] {item.text}")

        if progress_cb:
            guessed_total = max(20, int(duration // 8) + 1)
            progress_cb(min(95, int((idx / guessed_total) * 100)))

    if progress_cb:
        progress_cb(100)

    return TranscriptResult(
        language=info.language,
        duration_seconds=duration,
        formatted_transcript="\n".join(lines),
        segments=segments,
    )
