from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.config import settings
from app.database import init_db, SessionLocal, get_db
from app.auth import get_current_user
from app.plugins.base import GameRegistry
from app.models import Game as GameModel, Review
from app.routers.upload import load_custom_games_from_db
from app import routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    init_db()
    
    settings.CUSTOM_GAMES_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    from app.plugins.whack_a_mole import WhackAMolePlugin
    GameRegistry.register(WhackAMolePlugin())
    
    db = SessionLocal()
    try:
        load_custom_games_from_db(db)
    finally:
        db.close()
    
    from app.routers.battle import manager
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
app.mount("/custom-games", StaticFiles(directory=str(settings.CUSTOM_GAMES_DIR)), name="custom_games")

app.include_router(routers.auth.router, prefix="/auth", tags=["auth"])
app.include_router(routers.upload.router, prefix="/games", tags=["games"])
app.include_router(routers.game.router, prefix="/games", tags=["games"])
app.include_router(routers.leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(routers.review.router, prefix="/reviews", tags=["reviews"])
app.include_router(routers.battle.router, prefix="/battle", tags=["battle"])


def get_game_ratings(db: Session) -> dict:
    ratings = db.query(
        Review.game_id,
        func.avg(Review.rating).label("average_rating"),
        func.count(Review.id).label("review_count"),
        func.max(Review.created_at).label("latest_review_at"),
    ).group_by(Review.game_id).all()
    
    rating_dict = {}
    for game_id, avg_rating, review_count, latest_at in ratings:
        rating_dict[game_id] = {
            "average_rating": round(float(avg_rating), 1) if avg_rating else 0,
            "review_count": review_count,
            "latest_review_at": latest_at,
        }
    
    return rating_dict


def get_games_with_ratings(db: Session, limit: int = None) -> list:
    games = GameRegistry.list_games()
    ratings = get_game_ratings(db)
    
    games_with_ratings = []
    for game in games:
        db_game = db.query(GameModel).filter(GameModel.slug == game["slug"]).first()
        
        game_rating = {
            **game,
            "average_rating": 0,
            "review_count": 0,
            "latest_review_at": None,
        }
        
        if db_game and db_game.id in ratings:
            game_rating["average_rating"] = ratings[db_game.id]["average_rating"]
            game_rating["review_count"] = ratings[db_game.id]["review_count"]
            game_rating["latest_review_at"] = ratings[db_game.id]["latest_review_at"]
        
        games_with_ratings.append(game_rating)
    
    games_with_ratings.sort(
        key=lambda x: (
            -x["average_rating"],
            -(x["latest_review_at"].timestamp() if x["latest_review_at"] else 0)
        )
    )
    
    if limit:
        return games_with_ratings[:limit]
    
    return games_with_ratings


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    games = get_games_with_ratings(db, limit=5)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "games": games,
        },
    )
