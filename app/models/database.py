from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()


class MasterPassword(Base):
    """主密码表"""
    __tablename__ = "master_password"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PasswordEntryDB(Base):
    """密码条目表"""
    __tablename__ = "password_entries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    encrypted_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_db(db_url: str):
    """初始化数据库连接和表"""
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    return engine, SessionLocal


def get_db_session(SessionLocal):
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
