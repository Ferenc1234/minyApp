from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
import logging
from typing import Optional

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://mineuser:minepass@localhost:5432/minedb")
    sqlalchemy_echo: bool = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

# Database setup
settings = get_settings()
engine = create_engine(
    settings.database_url,
    echo=settings.sqlalchemy_echo,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from app.models import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger = logging.getLogger(__name__)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating database tables: {e}")
        raise
