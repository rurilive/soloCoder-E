import uuid
import random
import string
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, get_current_user_or_401
from app.models import GameRoom, Game as GameModel, User
from app.plugins.base import GameRegistry

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}
        self.room_states: Dict[str, Dict[str, Any]] = {}
        self.room_hosts: Dict[str, int] = {}

    async def connect(self, websocket: WebSocket, room_code: str, user_id: int):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = {}
        self.active_connections[room_code][user_id] = websocket

    def disconnect(self, room_code: str, user_id: int):
        if room_code in self.active_connections:
            if user_id in self.active_connections[room_code]:
                del self.active_connections[room_code][user_id]
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]
                if room_code in self.room_states:
                    del self.room_states[room_code]
                if room_code in self.room_hosts:
                    del self.room_hosts[room_code]

    async def broadcast_to_room(self, room_code: str, message: Dict[str, Any]):
        if room_code in self.active_connections:
            for connection in self.active_connections[room_code].values():
                await connection.send_json(message)

    async def send_to_user(self, room_code: str, user_id: int, message: Dict[str, Any]):
        if room_code in self.active_connections and user_id in self.active_connections[room_code]:
            await self.active_connections[room_code][user_id].send_json(message)

    def get_room_players(self, room_code: str) -> list:
        if room_code in self.active_connections:
            return list(self.active_connections[room_code].keys())
        return []

    def get_room_host(self, room_code: str) -> Optional[int]:
        return self.room_hosts.get(room_code)

    def set_room_host(self, room_code: str, host_id: int):
        self.room_hosts[room_code] = host_id

    def init_room_state(self, room_code: str, host_id: int):
        self.room_states[room_code] = {
            "status": "waiting",
            "players": {host_id: {"score": 0, "ready": False}},
            "game_started": False,
            "time_left": 30,
        }
        self.room_hosts[room_code] = host_id

    def get_or_init_room_state(self, room_code: str, host_id: int, player2_id: Optional[int] = None) -> Dict[str, Any]:
        if room_code not in self.room_states:
            self.room_states[room_code] = {
                "status": "waiting",
                "players": {host_id: {"score": 0, "ready": False}},
                "game_started": False,
                "time_left": 30,
            }
            if player2_id is not None:
                self.room_states[room_code]["players"][player2_id] = {"score": 0, "ready": False}
        if room_code not in self.room_hosts:
            self.room_hosts[room_code] = host_id
        return self.room_states[room_code]

    def add_player_to_state(self, room_code: str, user_id: int):
        if room_code in self.room_states:
            if user_id not in self.room_states[room_code]["players"]:
                self.room_states[room_code]["players"][user_id] = {"score": 0, "ready": False}

    def update_score(self, room_code: str, user_id: int, score: int):
        if room_code in self.room_states:
            if user_id in self.room_states[room_code]["players"]:
                self.room_states[room_code]["players"][user_id]["score"] = score

    def get_room_state(self, room_code: str) -> Optional[Dict[str, Any]]:
        return self.room_states.get(room_code)


manager = ConnectionManager()


def generate_invite_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


