import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Game Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'game_platform.db'}"
    )
    
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "your-secret-key-change-in-production-please"
    )
    
    COOKIE_NAME: str = "game_platform_session"
    
    class Config:
        env_file = ".env"


settings = Settings()
