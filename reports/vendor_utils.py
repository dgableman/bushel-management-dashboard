"""
Vendor normalization utilities.
Functions to normalize vendor/buyer names using the vendor_mappings table (if it exists).
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict
from database.models import Base
from sqlalchemy import inspect


# Cache for vendor mappings to avoid repeated database queries
_vendor_mapping_cache: Optional[Dict[str, str]] = None
_vendor_mappings_table_exists: Optional[bool] = None


def _check_vendor_mappings_table(db: Session) -> bool:
    """Check if vendor_normalization table exists in the database."""
    global _vendor_mappings_table_exists
    
    if _vendor_mappings_table_exists is not None:
        return _vendor_mappings_table_exists
    
    try:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        _vendor_mappings_table_exists = 'vendor_normalization' in tables
        return _vendor_mappings_table_exists
    except Exception:
        _vendor_mappings_table_exists = False
        return False


def _load_vendor_mappings(db: Session) -> Dict[str, str]:
    """
    Load all vendor mappings from the database into a dictionary.
    Uses caching to avoid repeated queries.
    Only works if vendor_normalization table exists.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary mapping alias -> standard_name
    """
    global _vendor_mapping_cache
    
    if not _check_vendor_mappings_table(db):
        return {}
    
    if _vendor_mapping_cache is None:
        try:
            # Dynamically query vendor_normalization table using raw SQL
            from sqlalchemy import text
            result = db.execute(text("SELECT alias, standard_name FROM vendor_normalization"))
            _vendor_mapping_cache = {row[0]: row[1] for row in result}
        except Exception:
            _vendor_mapping_cache = {}
    
    return _vendor_mapping_cache


def normalize_vendor_name(db: Session, vendor: Optional[str]) -> str:
    """
    Normalize a vendor/buyer name using the vendor_normalization table (if it exists).
    
    If the vendor name has a mapping, returns the standard_name.
    If no mapping exists, returns the original name (or 'Unknown' if None).
    
    Args:
        db: Database session
        vendor: The vendor/buyer name to normalize (can be None)
        
    Returns:
        The normalized/standard vendor name
    """
    if vendor is None or vendor.strip() == '':
        return 'Unknown'
    
    vendor = vendor.strip()
    
    # If vendor_normalization table doesn't exist, just return the original name
    if not _check_vendor_mappings_table(db):
        return vendor
    
    mappings = _load_vendor_mappings(db)
    
    # Look up the mapping (case-insensitive lookup)
    # First try exact match
    normalized = mappings.get(vendor, None)
    if normalized:
        return normalized
    
    # Try case-insensitive lookup
    for alias, std_name in mappings.items():
        if alias.lower() == vendor.lower():
            return std_name
    
    # No mapping found, return original
    return vendor


def get_all_normalized_vendors(db: Session, contracts: list) -> list:
    """
    Get all unique normalized vendor names from a list of contracts.
    
    Args:
        db: Database session
        contracts: List of Contract objects
        
    Returns:
        List of unique normalized vendor names
    """
    vendors = set()
    for contract in contracts:
        if contract.buyer_name:
            normalized = normalize_vendor_name(db, contract.buyer_name)
            vendors.add(normalized)
    return sorted(list(vendors))
