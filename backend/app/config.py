from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ad Image Analyzer"
    upload_dir: Path = Path("storage/uploads")
    result_dir: Path = Path("storage/results")
    model_dir: Path = Path("models")
    qwen_vl_model_name: str = "Qwen/Qwen2.5-VL-3B-Instruct"
    whisper_model_name: str = "small"
    max_workers: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_prefix="AD_ANALYZER_")


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.result_dir.mkdir(parents=True, exist_ok=True)
settings.model_dir.mkdir(parents=True, exist_ok=True)
