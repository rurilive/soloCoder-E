from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, get_current_user_or_401
from app.plugins.base import GameRegistry
from app.models import Game as GameModel, Score, User
from app.config import settings
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


def _inject_game_context(html_content: str, game_slug: str, game_path: str) -> str:
    base_url = f"/custom-games/{game_path}/"
    base_tag = f'<base href="{base_url}">'
    
    inject_script = f"""
<script>
window.GAME_SLUG = "{game_slug}";
window.SUBMIT_SCORE_URL = "/games/submit-score";

window.submitGameScore = async function(score) {{
    try {{
        const response = await fetch(window.SUBMIT_SCORE_URL, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
                game_slug: window.GAME_SLUG,
                score: score
            }})
        }});
        return await response.json();
    }} catch (error) {{
        console.error('Error submitting score:', error);
        return {{ success: false, error: error.message }};
    }}
}};
</script>
"""
    if "</head>" in html_content:
        if "<base" not in html_content:
            html_content = html_content.replace("</head>", base_tag + inject_script + "</head>")
        else:
            html_content = html_content.replace("</head>", inject_script + "</head>")
    elif "</body>" in html_content:
        if "<base" not in html_content:
            html_content = base_tag + html_content.replace("</body>", inject_script + "</body>")
        else:
            html_content = html_content.replace("</body>", inject_script + "</body>")
    else:
        if "<base" not in html_content:
            html_content = base_tag + inject_script + html_content
        else:
            html_content = inject_script + html_content
    
    return html_content


@router.get("/iframe/{game_slug}", response_class=HTMLResponse)
async def game_iframe(
    game_slug: str,
    request: Request,
    db: Session = Depends(get_db),
):
    game_plugin = GameRegistry.get(game_slug)
    if not game_plugin:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not hasattr(game_plugin, 'game_path') or not game_plugin.game_path:
        raise HTTPException(status_code=400, detail="This game does not support iframe loading")
    
    game_full_path = settings.CUSTOM_GAMES_DIR / game_plugin.game_path
    index_html = game_full_path / "index.html"
    
    if not index_html.exists():
        raise HTTPException(status_code=404, detail="Game index.html not found")
    
    with open(index_html, "r", encoding="utf-8") as f:
        game_content = f.read()
    
    game_content = _inject_game_context(game_content, game_slug, game_plugin.game_path)
    
    return HTMLResponse(content=game_content)


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
