"""
Database configuration and session management.
"""

from sqlmodel import Session, create_engine
import os

# Database URL - use environment variable or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,  # Set to True for SQL query logging
)


def create_db_and_tables():
    """Create database tables."""
    from models import Summary

    Summary.metadata.create_all(engine)


def get_session() -> Session:
    """Get database session for terminal use."""
    return Session(engine)
