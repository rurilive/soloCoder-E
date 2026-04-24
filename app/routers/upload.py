import shutil
import uuid
import re
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.auth import get_current_user, get_current_user_or_401
from app.models import Game as GameModel, User
from app.models.models import GameStatus
from app.plugins.base import GameRegistry
from app.plugins.custom_game import CustomGamePlugin
from app.config import settings

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def sanitize_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    slug = slug.strip("-")
    return slug if slug else "game"


def validate_game_files(files: List[UploadFile]) -> tuple[bool, str]:
    has_index_html = False
    total_size = 0
    
    for file in files:
        filename = file.filename or ""
        file_ext = Path(filename).suffix.lower()
        
        if filename == "index.html":
            has_index_html = True
        
        if file_ext not in settings.ALLOWED_GAME_EXTENSIONS:
            return False, f"File type '{file_ext}' is not allowed. Allowed types: {settings.ALLOWED_GAME_EXTENSIONS}"
        
        if file.size:
            total_size += file.size
    
    if total_size > settings.MAX_GAME_SIZE:
        return False, f"Game files too large. Maximum size: {settings.MAX_GAME_SIZE / 1024 / 1024}MB"
    
    if not has_index_html:
        return False, "Game must contain an index.html file"
    
    return True, "Valid"


def extract_relative_path(filename: str, base_folder: str) -> str:
    if filename.startswith(base_folder + "/"):
        return filename[len(base_folder) + 1:]
    if filename.startswith(base_folder + "\\"):
        return filename[len(base_folder) + 1:]
    return filename


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    user = await get_current_user(request)
    if not user or not user.get("is_developer"):
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "user": user,
                "error": "You need to be a developer to upload games. Please register as a developer.",
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return templates.TemplateResponse(
        request,
        "games/upload.html",
        {"user": user, "error": None},
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload_game(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    instructions: str = Form(""),
    icon_emoji: str = Form("🎮"),
    version: str = Form("1.0.0"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    if not user.get("is_developer"):
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "user": user,
                "error": "You need to be a developer to upload games.",
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    is_valid, message = validate_game_files(files)
    if not is_valid:
        return templates.TemplateResponse(
            request,
            "games/upload.html",
            {
                "user": user,
                "error": message,
            },
        )
    
    slug = sanitize_slug(name)
    
    existing_game = db.query(GameModel).filter(GameModel.slug == slug).first()
    if existing_game:
        slug = f"{slug}-{uuid.uuid4().hex[:8]}"
    
    game_path = f"{user['user_id']}_{slug}"
    game_dir = settings.CUSTOM_GAMES_DIR / game_path
    
    try:
        game_dir.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            filename = file.filename or ""
            relative_path = extract_relative_path(filename, "")
            
            if "/" in relative_path or "\\" in relative_path:
                subdir = game_dir / Path(relative_path).parent
                subdir.mkdir(parents=True, exist_ok=True)
            
            file_path = game_dir / relative_path
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        
        db_user = db.query(User).filter(User.id == user["user_id"]).first()
        
        new_game = GameModel(
            name=name,
            slug=slug,
            description=description,
            developer=user["username"],
            developer_id=user["user_id"],
            is_custom=True,
            status=GameStatus.PUBLISHED,
            game_path=game_path,
            icon_emoji=icon_emoji,
            version=version,
            instructions=instructions,
        )
        db.add(new_game)
        db.commit()
        db.refresh(new_game)
        
        custom_plugin = CustomGamePlugin(
            name=name,
            slug=slug,
            description=description,
            game_path=game_path,
            developer=user["username"],
            icon_emoji=icon_emoji,
            instructions=instructions,
        )
        GameRegistry.register_custom(custom_plugin)
        
        return RedirectResponse(url=f"/games/{slug}", status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        if game_dir.exists():
            shutil.rmtree(game_dir)
        return templates.TemplateResponse(
            request,
            "games/upload.html",
            {
                "user": user,
                "error": f"Failed to upload game: {str(e)}",
            },
        )


@router.get("/my-games", response_class=HTMLResponse)
async def my_games(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    
    games = db.query(GameModel).filter(
        GameModel.developer_id == user["user_id"]
    ).all()
    
    return templates.TemplateResponse(
        request,
        "games/my_games.html",
        {
            "user": user,
            "games": games,
        },
    )


@router.get("/api/my-games", response_class=JSONResponse)
async def api_my_games(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    
    if not user:
        return JSONResponse(
            content={"success": False, "error": "Not logged in"},
            status_code=401,
        )
    
    games = db.query(GameModel).filter(
        GameModel.developer_id == user["user_id"]
    ).all()
    
    return JSONResponse(
        content={
            "success": True,
            "games": [
                {
                    "id": g.id,
                    "name": g.name,
                    "slug": g.slug,
                    "description": g.description,
                    "status": g.status,
                    "version": g.version,
                    "created_at": g.created_at.isoformat() if g.created_at else None,
                }
                for g in games
            ],
        }
    )


def load_custom_games_from_db(db: Session):
    custom_games = db.query(GameModel).filter(
        GameModel.is_custom == True,
        GameModel.status == GameStatus.PUBLISHED,
    ).all()
    
    GameRegistry.clear_custom_games()
    
    for game in custom_games:
        if game.game_path:
            custom_plugin = CustomGamePlugin(
                name=game.name,
                slug=game.slug,
                description=game.description or "",
                game_path=game.game_path,
                developer=game.developer or "User",
                icon_emoji=game.icon_emoji or "🎮",
                instructions=game.instructions,
            )
            GameRegistry.register_custom(custom_plugin)
