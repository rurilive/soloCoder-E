from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.routes.web import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
    
    yield


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
