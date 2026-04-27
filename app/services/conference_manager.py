import uuid
import random
import string
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set, List
from fastapi import WebSocket, status
from app.models import User

logger = logging.getLogger(__name__)

ROOM_TIMEOUT_MINUTES = 60
CLEANUP_INTERVAL_SECONDS = 300


def generate_room_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


class Participant:
    def __init__(self, user_id: int, username: str, websocket: WebSocket):
        self.user_id = user_id
        self.username = username
        self.websocket = websocket
        self.joined_at = datetime.utcnow()
        self.is_host = False
        self.audio_muted = False
        self.video_muted = False
        self.screen_sharing = False


class RoomState:
    def __init__(self, room_code: str, host_id: int, name: str = None):
        self.room_code = room_code
        self.name = name or f"会议 {room_code}"
        self.host_id = host_id
        self.participants: Dict[int, Participant] = {}
        self.status = "waiting"
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
        self.recording_enabled = False
        self.is_public = True
        self.max_participants = 10
        self.chat_history: List[Dict[str, Any]] = []

    def add_participant(self, participant: Participant):
        if participant.user_id == self.host_id:
            participant.is_host = True
        self.participants[participant.user_id] = participant
        self.last_active = datetime.utcnow()

    def remove_participant(self, user_id: int):
        if user_id in self.participants:
            del self.participants[user_id]
            self.last_active = datetime.utcnow()

    def get_participant_ids(self) -> List[int]:
        return list(self.participants.keys())

    def get_participants_info(self) -> List[Dict[str, Any]]:
        return [
            {
                "user_id": p.user_id,
                "username": p.username,
                "is_host": p.is_host,
                "audio_muted": p.audio_muted,
                "video_muted": p.video_muted,
                "screen_sharing": p.screen_sharing,
            }
            for p in self.participants.values()
        ]


class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, RoomState] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running: bool = False

    async def start_cleanup_task(self):
        if self._is_running:
            return
        self._is_running = True
        logger.info("Starting conference room cleanup task")
        while self._is_running:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
                self._run_cleanup()
            except asyncio.CancelledError:
                logger.info("Conference cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in conference cleanup task: {e}")

    def stop_cleanup_task(self):
        self._is_running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        logger.info("Conference cleanup task stopped")

    def _run_cleanup(self):
        cutoff_time = datetime.utcnow() - timedelta(minutes=ROOM_TIMEOUT_MINUTES)
        inactive_rooms = set()
        
        for room_code, room_state in self.rooms.items():
            if len(room_state.participants) == 0 and room_state.last_active < cutoff_time:
                inactive_rooms.add(room_code)
        
        for room_code in inactive_rooms:
            logger.info(f"Cleaning up inactive conference room: {room_code}")
            del self.rooms[room_code]

    def create_room(self, host_id: int, name: str = None, is_public: bool = True, max_participants: int = 10) -> str:
        room_code = generate_room_code()
        while room_code in self.rooms:
            room_code = generate_room_code()
        
        room = RoomState(room_code, host_id, name)
        room.is_public = is_public
        room.max_participants = max_participants
        self.rooms[room_code] = room
        
        logger.info(f"Created conference room: {room_code} by user {host_id}")
        return room_code

    def get_room(self, room_code: str) -> Optional[RoomState]:
        return self.rooms.get(room_code)

    def get_public_rooms(self) -> List[Dict[str, Any]]:
        return [
            {
                "room_code": room.room_code,
                "name": room.name,
                "host_id": room.host_id,
                "participant_count": len(room.participants),
                "max_participants": room.max_participants,
                "status": room.status,
                "created_at": room.created_at.isoformat(),
            }
            for room in self.rooms.values()
            if room.is_public and room.status in ["waiting", "active"]
        ]

    async def connect(self, websocket: WebSocket, room_code: str, user_id: int, username: str) -> bool:
        room = self.rooms.get(room_code)
        if not room:
            return False
        
        if len(room.participants) >= room.max_participants:
            return False
        
        await websocket.accept()
        
        participant = Participant(user_id, username, websocket)
        room.add_participant(participant)
        
        logger.info(f"User {user_id} ({username}) joined room {room_code}")
        return True

    def disconnect(self, room_code: str, user_id: int):
        room = self.rooms.get(room_code)
        if room:
            room.remove_participant(user_id)
            logger.info(f"User {user_id} left room {room_code}")

    async def broadcast_to_room(self, room_code: str, message: Dict[str, Any], exclude_user_id: int = None):
        room = self.rooms.get(room_code)
        if not room:
            return
        
        for participant in room.participants.values():
            if exclude_user_id and participant.user_id == exclude_user_id:
                continue
            try:
                await participant.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {participant.user_id}: {e}")

    async def send_to_user(self, room_code: str, user_id: int, message: Dict[str, Any]):
        room = self.rooms.get(room_code)
        if not room:
            return
        
        participant = room.participants.get(user_id)
        if participant:
            try:
                await participant.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")

    def add_chat_message(self, room_code: str, user_id: int, username: str, message: str):
        room = self.rooms.get(room_code)
        if not room:
            return
        
        chat_msg = {
            "user_id": user_id,
            "username": username,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        room.chat_history.append(chat_msg)
        room.last_active = datetime.utcnow()
        
        if len(room.chat_history) > 100:
            room.chat_history = room.chat_history[-50:]

    def update_participant_status(self, room_code: str, user_id: int, **kwargs):
        room = self.rooms.get(room_code)
        if not room:
            return
        
        participant = room.participants.get(user_id)
        if not participant:
            return
        
        if "audio_muted" in kwargs:
            participant.audio_muted = kwargs["audio_muted"]
        if "video_muted" in kwargs:
            participant.video_muted = kwargs["video_muted"]
        if "screen_sharing" in kwargs:
            participant.screen_sharing = kwargs["screen_sharing"]
        
        room.last_active = datetime.utcnow()


manager = ConnectionManager()
