from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import config

engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализировать базу данных"""
    Base.metadata.create_all(bind=engine)
