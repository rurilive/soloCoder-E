import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.utils.migration import init_db_with_migration
    
    migration_result = init_db_with_migration(engine)
    
    for msg in migration_result.messages:
        logger.info(f"[Migration] {msg}")
    
    if migration_result.errors:
        for err in migration_result.errors:
            logger.error(f"[Migration Error] {err}")
    
    if migration_result.altered_tables:
        logger.info(
            f"[Migration] Database updated successfully. "
            f"Altered {len(migration_result.altered_tables)} table(s)."
        )
    else:
        logger.info("[Migration] Database is up to date.")
    
    return migration_result
