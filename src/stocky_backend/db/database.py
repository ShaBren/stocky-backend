"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

from ..core.config import settings

# Create database engine
# Handle SQLAlchemy 2.0 requirement for explicit sync driver
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    # Convert to explicit synchronous SQLite driver
    db_url = db_url.replace("sqlite:///", "sqlite+pysqlite:///")

engine = create_engine(
    db_url,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
