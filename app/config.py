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
    
    CUSTOM_GAMES_DIR: Path = BASE_DIR / "custom_games"
    TEMP_UPLOAD_DIR: Path = BASE_DIR / "temp_uploads"
    
    MAX_GAME_SIZE: int = 10 * 1024 * 1024
    MAX_ARCHIVE_SIZE: int = 15 * 1024 * 1024
    
    ALLOWED_GAME_EXTENSIONS: list = [".html", ".js", ".css", ".json", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".wav", ".mp3", ".ogg"]
    ALLOWED_ARCHIVE_EXTENSIONS: list = [".zip", ".rar"]
    
    MAX_FILES_PER_GAME: int = 100
    MAX_FILE_SIZE: int = 5 * 1024 * 1024
    
    class Config:
        env_file = ".env"


settings = Settings()
