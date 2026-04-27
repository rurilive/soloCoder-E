from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ConferenceRoom(Base):
    __tablename__ = "conference_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(8), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=True)
    max_participants = Column(Integer, default=10)
    status = Column(String(20), default="waiting")
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    recording_enabled = Column(Boolean, default=False)
    
    host = relationship("User", foreign_keys=[host_id])
    participants = relationship("ConferenceParticipant", back_populates="room")
    recordings = relationship("Recording", back_populates="room")
    
    def to_dict(self):
        return {
            "id": self.id,
            "room_code": self.room_code,
            "name": self.name,
            "host_id": self.host_id,
            "is_public": self.is_public,
            "max_participants": self.max_participants,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "recording_enabled": self.recording_enabled,
        }


class ConferenceParticipant(Base):
    __tablename__ = "conference_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("conference_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    join_time = Column(DateTime, default=datetime.utcnow)
    leave_time = Column(DateTime, nullable=True)
    is_host = Column(Boolean, default=False)
    
    room = relationship("ConferenceRoom", back_populates="participants")
    user = relationship("User")
    
    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "join_time": self.join_time.isoformat() if self.join_time else None,
            "is_host": self.is_host,
        }


class Recording(Base):
    __tablename__ = "recordings"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("conference_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    duration = Column(Integer, default=0)
    size = Column(Integer, default=0)
    mime_type = Column(String(100), default="video/webm")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    room = relationship("ConferenceRoom", back_populates="recordings")
    user = relationship("User")
    
    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "duration": self.duration,
            "size": self.size,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
