from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "密码本管理器"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    
    ENCRYPTION_KEY_FILE: Path = DATA_DIR / ".encryption_key"
    PASSWORD_STORAGE_FILE: Path = DATA_DIR / "passwords.enc"
    MASTER_PASSWORD_HASH: Optional[str] = None
    
    SESSION_SECRET_KEY: str = "your-super-secret-session-key-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
