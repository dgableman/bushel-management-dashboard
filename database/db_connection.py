"""
Database connection utilities for read-only access.
Simplified version for Colab/reporting use.
"""
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime, date
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from database.models import Base
import re


def _parse_flexible_date(value):
    """Parse date from various formats."""
    if value is None:
        return None
    
    if isinstance(value, date):
        return value
    
    if isinstance(value, str):
        # Try ISO format first (YYYY-MM-DD)
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            pass
        
        # Try US format (M-D-YYYY or MM-DD-YYYY)
        match = re.match(r'(\d{1,2})-(\d{1,2})-(\d{4})', value)
        if match:
            month, day, year = match.groups()
            try:
                return date(int(year), int(month), int(day))
            except ValueError:
                pass
        
        # Try other formats
        for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    
    return None


def _adapt_date_for_sqlite(value):
    """Convert date to ISO format string for SQLite storage."""
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return value


# Register custom date adapter for SQLite
sqlite3.register_adapter(date, _adapt_date_for_sqlite)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas and date handlers on connection."""
    # For SQLite, we need to intercept date conversion
    # SQLAlchemy will try to parse DATE columns, but we want to handle it ourselves
    # We'll let SQLAlchemy read them as strings by not registering converters
    pass


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
    
    # Create engine without date type detection to prevent SQLAlchemy from parsing dates
    # We'll handle date parsing in our FlexibleDate TypeDecorator
    engine = create_engine(
        f'sqlite:///{db_path}',
        connect_args={
            'check_same_thread': False,
            # Don't use PARSE_DECLTYPES - let SQLAlchemy read dates as strings
            'detect_types': 0
        },
        echo=False
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













