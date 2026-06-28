"""Application settings, loaded from the repo-root .env.

Also puts the repo root on sys.path so the backend can `import ml...` (the shared CV pipeline).
"""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# repo root = .../VisionGuard  (config.py -> core -> app -> backend -> VisionGuard)
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database / queue
    DATABASE_URL: str = "sqlite:///./visionguard.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    PROCESS_MODE: str = "inline"  # inline (BackgroundTasks) | celery

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_DIR: str = str(REPO_ROOT / "data" / "evidence")

    # Mappls
    MAPPLS_REST_KEY: str = ""
    MAPPLS_MAP_SDK_KEY: str = ""

    # Hugging Face
    HUGGINGFACE_TOKEN: str = ""

    # Roboflow
    ROBOFLOW_WORKSPACE: str = ""
    ROBOFLOW_API_KEY: str = ""

    # Auth
    JWT_SECRET: str = "dev_secret_change_me"
    JWT_EXPIRE_MINUTES: int = 720
    JWT_ALGORITHM: str = "HS256"

    # Models
    MODEL_DETECTOR: str = "ml/weights/uvh26/yolo11s.pt"
    MODEL_HELMET: str = "ml/weights/Helmet.pt"
    MODEL_PLATE: str = "ml/weights/plate/best.pt"
    OCR_ENGINE: str = "easyocr"

    # Thresholds
    CONF_FLOOR: float = 0.25
    QUALITY_FLOOR: float = 0.30

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    @property
    def repo_root(self) -> Path:
        return REPO_ROOT

    def model_post_init(self, __context) -> None:
        # anchor a relative sqlite path to the repo root so the DB location is the same
        # regardless of the current working directory (uvicorn runs with --app-dir backend)
        pfx = "sqlite:///"
        if self.DATABASE_URL.startswith(pfx):
            raw = self.DATABASE_URL[len(pfx):]
            if not raw.startswith("/"):
                raw = raw[2:] if raw.startswith("./") else raw
                self.DATABASE_URL = f"{pfx}{(REPO_ROOT / raw).resolve()}"


settings = Settings()
