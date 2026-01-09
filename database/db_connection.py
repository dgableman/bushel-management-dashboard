"""
Database connection utilities for read-only access.
Simplified version for Colab/reporting use.
"""
import sqlite3
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base


def create_db_session(db_path: str) -> Session:
    """
    Create a SQLAlchemy session for read-only database access.
    
    Args:
        db_path: Path to the SQLite database file
    
    Returns:
        SQLAlchemy Session object
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    # Create engine (read-only mode)
    engine = create_engine(
        f'sqlite:///{db_path}',
        connect_args={'check_same_thread': False}  # Allow multi-threaded access
    )
    
    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    
    return SessionLocal()


def create_sqlite_connection(db_path: str) -> sqlite3.Connection:
    """
    Create a direct SQLite connection for simple queries.
    
    Args:
        db_path: Path to the SQLite database file
    
    Returns:
        sqlite3.Connection object
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn













