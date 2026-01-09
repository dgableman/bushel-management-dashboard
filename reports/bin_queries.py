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


def get_bins_with_storage_by_crop(db: Session, crop_year: int, include_empty: bool = False) -> Dict[str, List[Tuple[BinName, Optional[CropStorage]]]]:
    """
    Get bins grouped by crop from bin_names and crop_storage.
    
    Args:
        db: Database session
        crop_year: Crop year to filter storage records
        include_empty: If True, include all bins even without storage records. If False, only include bins with storage.
    
    Returns:
        Dictionary mapping crop name to list of (BinName, CropStorage or None) tuples.
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
        bins_by_crop: Dict[str, List[Tuple[BinName, Optional[CropStorage]]]] = {}
        
        for bin_name in bin_names:
            key = (bin_name.location, bin_name.bin_name)
            if key in storage_lookup:
                crop_storage = storage_lookup[key]
                crop = crop_storage.crop
                if crop not in bins_by_crop:
                    bins_by_crop[crop] = []
                bins_by_crop[crop].append((bin_name, crop_storage))
            elif include_empty:
                # If include_empty is True and bin doesn't have storage, we need to determine crop
                # For bins without storage, we could use preferred_crop from bin_name if available
                # Or create an "Unknown" category
                crop = bin_name.preferred_crop if hasattr(bin_name, 'preferred_crop') and bin_name.preferred_crop else 'Unknown'
                if crop not in bins_by_crop:
                    bins_by_crop[crop] = []
                bins_by_crop[crop].append((bin_name, None))
        
        return bins_by_crop
    except Exception:
        return {}


def get_bins_with_storage_by_location(db: Session, crop_year: int, include_empty: bool = False) -> Dict[str, List[Tuple[BinName, Optional[CropStorage]]]]:
    """
    Get bins grouped by location from bin_names and crop_storage.
    
    Args:
        db: Database session
        crop_year: Crop year to filter storage records
        include_empty: If True, include all bins even without storage records. If False, only include bins with storage.
    
    Returns:
        Dictionary mapping location name to list of (BinName, CropStorage or None) tuples.
    """
    try:
        bin_names = get_all_bin_names(db)
        crop_storage_list = get_crop_storage_for_year(db, crop_year)
        
        # Create a lookup dict for crop_storage by location+bin_name
        # Use multiple keys to handle potential variations in location/bin_name matching
        storage_lookup = {}
        for cs in crop_storage_list:
            # Primary key: location and bin_name from crop_storage
            key1 = (cs.location, cs.bin_name)
            storage_lookup[key1] = cs
            
            # Also try with bin_name from bin_names table for matching
            # (in case there are slight differences)
            if cs.location and cs.bin_name:
                key2 = (str(cs.location).strip(), str(cs.bin_name).strip())
                if key2 not in storage_lookup:
                    storage_lookup[key2] = cs
        
        # Group bins by location from bin_names
        bins_by_location: Dict[str, List[Tuple[BinName, Optional[CropStorage]]]] = {}
        
        for bin_name in bin_names:
            if not bin_name.location:
                continue  # Skip bins without a location
                
            # Try to match bin with storage record
            location = str(bin_name.location).strip()
            bin_name_str = str(bin_name.bin_name).strip() if bin_name.bin_name else ""
            
            # Try multiple key variations for matching
            key1 = (bin_name.location, bin_name.bin_name)
            key2 = (location, bin_name_str)
            
            crop_storage = None
            if key1 in storage_lookup:
                crop_storage = storage_lookup[key1]
            elif key2 in storage_lookup:
                crop_storage = storage_lookup[key2]
            
            # Include bin if: has storage OR include_empty is True
            if crop_storage or include_empty:
                if location not in bins_by_location:
                    bins_by_location[location] = []
                bins_by_location[location].append((bin_name, crop_storage))
        
        return bins_by_location
    except Exception as e:
        # Log error for debugging but return empty dict
        import logging
        logging.error(f"Error in get_bins_with_storage_by_location: {e}")
        return {}
