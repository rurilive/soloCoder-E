from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.routes.web import router as web_router
from app.models.database import init_db


_db_engine = None
_db_session_local = None


def get_db_engine():
    return _db_engine


def get_db_session_local():
    return _db_session_local


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _db_engine, _db_session_local
    
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
    
    _db_engine, _db_session_local = init_db(settings.DATABASE_URL)
    
    yield
    
    if _db_engine:
        _db_engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

app.include_router(web_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5555,
        reload=True
    )
