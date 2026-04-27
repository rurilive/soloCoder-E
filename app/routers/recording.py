import logging
from pathlib import Path
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, get_current_user_or_401
from app.config import settings
from app.services.recording_service import recording_service

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
async def recording_list_page(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    if not user:
        return JSONResponse(
            content={"error": "Not authenticated"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    
    recordings = recording_service.get_user_recordings(user["user_id"])
    
    return templates.TemplateResponse(
        request,
        "recording/list.html",
        {
            "user": user,
            "recordings": recordings,
        },
    )


@router.get("/api/list")
async def list_recordings(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    recordings = recording_service.get_user_recordings(user["user_id"])
    return JSONResponse(content={"recordings": recordings})


@router.post("/api/upload")
async def upload_recording(
    request: Request,
    file: UploadFile = File(...),
    room_code: str = Form(...),
    duration: int = Form(0),
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_size = 0
    if hasattr(file.file, "__len__"):
        file_size = len(file.file.read())
        file.file.seek(0)
    
    if file_size > settings.MAX_RECORDING_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_RECORDING_SIZE / 1024 / 1024} MB",
        )
    
    recording = await recording_service.save_recording(
        user_id=user["user_id"],
        room_code=room_code,
        file=file,
        duration=duration,
    )
    
    if not recording:
        raise HTTPException(status_code=500, detail="Failed to save recording")
    
    return JSONResponse(content={
        "success": True,
        "recording": recording.to_dict(),
    })


@router.get("/api/download/{recording_id}")
async def download_recording(
    request: Request,
    recording_id: int,
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    file_path = recording_service.get_recording_path(recording_id, user["user_id"])
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return FileResponse(
        path=str(file_path),
        media_type="video/webm",
        filename=file_path.name,
    )


@router.delete("/api/{recording_id}")
async def delete_recording(
    request: Request,
    recording_id: int,
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    success = recording_service.delete_recording(recording_id, user["user_id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return JSONResponse(content={"success": True})
