"""
Contract-related read-only queries.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models import Contract
from datetime import date


def get_all_contracts(db: Session) -> List[Contract]:
    """Get all contracts."""
    return db.query(Contract).all()


def get_contract_by_number(db: Session, contract_number: str) -> Optional[Contract]:
    """Get a contract by contract number."""
    return db.query(Contract).filter(Contract.contract_number == contract_number).first()


def get_active_contracts(db: Session) -> List[Contract]:
    """Get all active contracts."""
    return db.query(Contract).filter(Contract.status == "Active").all()


def get_contracts_by_commodity(db: Session, commodity: str) -> List[Contract]:
    """Get all contracts for a specific commodity."""
    return db.query(Contract).filter(Contract.commodity == commodity).all()


def get_contracts_by_status(db: Session, status: str) -> List[Contract]:
    """Get all contracts with a specific status."""
    return db.query(Contract).filter(Contract.status == status).all()


def get_contracts_by_fill_status(db: Session, fill_status: str) -> List[Contract]:
    """Get all contracts with a specific fill status."""
    return db.query(Contract).filter(Contract.fill_status == fill_status).all()


def get_contracts_by_date_range(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Contract]:
    """Get contracts within a date range (based on date_sold)."""
    query = db.query(Contract)
    
    if start_date:
        query = query.filter(Contract.date_sold >= start_date)
    if end_date:
        query = query.filter(Contract.date_sold <= end_date)
    
    return query.all()













