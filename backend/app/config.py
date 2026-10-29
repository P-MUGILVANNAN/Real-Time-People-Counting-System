import os
import json
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "Real-Time People Counting and Crowd Density Estimation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Compute Device
    DEVICE: str = "cpu"  # "cpu" or "cuda"

    # Paths
    BASE_DIR: Path = ROOT_DIR
    MODELS_DIR: Path = ROOT_DIR / "models"
    OUTPUTS_DIR: Path = ROOT_DIR / "outputs"
    DATASETS_DIR: Path = ROOT_DIR / "datasets"

    DETECTION_MODEL_PATH: str = str(ROOT_DIR / "models" / "detection" / "yolov8n.pt")
    DENSITY_MODEL_PATH: str = str(ROOT_DIR / "models" / "density" / "mcnn_shanghaitech.pth")
    TRACKER_TYPE: str = "bytetrack"  # "bytetrack" or "botsort"

    # Detection Parameters
    CONFIDENCE_THRESHOLD: float = 0.35
    IOU_THRESHOLD: float = 0.45
    INPUT_IMAGE_SIZE: int = 640
    MAX_DETECTIONS: int = 300
    TRACK_BUFFER_FRAMES: int = 30

    # Video Settings
    WEBCAM_INDEX: int = 0
    FRAME_SKIP: int = 0
    VIDEO_QUEUE_SIZE: int = 30
    SAVE_ANNOTATED_VIDEO: bool = False

    # Alert Thresholds
    MODERATE_CROWD_THRESHOLD: int = 10
    HIGH_CROWD_THRESHOLD: int = 25
    CRITICAL_CROWD_THRESHOLD: int = 50
    ALERT_COOLDOWN_SECONDS: float = 15.0
    ANALYTICS_SNAPSHOT_INTERVAL_SEC: float = 2.0

    # Storage & Database
    DATABASE_URL: str = f"sqlite:///{ROOT_DIR / 'outputs' / 'crowd_system.db'}"
    DATA_RETENTION_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
