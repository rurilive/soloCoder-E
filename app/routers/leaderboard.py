from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.auth import get_current_user
from app.models import Score, User, Game as GameModel
from app.plugins.base import GameRegistry
from typing import List, Dict, Any

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_leaderboard(db: Session, game_slug: str = None) -> List[Dict[str, Any]]:
    query = db.query(
        Score,
        User.username,
        GameModel.name.label("game_name"),
        GameModel.slug.label("game_slug"),
    ).join(
        User, Score.user_id == User.id
    ).join(
        GameModel, Score.game_id == GameModel.id
    )
    
    if game_slug:
        query = query.filter(GameModel.slug == game_slug)
    
    scores = query.order_by(desc(Score.score)).all()
    
    leaderboard = []
    for score, username, game_name, game_slug in scores:
        leaderboard.append({
            "username": username,
            "score": score.score,
            "game_name": game_name,
            "game_slug": game_slug,
            "created_at": score.created_at,
        })
    
    return leaderboard


@router.get("/", response_class=HTMLResponse)
async def leaderboard_page(
    request: Request,
    game: str = None,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    games = GameRegistry.list_games()
    
    leaderboard_data = get_leaderboard(db, game)
    
    return templates.TemplateResponse(
        request,
        "leaderboard/index.html",
        {
            "user": user,
            "games": games,
            "selected_game": game,
            "leaderboard": leaderboard_data,
        },
    )
