from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, get_current_user_or_401
from app.plugins.base import GameRegistry
from app.models import Game as GameModel, Score, User
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class ScoreSubmit(BaseModel):
    game_slug: str
    score: int


@router.get("/", response_class=HTMLResponse)
async def game_list(request: Request):
    user = await get_current_user(request)
    games = GameRegistry.list_games()
    return templates.TemplateResponse(
        request,
        "games/list.html",
        {
            "user": user,
            "games": games,
        },
    )


@router.get("/{game_slug}", response_class=HTMLResponse)
async def game_play(
    request: Request,
    game_slug: str,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    
    if not user:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "user": None,
                "error": "Please login to play games",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    
    game_plugin = GameRegistry.get(game_slug)
    if not game_plugin:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = db.query(GameModel).filter(GameModel.slug == game_slug).first()
    if not game:
        game = GameModel(
            name=game_plugin.name,
            slug=game_plugin.slug,
            description=game_plugin.description,
        )
        db.add(game)
        db.commit()
        db.refresh(game)
    
    return await game_plugin.play(request, templates)


@router.post("/submit-score")
async def submit_score(
    request: Request,
    score_data: ScoreSubmit,
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    game_plugin = GameRegistry.get(score_data.game_slug)
    if not game_plugin:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = db.query(GameModel).filter(GameModel.slug == score_data.game_slug).first()
    if not game:
        game = GameModel(
            name=game_plugin.name,
            slug=game_plugin.slug,
            description=game_plugin.description,
        )
        db.add(game)
        db.commit()
        db.refresh(game)
    
    new_score = Score(
        game_id=game.id,
        user_id=user["user_id"],
        score=score_data.score,
    )
    db.add(new_score)
    db.commit()
    
    return JSONResponse(
        content={
            "success": True,
            "message": "Score submitted successfully",
            "score": score_data.score,
        }
    )
