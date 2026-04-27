import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, get_current_user_or_401, decode_access_token
from app.config import settings
from app.services.conference_manager import manager
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
async def conference_lobby(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    public_rooms = manager.get_public_rooms()
    
    return templates.TemplateResponse(
        request,
        "conference/lobby.html",
        {
            "user": user,
            "rooms": public_rooms,
        },
    )


@router.post("/create")
async def create_room(
    request: Request,
    name: str = Form("会议"),
    is_public: bool = Form(True),
    max_participants: int = Form(10),
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    if max_participants < 2 or max_participants > 50:
        max_participants = 10
    
    room_code = manager.create_room(
        host_id=user["user_id"],
        name=name,
        is_public=is_public,
        max_participants=max_participants,
    )
    
    return RedirectResponse(
        url=f"/conference/room/{room_code}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/join")
async def join_room(
    request: Request,
    room_code: str = Form(...),
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    room_code = room_code.strip().upper()
    
    room = manager.get_room(room_code)
    if not room:
        return templates.TemplateResponse(
            request,
            "conference/lobby.html",
            {
                "user": user,
                "rooms": manager.get_public_rooms(),
                "error": f"房间 {room_code} 不存在",
            },
        )
    
    return RedirectResponse(
        url=f"/conference/room/{room_code}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/room/{room_code}", response_class=HTMLResponse)
async def room_page(
    request: Request,
    room_code: str,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    
    if not user:
        return RedirectResponse(
            url=f"/auth/login?next=/conference/room/{room_code}",
            status_code=status.HTTP_302_FOUND,
        )
    
    room = manager.get_room(room_code)
    if not room:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "user": user,
                "error": f"房间 {room_code} 不存在或已过期",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    participant_count = len(room.participants)
    if participant_count >= room.max_participants and user["user_id"] not in room.get_participant_ids():
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "user": user,
                "error": f"房间已满 (最多 {room.max_participants} 人)",
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    return templates.TemplateResponse(
        request,
        "conference/room.html",
        {
            "user": user,
            "room": {
                "room_code": room.room_code,
                "name": room.name,
                "host_id": room.host_id,
                "is_public": room.is_public,
                "max_participants": room.max_participants,
                "status": room.status,
                "participants": room.get_participants_info(),
                "chat_history": room.chat_history,
            },
        },
    )


@router.get("/api/room/{room_code}/info")
async def get_room_info(
    request: Request,
    room_code: str,
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
    room = manager.get_room(room_code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return JSONResponse(content={
        "room_code": room.room_code,
        "name": room.name,
        "host_id": room.host_id,
        "participants": room.get_participants_info(),
        "status": room.status,
    })


@router.websocket("/ws/{room_code}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_code: str,
    db: Session = Depends(get_db),
):
    token = websocket.cookies.get(settings.COOKIE_NAME)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    user_id = payload.get("user_id")
    username = payload.get("username")
    if user_id is None or username is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    room = manager.get_room(room_code)
    if not room:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    success = await manager.connect(websocket, room_code, user_id, username)
    if not success:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        await manager.broadcast_to_room(
            room_code,
            {
                "type": "participant_joined",
                "user_id": user_id,
                "username": username,
                "participants": room.get_participants_info(),
            },
            exclude_user_id=user_id,
        )
        
        await manager.send_to_user(
            room_code,
            user_id,
            {
                "type": "room_joined",
                "room_code": room_code,
                "participants": room.get_participants_info(),
                "chat_history": room.chat_history,
                "is_host": user_id == room.host_id,
            },
        )
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            room = manager.get_room(room_code)
            if not room:
                break
            
            if message_type == "offer":
                target_user_id = data.get("target_user_id")
                offer = data.get("offer")
                if target_user_id and offer:
                    await manager.send_to_user(
                        room_code,
                        target_user_id,
                        {
                            "type": "offer",
                            "from_user_id": user_id,
                            "from_username": username,
                            "offer": offer,
                        },
                    )
            
            elif message_type == "answer":
                target_user_id = data.get("target_user_id")
                answer = data.get("answer")
                if target_user_id and answer:
                    await manager.send_to_user(
                        room_code,
                        target_user_id,
                        {
                            "type": "answer",
                            "from_user_id": user_id,
                            "from_username": username,
                            "answer": answer,
                        },
                    )
            
            elif message_type == "ice_candidate":
                target_user_id = data.get("target_user_id")
                candidate = data.get("candidate")
                if target_user_id and candidate:
                    await manager.send_to_user(
                        room_code,
                        target_user_id,
                        {
                            "type": "ice_candidate",
                            "from_user_id": user_id,
                            "from_username": username,
                            "candidate": candidate,
                        },
                    )
            
            elif message_type == "chat_message":
                message = data.get("message", "").strip()
                if message:
                    manager.add_chat_message(room_code, user_id, username, message)
                    await manager.broadcast_to_room(
                        room_code,
                        {
                            "type": "chat_message",
                            "user_id": user_id,
                            "username": username,
                            "message": message,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
            
            elif message_type == "mute_audio":
                muted = data.get("muted", True)
                manager.update_participant_status(room_code, user_id, audio_muted=muted)
                await manager.broadcast_to_room(
                    room_code,
                    {
                        "type": "audio_muted",
                        "user_id": user_id,
                        "username": username,
                        "muted": muted,
                    },
                )
            
            elif message_type == "mute_video":
                muted = data.get("muted", True)
                manager.update_participant_status(room_code, user_id, video_muted=muted)
                await manager.broadcast_to_room(
                    room_code,
                    {
                        "type": "video_muted",
                        "user_id": user_id,
                        "username": username,
                        "muted": muted,
                    },
                )
            
            elif message_type == "screen_share_start":
                manager.update_participant_status(room_code, user_id, screen_sharing=True)
                await manager.broadcast_to_room(
                    room_code,
                    {
                        "type": "screen_share_start",
                        "user_id": user_id,
                        "username": username,
                    },
                )
            
            elif message_type == "screen_share_stop":
                manager.update_participant_status(room_code, user_id, screen_sharing=False)
                await manager.broadcast_to_room(
                    room_code,
                    {
                        "type": "screen_share_stop",
                        "user_id": user_id,
                        "username": username,
                    },
                )
            
            elif message_type == "start_recording":
                if user_id == room.host_id:
                    room.recording_enabled = True
                    await manager.broadcast_to_room(
                        room_code,
                        {
                            "type": "recording_started",
                            "started_by": username,
                        },
                    )
            
            elif message_type == "stop_recording":
                if user_id == room.host_id:
                    room.recording_enabled = False
                    await manager.broadcast_to_room(
                        room_code,
                        {
                            "type": "recording_stopped",
                            "stopped_by": username,
                        },
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(room_code, user_id)
        room = manager.get_room(room_code)
        if room:
            await manager.broadcast_to_room(
                room_code,
                {
                    "type": "participant_left",
                    "user_id": user_id,
                    "username": username,
                    "participants": room.get_participants_info(),
                },
            )
