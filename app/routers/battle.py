import uuid
import random
import string
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.auth import get_current_user, get_current_user_or_401
from app.models import GameRoom, Game as GameModel, User
from app.plugins.base import GameRegistry

logger = logging.getLogger(__name__)

ROOM_TIMEOUT_MINUTES = 5
CLEANUP_INTERVAL_SECONDS = 60

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}
        self.room_states: Dict[str, Dict[str, Any]] = {}
        self.room_hosts: Dict[str, int] = {}
        self.room_last_active: Dict[str, datetime] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running: bool = False

    def update_last_active(self, room_code: str):
        self.room_last_active[room_code] = datetime.utcnow()

    def get_inactive_rooms(self, timeout_minutes: int = ROOM_TIMEOUT_MINUTES) -> Set[str]:
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        inactive_rooms = set()
        for room_code, last_active in self.room_last_active.items():
            if last_active < cutoff_time:
                inactive_rooms.add(room_code)
        return inactive_rooms

    def force_disconnect_room(self, room_code: str):
        if room_code in self.active_connections:
            for user_id, websocket in list(self.active_connections[room_code].items()):
                try:
                    asyncio.create_task(websocket.close(code=status.WS_1001_GOING_AWAY))
                except Exception:
                    pass
                self.disconnect(room_code, user_id)

    def cleanup_room(self, room_code: str):
        self.force_disconnect_room(room_code)
        if room_code in self.room_last_active:
            del self.room_last_active[room_code]

    async def start_cleanup_task(self):
        if self._is_running:
            return
        self._is_running = True
        logger.info("Starting room cleanup task")
        while self._is_running:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
                self._run_cleanup()
            except asyncio.CancelledError:
                logger.info("Room cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def _run_cleanup(self):
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=ROOM_TIMEOUT_MINUTES)
            
            all_db_rooms = db.query(GameRoom).all()
            
            inactive_codes = set()
            
            for db_room in all_db_rooms:
                last_active = self.room_last_active.get(db_room.invite_code)
                
                if last_active is None:
                    last_active = db_room.last_active_at
                
                if last_active is None:
                    last_active = db_room.created_at
                
                if last_active is None or last_active < cutoff_time:
                    inactive_codes.add(db_room.invite_code)
            
            for room_code in self.room_last_active:
                if room_code not in inactive_codes:
                    if self.room_last_active[room_code] < cutoff_time:
                        inactive_codes.add(room_code)
            
            if not inactive_codes:
                return

            logger.info(f"Found {len(inactive_codes)} inactive rooms to cleanup")
            
            for room_code in inactive_codes:
                try:
                    db_room = db.query(GameRoom).filter(
                        GameRoom.invite_code == room_code
                    ).first()
                    
                    if db_room:
                        db.delete(db_room)
                        logger.info(f"Deleted room {room_code} from database (inactive for {ROOM_TIMEOUT_MINUTES} minutes)")
                    
                    self.cleanup_room(room_code)
                    logger.info(f"Cleaned up room {room_code} from memory")
                    
                except Exception as e:
                    logger.error(f"Error cleaning up room {room_code}: {e}")
            
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error during database cleanup: {e}")
        finally:
            db.close()

    def stop_cleanup_task(self):
        self._is_running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        logger.info("Room cleanup task stopped")

    async def connect(self, websocket: WebSocket, room_code: str, user_id: int):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = {}
        self.active_connections[room_code][user_id] = websocket
        self.update_last_active(room_code)

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
                if room_code in self.room_last_active:
                    del self.room_last_active[room_code]
            else:
                self.update_last_active(room_code)

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
        self.update_last_active(room_code)

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
        else:
            if host_id not in self.room_states[room_code]["players"]:
                self.room_states[room_code]["players"][host_id] = {"score": 0, "ready": False}
            if player2_id is not None and player2_id not in self.room_states[room_code]["players"]:
                self.room_states[room_code]["players"][player2_id] = {"score": 0, "ready": False}
        if room_code not in self.room_hosts:
            self.room_hosts[room_code] = host_id
        self.update_last_active(room_code)
        return self.room_states[room_code]

    def add_player_to_state(self, room_code: str, user_id: int):
        if room_code in self.room_states:
            if user_id not in self.room_states[room_code]["players"]:
                self.room_states[room_code]["players"][user_id] = {"score": 0, "ready": False}
                self.update_last_active(room_code)

    def update_score(self, room_code: str, user_id: int, score: int):
        if room_code in self.room_states:
            if user_id in self.room_states[room_code]["players"]:
                self.room_states[room_code]["players"][user_id]["score"] = score
                self.update_last_active(room_code)

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
    
    if room_data.player2_id is not None:
        if user["user_id"] != room_data.host_id and user["user_id"] != room_data.player2_id:
            return templates.TemplateResponse(
                request,
                "error.html",
                {
                    "user": user,
                    "error": "This room is full. Please try another room.",
                },
                status_code=status.HTTP_403_FORBIDDEN,
            )
    
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
    
    if room.player2_id is not None:
        if user_id != room.host_id and user_id != room.player2_id:
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
            
            manager.update_last_active(invite_code)
            
            room_state = manager.get_room_state(invite_code)
            if not room_state:
                continue
            
            if message_type == "ready":
                is_ready = data.get("ready", True)
                if user_id not in room_state["players"]:
                    room_state["players"][user_id] = {"score": 0, "ready": is_ready}
                else:
                    room_state["players"][user_id]["ready"] = is_ready
                manager.update_last_active(invite_code)
                
                players_ready = []
                for uid, pdata in room_state["players"].items():
                    players_ready.append({
                        "user_id": uid,
                        "ready": pdata.get("ready", False)
                    })
                
                await manager.broadcast_to_room(
                    invite_code,
                    {
                        "type": "player_ready",
                        "user_id": user_id,
                        "ready": is_ready,
                        "players": players_ready,
                    },
                )
            
            elif message_type == "start_game":
                room_host = manager.get_room_host(invite_code)
                if room_host is None:
                    room_host = room.host_id
                
                if user_id != room_host:
                    await manager.send_to_user(
                        invite_code,
                        user_id,
                        {
                            "type": "error",
                            "message": "Only the host can start the game"
                        },
                    )
                    continue
                
                connected_players = manager.get_room_players(invite_code)
                if len(connected_players) < 2:
                    await manager.send_to_user(
                        invite_code,
                        user_id,
                        {
                            "type": "error",
                            "message": "Need at least 2 players to start the game"
                        },
                    )
                    continue
                
                all_ready = True
                for uid in connected_players:
                    player_data = room_state["players"].get(str(uid)) or room_state["players"].get(uid)
                    if not player_data or not player_data.get("ready", False):
                        all_ready = False
                        break
                
                if not all_ready:
                    await manager.send_to_user(
                        invite_code,
                        user_id,
                        {
                            "type": "error",
                            "message": "All players must be ready to start the game"
                        },
                    )
                    continue
                
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
