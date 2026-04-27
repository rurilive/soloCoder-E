import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Conference System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'conference.db'}"
    )
    
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "conference-secret-key-change-in-production-please"
    )
    
    COOKIE_NAME: str = "conference_session"
    
    RECORDINGS_DIR: Path = BASE_DIR / "recordings"
    TEMP_UPLOAD_DIR: Path = BASE_DIR / "temp_uploads"
    
    MAX_RECORDING_SIZE: int = 500 * 1024 * 1024
    
    class Config:
        env_file = ".env"


settings = Settings()
