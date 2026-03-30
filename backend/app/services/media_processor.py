from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np
import whisper
from skimage.metrics import structural_similarity as ssim

from .model_loader import VisionLanguageService
from .schemas import AudioSegment, FileResult, FrameResult, PrecisionMode

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi"}


class MediaProcessor:
    def __init__(self, upload_dir: Path, output_dir: Path, model_root: Path) -> None:
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self.data_root = upload_dir.parent
        self.model_root = model_root
        self.vl_service = VisionLanguageService(model_root)
        self.whisper_model = whisper.load_model("base", download_root=str(model_root / "whisper"))

    def _to_web_path(self, path: Path) -> str:
        return f"/data/{path.relative_to(self.data_root).as_posix()}"

    @staticmethod
    def _frame_hash(frame: np.ndarray) -> str:
        small = cv2.resize(frame, (64, 64))
        return hashlib.md5(small.tobytes()).hexdigest()

    @staticmethod
    def _is_duplicate(frame_a: np.ndarray, frame_b: np.ndarray, threshold: float = 0.96) -> bool:
        gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)
        score, _ = ssim(gray_a, gray_b, full=True)
        return score >= threshold

    def _extract_frames(self, video_path: Path, frame_interval_seconds: float, target_dir: Path):
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        stride = max(1, int(fps * frame_interval_seconds))

        idx = 0
        saved: list[tuple[Path, float]] = []
        last_frame = None
        seen_hashes = set()

        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            if idx % stride != 0:
                idx += 1
                continue

            frame_hash = self._frame_hash(frame)
            if frame_hash in seen_hashes:
                idx += 1
                continue
            if last_frame is not None and self._is_duplicate(last_frame, frame):
                idx += 1
                continue

            ts = idx / fps
            out_path = target_dir / f"frame_{idx:06d}.jpg"
            cv2.imwrite(str(out_path), frame)
            saved.append((out_path, ts))
            seen_hashes.add(frame_hash)
            last_frame = frame
            idx += 1

        cap.release()
        return saved

    def _transcribe(self, video_path: Path) -> list[AudioSegment]:
        transcript = self.whisper_model.transcribe(str(video_path), verbose=False)
        segments = transcript.get("segments", [])
        return [
            AudioSegment(start=float(seg["start"]), end=float(seg["end"]), text=seg["text"].strip())
            for seg in segments
        ]

    def process_image(self, file_path: Path, family: str, size: str, precision: PrecisionMode) -> FileResult:
        try:
            analyzed = self.vl_service.analyze_image(file_path, family, size, precision)
        except Exception as exc:
            analyzed = {
                "visible_text": "",
                "prices": [],
                "key_messages": [f"analysis_error: {exc}"],
                "cta": "",
                "marketing_intent": "awareness",
                "importance_score": 1,
            }
        return FileResult(
            filename=file_path.name,
            file_type="image",
            frames=[
                FrameResult(
                    frame_path=self._to_web_path(file_path),
                    timestamp_seconds=0,
                    **analyzed,
                )
            ],
            audio_transcript=[],
        )

    def process_video(self, file_path: Path, family: str, size: str, precision: PrecisionMode, frame_interval_seconds: float) -> FileResult:
        frame_dir = self.output_dir / file_path.stem
        frame_dir.mkdir(parents=True, exist_ok=True)

        extracted = self._extract_frames(file_path, frame_interval_seconds, frame_dir)
        frame_results: list[FrameResult] = []
        for frame_path, ts in extracted:
            try:
                analyzed = self.vl_service.analyze_image(frame_path, family, size, precision)
            except Exception as exc:
                analyzed = {
                    "visible_text": "",
                    "prices": [],
                    "key_messages": [f"analysis_error: {exc}"],
                    "cta": "",
                    "marketing_intent": "awareness",
                    "importance_score": 1,
                }
            frame_results.append(
                FrameResult(
                    frame_path=self._to_web_path(frame_path),
                    timestamp_seconds=ts,
                    **analyzed,
                )
            )

        return FileResult(
            filename=file_path.name,
            file_type="video",
            frames=frame_results,
            audio_transcript=self._transcribe(file_path),
        )
