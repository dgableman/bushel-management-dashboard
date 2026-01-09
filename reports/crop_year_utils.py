"""
Utilities for crop year calculations and sales reporting.
"""
from datetime import date, datetime
from typing import Tuple
from sqlalchemy.orm import Session
from database.models import (
    Contract, Settlement, CropTotals, HarvestActual
)
from reports.commodity_utils import normalize_commodity_name


def get_crop_year_from_date(d: date) -> int:
    """
    Determine crop year from a date.
    Crop year runs Oct 1 - Sep 30, named by the year of Oct 1.
    Example: Oct 1, 2025 to Sep 30, 2026 = Crop Year 2025
    
    Args:
        d: Date to check
        
    Returns:
        Crop year (integer, year of Oct 1)
    """
    if d is None:
        return None
    
    # If month is October (10), November (11), or December (12), crop year is current year
    # Otherwise, crop year is previous year
    if d.month >= 10:
        return d.year
    else:
        return d.year - 1


def get_current_crop_year() -> int:
    """Get the current crop year based on today's date."""
    return get_crop_year_from_date(date.today())


def get_crop_year_date_range(crop_year: int) -> Tuple[date, date]:
    """
    Get the start and end dates for a crop year.
    
    Args:
        crop_year: Crop year (year of Oct 1)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    start_date = date(crop_year, 10, 1)
    end_date = date(crop_year + 1, 9, 30)
    return start_date, end_date


def is_date_in_crop_year(d: date, crop_year: int) -> bool:
    """
    Check if a date falls within a crop year.
    
    Args:
        d: Date to check
        crop_year: Crop year to check against
        
    Returns:
        True if date is in crop year, False otherwise
    """
    if d is None:
        return False
    
    start_date, end_date = get_crop_year_date_range(crop_year)
    return start_date <= d <= end_date


def get_starting_bushels(db: Session, crop_year: int, crop: str) -> int:
    """
    Get starting bushels for a crop and crop year.
    First tries crop_totals table (type='actual'), 
    then falls back to harvest_actual table.
    
    Args:
        db: Database session
        crop_year: Crop year
        crop: Normalized crop name
        
    Returns:
        Total starting bushels (integer)
    """
    # First try crop_totals
    crop_total = db.query(CropTotals).filter(
        CropTotals.crop_year == crop_year,
        CropTotals.crop == crop,
        CropTotals.type == 'actual'
    ).first()
    
    if crop_total:
        return crop_total.initial_content or 0
    
    # Fall back to harvest_actual - check both capitalized and lowercase versions
    harvest_records = db.query(HarvestActual).filter(
        HarvestActual.crop_year == crop_year,
        HarvestActual.crop == crop
    ).all()
    
    # Filter by status (accept various formats)
    harvest_records = [
        h for h in harvest_records
        if h.status and h.status.lower() in ['partial', 'partials', 'complete']
    ]
    
    if harvest_records:
        return sum(h.bushels or 0 for h in harvest_records)
    
    return 0


def calculate_settlement_revenue(settlement: Settlement) -> float:
    """
    Calculate revenue for a settlement row.
    Uses net_amount -> gross_amount -> bushels*price.
    
    Args:
        settlement: Settlement object
        
    Returns:
        Revenue amount (float)
    """
    if settlement.net_amount is not None:
        return float(settlement.net_amount)
    elif settlement.gross_amount is not None:
        return float(settlement.gross_amount)
    elif settlement.bushels is not None and settlement.price is not None:
        return float(settlement.bushels) * float(settlement.price)
    return 0.0
