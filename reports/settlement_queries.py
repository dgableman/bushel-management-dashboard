"""
Settlement-related read-only queries.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models import Settlement
from datetime import date


def get_all_settlements(db: Session) -> List[Settlement]:
    """Get all settlements."""
    return db.query(Settlement).all()


def get_settlement_by_id(db: Session, settlement_id: str) -> List[Settlement]:
    """Get all rows for a specific settlement ID."""
    return db.query(Settlement).filter(Settlement.settlement_ID == settlement_id).all()


def get_settlements_by_contract(db: Session, contract_number: str) -> List[Settlement]:
    """Get all settlements for a specific contract number."""
    return db.query(Settlement).filter(Settlement.contract_id == contract_number).all()


def get_settlements_by_status(db: Session, status: str) -> List[Settlement]:
    """Get all settlements with a specific status."""
    return db.query(Settlement).filter(Settlement.status == status).all()


def get_settlements_by_date_range(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Settlement]:
    """Get settlements within a date range (based on date_delivered)."""
    query = db.query(Settlement)
    
    if start_date:
        query = query.filter(Settlement.date_delivered >= start_date)
    if end_date:
        query = query.filter(Settlement.date_delivered <= end_date)
    
    return query.all()


def get_unique_settlement_ids(db: Session) -> List[str]:
    """Get all unique settlement IDs."""
    results = db.query(Settlement.settlement_ID).distinct().all()
    return [r[0] for r in results if r[0] is not None]


