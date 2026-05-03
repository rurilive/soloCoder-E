from .database import Base, engine, SessionLocal
from .models import Category

Base.metadata.create_all(bind=engine)

DEFAULT_CATEGORIES = [
    {"name": "小说", "description": "各种类型的小说作品，包括言情、科幻、悬疑等"},
    {"name": "文学", "description": "经典文学作品、散文、诗歌等文学类书籍"},
    {"name": "历史", "description": "历史著作、传记、回忆录等历史相关书籍"},
    {"name": "科技", "description": "科学技术、编程、计算机等技术类书籍"},
    {"name": "哲学", "description": "哲学思想、心理学、宗教等人文社科书籍"},
    {"name": "其他", "description": "未分类或无法归类的书籍"}
]

def init_categories():
    db = SessionLocal()
    try:
        for category_data in DEFAULT_CATEGORIES:
            existing = db.query(Category).filter(Category.name == category_data["name"]).first()
            if not existing:
                new_category = Category(
                    name=category_data["name"],
                    description=category_data["description"]
                )
                db.add(new_category)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error initializing categories: {e}")
    finally:
        db.close()

init_categories()
