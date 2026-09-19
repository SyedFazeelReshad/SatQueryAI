from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",)
    )

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    secret_key: str = "dev-secret"
    upload_dir: Path = Path("./uploads")
    output_dir: Path = Path("./outputs")
    max_upload_size_mb: int = 500
    vlm_adapter_path: str = ""
    grounding_dino_path: str = "models/grounding/"
    sam2_checkpoint_path: str = "models/segmentation/"
    model_device: str = "cpu"
    model_quantization: str = "none"
    ndvi_vegetation_threshold: float = 0.3
    ndwi_water_threshold: float = 0.0
    change_threshold_percentile: float = 95.0
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