@router.get("/", response_class=HTMLResponse)
async def battle_lobby(
    request: Request,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    games = GameRegistry.list_games()
    
    public_rooms = db.query(
        GameRoom,
        User.username.label("host_name"),
        GameModel.name.label("game_name"),
    ).join(
        User, GameRoom.host_id == User.id
    ).join(
        GameModel, GameRoom.game_id == GameModel.id
    ).filter(
        GameRoom.is_public == True,
        GameRoom.status == "waiting",
    ).all()
    
    room_list = []
    for room, host_name, game_name in public_rooms:
        room_list.append({
            "id": room.id,
            "invite_code": room.invite_code,
            "host_name": host_name,
            "game_name": game_name,
            "game_slug": room.game.slug if room.game else None,
            "status": room.status,
            "player2_id": room.player2_id,
        })
    
    return templates.TemplateResponse(
        request,
        "battle/lobby.html",
        {
            "user": user,
            "games": games,
            "rooms": room_list,
        },
    )


@router.post("/create")
async def create_room(
    request: Request,
    game_slug: str = Form(...),
    is_public: bool = Form(True),
    db: Session = Depends(get_db),
):
    user = await get_current_user_or_401(request)
    
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
    
    invite_code = generate_invite_code()
    while db.query(GameRoom).filter(GameRoom.invite_code == invite_code).first():
        invite_code = generate_invite_code()
    
    new_room = GameRoom(
        game_id=game.id,
        host_id=user["user_id"],
        invite_code=invite_code,
        is_public=is_public,
        status="waiting",
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    manager.init_room_state(invite_code, user["user_id"])
    
    return RedirectResponse(
        url=f"/battle/room/{invite_code}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/room/{invite_code}", response_class=HTMLResponse)
async def room_page(
    request: Request,
    invite_code: str,
    db: Session = Depends(get_db),
):
    user = await get_current_user(request)
    
    if not user:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "user": None,
                "error": "Please login to join a battle room",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    
    room = db.query(
        GameRoom,
        User.username.label("host_name"),
        GameModel.name.label("game_name"),
        GameModel.slug.label("game_slug"),
    ).join(
        User, GameRoom.host_id == User.id
    ).join(
        GameModel, GameRoom.game_id == GameModel.id
    ).filter(
        GameRoom.invite_code == invite_code
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room_data, host_name, game_name, game_slug = room
    
    if room_data.status == "waiting" and room_data.player2_id is None:
        if user["user_id"] != room_data.host_id:
            room_data.player2_id = user["user_id"]
            db.commit()
            manager.add_player_to_state(invite_code, user["user_id"])
    
    player2_name = None
    if room_data.player2_id:
        player2 = db.query(User).filter(User.id == room_data.player2_id).first()
        player2_name = player2.username if player2 else None
    
    return templates.TemplateResponse(
        request,
        "battle/room.html",
        {
            "user": user,
            "room": {
                "invite_code": room_data.invite_code,
                "host_name": host_name,
                "host_id": room_data.host_id,
                "player2_name": player2_name,
                "player2_id": room_data.player2_id,
                "game_name": game_name,
                "game_slug": game_slug,
                "is_public": room_data.is_public,
                "status": room_data.status,
            },
        },
    )


@router.websocket("/ws/{invite_code}")
async def websocket_endpoint(
    websocket: WebSocket,
    invite_code: str,
    db: Session = Depends(get_db),
):
    token = websocket.cookies.get("game_platform_session")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    from app.auth import decode_access_token
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    user_id = payload.get("user_id")
    username = payload.get("username")
    if user_id is None or username is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    room = db.query(GameRoom).filter(GameRoom.invite_code == invite_code).first()
    if not room:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket, invite_code, user_id)
    
    try:
        room_state = manager.get_or_init_room_state(
            invite_code,
            room.host_id,
            room.player2_id
        )
        
        await manager.broadcast_to_room(
            invite_code,
            {
                "type": "player_joined",
                "user_id": user_id,
                "username": username,
                "players": manager.get_room_players(invite_code),
            },
        )
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            room_state = manager.get_room_state(invite_code)
            if not room_state:
                continue
            
            if message_type == "start_game":
                room_host = manager.get_room_host(invite_code)
                if room_host is None:
                    room_host = room.host_id
                
                if user_id == room_host:
                    room_state["game_started"] = True
                    room_state["status"] = "playing"
                    await manager.broadcast_to_room(
                        invite_code,
                        {
                            "type": "game_started",
                            "time_left": room_state.get("time_left", 30),
                        },
                    )
            
            elif message_type == "score_update":
                score = data.get("score", 0)
                manager.update_score(invite_code, user_id, score)
                room_state = manager.get_room_state(invite_code)
                if room_state:
                    await manager.broadcast_to_room(
                        invite_code,
                        {
                            "type": "score_update",
                            "user_id": user_id,
                            "score": score,
                            "players": room_state["players"],
                        },
                    )
            
            elif message_type == "game_ended":
                room_state = manager.get_room_state(invite_code)
                if room_state:
                    room_state["status"] = "finished"
                    await manager.broadcast_to_room(
                        invite_code,
                        {
                            "type": "game_ended",
                            "players": room_state["players"],
                        },
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(invite_code, user_id)
        await manager.broadcast_to_room(
            invite_code,
            {
                "type": "player_left",
                "user_id": user_id,
                "username": username,
                "players": manager.get_room_players(invite_code),
            },
        )
