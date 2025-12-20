"""
Bin and storage-related read-only queries.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models import Bin, StorageRecord


def get_all_bins(db: Session) -> List[Bin]:
    """Get all bins."""
    return db.query(Bin).all()


def get_bin_by_number(db: Session, bin_number: str) -> Optional[Bin]:
    """Get a bin by bin number."""
    return db.query(Bin).filter(Bin.bin_number == bin_number).first()


def get_available_bins(db: Session) -> List[Bin]:
    """Get all available bins."""
    return db.query(Bin).filter(Bin.status == "Available").all()


def get_bins_by_crop_type(db: Session, crop_type: str) -> List[Bin]:
    """Get all bins for a specific crop type."""
    return db.query(Bin).filter(Bin.crop_type == crop_type).all()


def get_storage_records_by_bin(db: Session, bin_id: int) -> List[StorageRecord]:
    """Get all storage records for a specific bin."""
    return db.query(StorageRecord).filter(StorageRecord.bin_id == bin_id).all()


def get_storage_records_by_contract(db: Session, contract_id: int) -> List[StorageRecord]:
    """Get all storage records for a specific contract."""
    return db.query(StorageRecord).filter(StorageRecord.contract_id == contract_id).all()


