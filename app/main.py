import os
import shutil
from datetime import datetime
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, Book, Chapter, Bookmark
from .parser import BookParser

Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-Reader")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class BookmarkCreate(BaseModel):
    book_id: int
    chapter_id: int
    position: int = 0
    note: str = ""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/reader/{book_id}", response_class=HTMLResponse)
async def reader(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse(request, "reader.html", context={"book": book})


@app.post("/upload/")
async def upload_book(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith('.epub') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Only .epub and .txt files are supported")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        title, author, chapters = BookParser.parse(file_path)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")
    
    db_book = Book(
        title=title,
        author=author,
        file_path=file_path,
        file_type=os.path.splitext(file.filename)[1][1:]
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    for order, chapter_data in enumerate(chapters):
        db_chapter = Chapter(
            book_id=db_book.id,
            title=chapter_data['title'],
            order=order,
            level=chapter_data.get('level', 1),
            content=chapter_data['content']
        )
        db.add(db_chapter)
    
    db.commit()
    
    return JSONResponse(content={
        "id": db_book.id,
        "title": db_book.title,
        "author": db_book.author,
        "chapters_count": len(chapters)
    })


@app.get("/books/")
async def get_books(db: Session = Depends(get_db)):
    books = db.query(Book).order_by(Book.last_read_at.desc()).all()
    return JSONResponse(content=[{
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "file_type": book.file_type,
        "created_at": book.created_at.isoformat() if book.created_at else None,
        "last_read_at": book.last_read_at.isoformat() if book.last_read_at else None
    } for book in books])


@app.get("/books/{book_id}")
async def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book.last_read_at = datetime.utcnow()
    db.commit()
    
    chapters = db.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.order).all()
    
    return JSONResponse(content={
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "file_type": book.file_type,
        "chapters": [{
            "id": chapter.id,
            "title": chapter.title,
            "order": chapter.order,
            "level": chapter.level
        } for chapter in chapters]
    })


@app.get("/chapters/{chapter_id}")
async def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    book = db.query(Book).filter(Book.id == chapter.book_id).first()
    book.last_read_at = datetime.utcnow()
    db.commit()
    
    return JSONResponse(content={
        "id": chapter.id,
        "book_id": chapter.book_id,
        "title": chapter.title,
        "order": chapter.order,
        "content": chapter.content
    })


@app.post("/bookmarks/")
async def create_bookmark(bookmark: BookmarkCreate, db: Session = Depends(get_db)):
    db_bookmark = Bookmark(
        book_id=bookmark.book_id,
        chapter_id=bookmark.chapter_id,
        position=bookmark.position,
        note=bookmark.note
    )
    db.add(db_bookmark)
    db.commit()
    db.refresh(db_bookmark)
    
    return JSONResponse(content={
        "id": db_bookmark.id,
        "book_id": db_bookmark.book_id,
        "chapter_id": db_bookmark.chapter_id,
        "position": db_bookmark.position,
        "note": db_bookmark.note,
        "created_at": db_bookmark.created_at.isoformat()
    })


@app.get("/bookmarks/{book_id}")
async def get_bookmarks(book_id: int, db: Session = Depends(get_db)):
    bookmarks = db.query(Bookmark).filter(Bookmark.book_id == book_id).order_by(Bookmark.created_at.desc()).all()
    
    return JSONResponse(content=[{
        "id": bookmark.id,
        "book_id": bookmark.book_id,
        "chapter_id": bookmark.chapter_id,
        "chapter_title": db.query(Chapter).filter(Chapter.id == bookmark.chapter_id).first().title,
        "position": bookmark.position,
        "note": bookmark.note,
        "created_at": bookmark.created_at.isoformat()
    } for bookmark in bookmarks])


@app.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    bookmark = db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()
    
    return JSONResponse(content={"message": "Bookmark deleted successfully"})


@app.delete("/books/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if os.path.exists(book.file_path):
        os.remove(book.file_path)
    
    db.delete(book)
    db.commit()
    
    return JSONResponse(content={"message": "Book deleted successfully"})
