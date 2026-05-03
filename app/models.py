from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255))
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_read_at = Column(DateTime, default=datetime.utcnow)

    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="book", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    title = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    book = relationship("Book", back_populates="chapters")
    bookmarks = relationship("Bookmark", back_populates="chapter", cascade="all, delete-orphan")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    position = Column(Integer, default=0)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="bookmarks")
    chapter = relationship("Chapter", back_populates="bookmarks")
