"""
Bin and storage-related read-only queries.
Includes functions for grouping bins by crop or location.
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


def get_bin_storage_metrics(crop_storage, bin_name) -> dict:
    """
    Bushel metrics for bin charts using non-overlapping segments.

    Reference height: bin capacity (finite) or initial fill (unlimited).
    Stack (bottom to top): settled, contracted, uncontracted in-bin, empty space.
    """
    capacity = int(bin_name.capacity or 0) if bin_name else 0
    is_unlimited = capacity == 0

    if crop_storage is None:
        reference = float(capacity) if capacity > 0 else 1.0
        return {
            'current': 0.0,
            'initial': 0.0,
            'settled': 0.0,
            'contracted': 0.0,
            'contracted_raw': 0.0,
            'capacity': float(capacity),
            'is_unlimited': is_unlimited,
            'reference': reference,
            'chart_settled': 0.0,
            'chart_contracted': 0.0,
            'chart_uncontracted': 0.0,
            'chart_empty': reference,
            'empty_uses_settled_color': True,
            'available_to_market': 0.0,
            'available_pct': 0.0,
            'over_contracted': 0.0,
            'is_empty_bin': True,
            'availability_label': 'Empty bin',
        }

    current = int(getattr(crop_storage, 'current_content', 0) or 0)
    initial = int(getattr(crop_storage, 'initial_content', 0) or 0)
    settled = int(getattr(crop_storage, 'settled_bushels', 0) or 0)
    contracted = int(getattr(crop_storage, 'contracted_bushels', 0) or 0)

    if is_unlimited:
        reference = float(max(initial, settled + current, 1))
    else:
        reference = float(capacity)

    contracted_chart = float(min(contracted, max(current, 0)))
    over_contracted = float(max(0, contracted - current))
    uncontracted = float(max(0, current - contracted_chart))
    chart_settled = float(settled)
    chart_empty = float(max(0.0, reference - settled - current))

    available_to_market = uncontracted
    available_pct = (available_to_market / reference * 100.0) if reference > 0 else 0.0

    if current == 0 and settled > 0 and chart_empty <= 0:
        availability_label = 'Empty — all settled'
    elif over_contracted > 0:
        availability_label = (
            f'Available: {available_to_market:,.0f} bu ({available_pct:.0f}%)\n'
            f'Over-contracted: {over_contracted:,.0f} bu'
        )
    else:
        availability_label = f'Available: {available_to_market:,.0f} bu ({available_pct:.0f}%)'

    return {
        'current': float(current),
        'initial': float(initial),
        'settled': float(settled),
        'contracted': contracted_chart,
        'contracted_raw': float(contracted),
        'capacity': float(capacity),
        'is_unlimited': is_unlimited,
        'reference': reference,
        'chart_settled': chart_settled,
        'chart_contracted': contracted_chart,
        'chart_uncontracted': uncontracted,
        'chart_empty': chart_empty,
        'empty_uses_settled_color': False,
        'available_to_market': available_to_market,
        'available_pct': available_pct,
        'over_contracted': over_contracted,
        'is_empty_bin': False,
        'availability_label': availability_label,
    }
