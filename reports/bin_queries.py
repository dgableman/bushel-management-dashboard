"""
Bin and storage-related read-only queries.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Tuple
from database.models import BinName, CropStorage


def get_all_bin_names(db: Session) -> List[BinName]:
    """Get all bin names from bin_names table."""
    try:
        return db.query(BinName).all()
    except Exception:
        # bin_names table may not exist in all databases
        return []


def get_crop_storage_for_year(db: Session, crop_year: int) -> List[CropStorage]:
    """Get all crop storage records for a specific crop year."""
    try:
        return db.query(CropStorage).filter(CropStorage.crop_year == crop_year).all()
    except Exception:
        return []


def get_bins_with_storage_by_crop(db: Session, crop_year: int) -> Dict[str, List[Tuple[BinName, CropStorage]]]:
    """
    Get bins grouped by crop from bin_names and crop_storage.
    
    Returns a dictionary mapping crop name to list of (BinName, CropStorage) tuples.
    """
    try:
        bin_names = get_all_bin_names(db)
        crop_storage_list = get_crop_storage_for_year(db, crop_year)
        
        # Create a lookup dict for crop_storage by location+bin_name
        storage_lookup = {}
        for cs in crop_storage_list:
            key = (cs.location, cs.bin_name)
            storage_lookup[key] = cs
        
        # Group bins by crop from crop_storage
        bins_by_crop: Dict[str, List[Tuple[BinName, CropStorage]]] = {}
        
        for bin_name in bin_names:
            key = (bin_name.location, bin_name.bin_name)
            if key in storage_lookup:
                crop_storage = storage_lookup[key]
                crop = crop_storage.crop
                if crop not in bins_by_crop:
                    bins_by_crop[crop] = []
                bins_by_crop[crop].append((bin_name, crop_storage))
        
        return bins_by_crop
    except Exception:
        return {}
