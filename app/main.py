from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from pathlib import Path
from app.config import settings
from app.database import init_db
from app.auth import get_current_user
from app import routers
from app.services.conference_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    init_db()
    
    settings.RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    cleanup_task = asyncio.create_task(manager.start_cleanup_task())
    
    yield
    
    manager.stop_cleanup_task()
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(routers.auth.router, prefix="/auth", tags=["auth"])
app.include_router(routers.conference.router, prefix="/conference", tags=["conference"])
app.include_router(routers.recording.router, prefix="/recording", tags=["recording"])


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
):
    user = await get_current_user(request)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
        },
    )
