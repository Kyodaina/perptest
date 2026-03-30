"""Pre-download Qwen2.5-VL assets into ./app/models."""

import os

from huggingface_hub import snapshot_download

MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"
CACHE_DIR = "app/models"


def main() -> None:
    os.environ["HF_HOME"] = CACHE_DIR
    snapshot_download(repo_id=MODEL_ID, local_dir=CACHE_DIR)
    print(f"Model downloaded to {CACHE_DIR}")


if __name__ == "__main__":
    main()
