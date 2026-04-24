import shutil
import uuid
import re
import tempfile
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
from app.utils.game_validator import game_validator, ValidationResult

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def sanitize_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    slug = slug.strip("-")
    return slug if slug else "game"


def is_archive_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in settings.ALLOWED_ARCHIVE_EXTENSIONS


def validate_individual_files(files: List[UploadFile]) -> ValidationResult:
    result = ValidationResult(valid=True)
    has_index_html = False
    total_size = 0
    file_count = 0
    
    for file in files:
        filename = file.filename or ""
        file_ext = Path(filename).suffix.lower()
        
        if filename == "index.html":
            has_index_html = True
        
        if file_ext not in settings.ALLOWED_GAME_EXTENSIONS and file_ext:
            result.add_warning(
                f"Uncommon file type: {filename} (may not work correctly)"
            )
        
        if file.size:
            total_size += file.size
            file_count += 1
    
    if total_size > settings.MAX_GAME_SIZE:
        result.add_error(
            f"Game files too large. Maximum size: {settings.MAX_GAME_SIZE / 1024 / 1024}MB, "
            f"Got: {total_size / 1024 / 1024:.2f}MB"
        )
    
    if not has_index_html:
        result.add_error("Game must contain an index.html file")
    
    if file_count > settings.MAX_FILES_PER_GAME:
        result.add_error(
            f"Too many files. Maximum: {settings.MAX_FILES_PER_GAME}, Got: {file_count}"
        )
    
    result.file_count = file_count
    result.total_size = total_size
    result.index_html_found = has_index_html
    
    return result


def extract_relative_path(filename: str, base_folder: str) -> str:
    if filename.startswith(base_folder + "/"):
        return filename[len(base_folder) + 1:]
    if filename.startswith(base_folder + "\\"):
        return filename[len(base_folder) + 1:]
    return filename


def format_validation_errors(result: ValidationResult) -> str:
    messages = []
    
    if result.errors:
        messages.append("Errors:")
        for error in result.errors:
            messages.append(f"  ❌ {error}")
    
    if result.warnings:
        messages.append("Warnings:")
        for warning in result.warnings:
            messages.append(f"  ⚠️ {warning}")
    
    if result.valid:
        messages.append(f"✓ Valid: {result.file_count} files, {result.total_size / 1024:.1f}KB")
    
    return "\n".join(messages)


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
        {"user": user, "error": None, "validation_result": None},
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload_game(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    instructions: str = Form(""),
    icon_emoji: str = Form("🎮"),
    version: str = Form("1.0.0"),
    archive: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
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
    
    if not archive and not files:
        return templates.TemplateResponse(
            request,
            "games/upload.html",
            {
                "user": user,
                "error": "Please upload either an archive file or individual game files.",
            },
        )
    
    temp_dir = None
    game_dir = None
    validation_result = None
    
    try:
        if archive and is_archive_file(archive.filename or ""):
            archive_ext = Path(archive.filename or "").suffix.lower()
            
            settings.TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            temp_dir = Path(tempfile.mkdtemp(dir=settings.TEMP_UPLOAD_DIR))
            archive_path = temp_dir / f"upload{archive_ext}"
            
            with open(archive_path, "wb") as f:
                shutil.copyfileobj(archive.file, f)
            
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            validation_result, game_root = game_validator.extract_and_validate(
                archive_path, extract_dir
            )
            
            if not validation_result.valid:
                error_msg = "Archive validation failed:\n" + format_validation_errors(validation_result)
                return templates.TemplateResponse(
                    request,
                    "games/upload.html",
                    {
                        "user": user,
                        "error": error_msg,
                        "validation_result": validation_result,
                    },
                )
            
            if not game_root:
                return templates.TemplateResponse(
                    request,
                    "games/upload.html",
                    {
                        "user": user,
                        "error": "Could not find index.html in the archive. "
                                 "Make sure your archive contains index.html at the root level.",
                        "validation_result": validation_result,
                    },
                )
            
            slug = sanitize_slug(name)
            existing_game = db.query(GameModel).filter(GameModel.slug == slug).first()
            if existing_game:
                slug = f"{slug}-{uuid.uuid4().hex[:8]}"
            
            game_path = f"{user['user_id']}_{slug}"
            game_dir = settings.CUSTOM_GAMES_DIR / game_path
            game_dir.mkdir(parents=True, exist_ok=True)
            
            for item in game_root.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(game_root)
                    dest_path = game_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
        
        elif files and len(files) > 0:
            validation_result = validate_individual_files(files)
            
            if not validation_result.valid:
                error_msg = "File validation failed:\n" + format_validation_errors(validation_result)
                return templates.TemplateResponse(
                    request,
                    "games/upload.html",
                    {
                        "user": user,
                        "error": error_msg,
                        "validation_result": validation_result,
                    },
                )
            
            slug = sanitize_slug(name)
            existing_game = db.query(GameModel).filter(GameModel.slug == slug).first()
            if existing_game:
                slug = f"{slug}-{uuid.uuid4().hex[:8]}"
            
            game_path = f"{user['user_id']}_{slug}"
            game_dir = settings.CUSTOM_GAMES_DIR / game_path
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
        
        else:
            return templates.TemplateResponse(
                request,
                "games/upload.html",
                {
                    "user": user,
                    "error": "Invalid upload. Please upload either a valid archive or game files.",
                },
            )
        
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
        if game_dir and game_dir.exists():
            shutil.rmtree(game_dir)
        return templates.TemplateResponse(
            request,
            "games/upload.html",
            {
                "user": user,
                "error": f"Failed to upload game: {str(e)}",
                "validation_result": None,
            },
        )
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/api/validate-archive", response_class=JSONResponse)
async def api_validate_archive(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    
    if not user or not user.get("is_developer"):
        return JSONResponse(
            content={
                "success": False,
                "error": "Not authorized. Please login as a developer.",
            },
            status_code=403,
        )
    
    temp_dir = None
    
    try:
        if not is_archive_file(file.filename or ""):
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Not a supported archive format. "
                             f"Supported: {settings.ALLOWED_ARCHIVE_EXTENSIONS}",
                    "is_archive": False,
                }
            )
        
        archive_ext = Path(file.filename or "").suffix.lower()
        settings.TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(dir=settings.TEMP_UPLOAD_DIR))
        archive_path = temp_dir / f"validate{archive_ext}"
        
        with open(archive_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        validation_result, game_root = game_validator.extract_and_validate(
            archive_path, extract_dir
        )
        
        return JSONResponse(
            content={
                "success": validation_result.valid,
                "valid": validation_result.valid,
                "is_archive": True,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "file_count": validation_result.file_count,
                "total_size": validation_result.total_size,
                "index_html_found": validation_result.index_html_found,
                "game_root_found": game_root is not None,
            }
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "is_archive": False,
            }
        )
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


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
