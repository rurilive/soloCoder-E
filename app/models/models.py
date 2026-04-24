from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_developer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("Score", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    review_replies = relationship("ReviewReply", back_populates="developer")
    hosted_rooms = relationship("GameRoom", foreign_keys="GameRoom.host_id", back_populates="host")
    joined_rooms = relationship("GameRoom", foreign_keys="GameRoom.player2_id", back_populates="player2")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    developer = Column(String(100), default="System")
    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("Score", back_populates="game")
    reviews = relationship("Review", back_populates="game")
    rooms = relationship("GameRoom", back_populates="game")


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="scores")
    user = relationship("User", back_populates="scores")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    replies = relationship("ReviewReply", back_populates="review")


class ReviewReply(Base):
    __tablename__ = "review_replies"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("Review", back_populates="replies")
    developer = relationship("User", back_populates="review_replies")


class GameRoom(Base):
    __tablename__ = "game_rooms"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invite_code = Column(String(20), unique=True, index=True, nullable=False)
    is_public = Column(Boolean, default=True)
    status = Column(String(20), default="waiting")
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="rooms")
    host = relationship("User", foreign_keys=[host_id], back_populates="hosted_rooms")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="joined_rooms")
