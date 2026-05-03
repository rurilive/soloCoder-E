import os
import shutil
from datetime import datetime
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, Book, Chapter, Bookmark, Category
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


class BookCategoryUpdate(BaseModel):
    category_id: int = None


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
async def upload_book(
    file: UploadFile = File(...), 
    category_id: int = Form(None),
    db: Session = Depends(get_db)
):
    if not (file.filename.endswith('.epub') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Only .epub and .txt files are supported")
    
    if category_id is not None:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category ID")
    
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
        file_type=os.path.splitext(file.filename)[1][1:],
        category_id=category_id
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
    
    category_name = None
    if db_book.category:
        category_name = db_book.category.name
    
    return JSONResponse(content={
        "id": db_book.id,
        "title": db_book.title,
        "author": db_book.author,
        "category_id": db_book.category_id,
        "category_name": category_name,
        "chapters_count": len(chapters)
    })


@app.get("/books/")
async def get_books(category_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Book)
    if category_id is not None:
        query = query.filter(Book.category_id == category_id)
    books = query.order_by(Book.last_read_at.desc()).all()
    
    return JSONResponse(content=[{
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "file_type": book.file_type,
        "category_id": book.category_id,
        "category_name": book.category.name if book.category else None,
        "created_at": book.created_at.isoformat() if book.created_at else None,
        "last_read_at": book.last_read_at.isoformat() if book.last_read_at else None
    } for book in books])


@app.put("/books/{book_id}/category")
async def update_book_category(
    book_id: int, 
    category_update: BookCategoryUpdate,
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if category_update.category_id is not None:
        category = db.query(Category).filter(Category.id == category_update.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category ID")
    
    book.category_id = category_update.category_id
    db.commit()
    db.refresh(book)
    
    return JSONResponse(content={
        "id": book.id,
        "title": book.title,
        "category_id": book.category_id,
        "category_name": book.category.name if book.category else None
    })


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
        "level": chapter.level,
        "content": chapter.content
    })


@app.get("/books/{book_id}/raw-content")
async def get_book_raw_content(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if not os.path.exists(book.file_path):
        raise HTTPException(status_code=404, detail="Original file not found")
    
    book.last_read_at = datetime.utcnow()
    db.commit()
    
    file_type = book.file_type.lower()
    
    if file_type == 'txt':
        try:
            with open(book.file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except UnicodeDecodeError:
            with open(book.file_path, 'r', encoding='gbk') as f:
                raw_content = f.read()
        
        return JSONResponse(content={
            "book_id": book.id,
            "title": book.title,
            "file_type": "txt",
            "content": raw_content
        })
    
    elif file_type == 'epub':
        from ebooklib import epub
        from bs4 import BeautifulSoup
        
        book_epub = epub.read_epub(book.file_path)
        raw_content_parts = []
        
        for item in book_epub.get_items():
            if item.get_type() == 9:
                content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')
                
                for script in soup(['script', 'style']):
                    script.decompose()
                
                text_content = soup.get_text(separator='\n', strip=False)
                if text_content.strip():
                    raw_content_parts.append(text_content)
        
        raw_content = '\n\n'.join(raw_content_parts)
        
        return JSONResponse(content={
            "book_id": book.id,
            "title": book.title,
            "file_type": "epub",
            "content": raw_content
        })
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")


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


@app.get("/categories/")
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.id).all()
    return JSONResponse(content=[{
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "books_count": len(category.books)
    } for category in categories])


@app.get("/categories/{category_id}")
async def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return JSONResponse(content={
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "books_count": len(category.books)
    })
