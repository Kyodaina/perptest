"""Pre-download faster-whisper assets into ./app/models."""

from pathlib import Path

from faster_whisper import WhisperModel

MODEL_SIZE = "large-v3"
MODEL_DIR = Path("app/models")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    WhisperModel(
        MODEL_SIZE,
        device="cpu",
        compute_type="int8",
        download_root=str(MODEL_DIR),
    )
    print(f"Model '{MODEL_SIZE}' downloaded to {MODEL_DIR.resolve()}")


if __name__ == "__main__":
    main()
