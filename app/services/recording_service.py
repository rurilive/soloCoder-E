import os
import uuid
import aiofiles
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from app.config import settings
from app.database import SessionLocal
from app.models import Recording

logger = logging.getLogger(__name__)


class RecordingService:
    def __init__(self):
        self.recordings_dir = settings.RECORDINGS_DIR
        self.temp_dir = settings.TEMP_UPLOAD_DIR
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_recording(
        self,
        user_id: int,
        room_code: str,
        file: UploadFile,
        duration: int = 0,
    ) -> Optional[Recording]:
        try:
            file_ext = self._get_file_ext(file.content_type)
            filename = f"{room_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            file_path = self.recordings_dir / filename
            
            async with aiofiles.open(str(file_path), "wb") as f:
                while content := await file.read(1024 * 1024):
                    await f.write(content)
            
            file_size = file_path.stat().st_size
            
            db = SessionLocal()
            try:
                recording = Recording(
                    room_id=0,
                    user_id=user_id,
                    filename=filename,
                    file_path=str(file_path),
                    duration=duration,
                    size=file_size,
                    mime_type=file.content_type or "video/webm",
                )
                db.add(recording)
                db.commit()
                db.refresh(recording)
                return recording
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            return None
    
    def _get_file_ext(self, content_type: Optional[str]) -> str:
        if not content_type:
            return ".webm"
        
        ext_map = {
            "video/webm": ".webm",
            "video/mp4": ".mp4",
            "video/x-matroska": ".mkv",
            "audio/webm": ".webm",
            "audio/mp4": ".m4a",
        }
        return ext_map.get(content_type, ".webm")
    
    def get_user_recordings(self, user_id: int) -> list:
        db = SessionLocal()
        try:
            recordings = db.query(Recording).filter(
                Recording.user_id == user_id
            ).order_by(Recording.created_at.desc()).all()
            return [r.to_dict() for r in recordings]
        finally:
            db.close()
    
    def get_recording_path(self, recording_id: int, user_id: int) -> Optional[Path]:
        db = SessionLocal()
        try:
            recording = db.query(Recording).filter(
                Recording.id == recording_id,
                Recording.user_id == user_id
            ).first()
            if recording:
                return Path(recording.file_path)
            return None
        finally:
            db.close()
    
    def delete_recording(self, recording_id: int, user_id: int) -> bool:
        db = SessionLocal()
        try:
            recording = db.query(Recording).filter(
                Recording.id == recording_id,
                Recording.user_id == user_id
            ).first()
            if recording:
                file_path = Path(recording.file_path)
                if file_path.exists():
                    file_path.unlink()
                db.delete(recording)
                db.commit()
                return True
            return False
        finally:
            db.close()


recording_service = RecordingService()
