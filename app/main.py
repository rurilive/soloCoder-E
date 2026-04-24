from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from pathlib import Path
from app.config import settings
from app.database import init_db, SessionLocal
from app.auth import get_current_user
from app.plugins.base import GameRegistry
from app.routers.upload import load_custom_games_from_db
from app import routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    
    settings.CUSTOM_GAMES_DIR.mkdir(parents=True, exist_ok=True)
    
    from app.plugins.whack_a_mole import WhackAMolePlugin
    GameRegistry.register(WhackAMolePlugin())
    
    db = SessionLocal()
    try:
        load_custom_games_from_db(db)
    finally:
        db.close()
    
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/custom-games", StaticFiles(directory=str(settings.CUSTOM_GAMES_DIR)), name="custom_games")

app.include_router(routers.auth.router, prefix="/auth", tags=["auth"])
app.include_router(routers.game.router, prefix="/games", tags=["games"])
app.include_router(routers.upload.router, prefix="/games", tags=["games"])
app.include_router(routers.leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(routers.review.router, prefix="/reviews", tags=["reviews"])
app.include_router(routers.battle.router, prefix="/battle", tags=["battle"])


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = await get_current_user(request)
    games = GameRegistry.list_games()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "games": games,
        },
    )
