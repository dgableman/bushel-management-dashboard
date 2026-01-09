"""
Commodity normalization utilities.
Functions to normalize commodity names using the commodity_mappings table.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict
from database.models import CommodityMapping


# Cache for commodity mappings to avoid repeated database queries
_commodity_mapping_cache: Optional[Dict[str, str]] = None


def _load_commodity_mappings(db: Session) -> Dict[str, str]:
    """
    Load all commodity mappings from the database into a dictionary.
    Uses caching to avoid repeated queries.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary mapping alias -> standard_name
    """
    global _commodity_mapping_cache
    
    if _commodity_mapping_cache is None:
        mappings = db.query(CommodityMapping).all()
        _commodity_mapping_cache = {m.alias: m.standard_name for m in mappings}
    
    return _commodity_mapping_cache


def normalize_commodity_name(db: Session, commodity: Optional[str]) -> str:
    """
    Normalize a commodity name using the commodity_mappings table.
    
    If the commodity name has a mapping, returns the standard_name.
    If no mapping exists, returns the original name (or 'Unknown' if None).
    
    Args:
        db: Database session
        commodity: The commodity name to normalize (can be None)
        
    Returns:
        The normalized/standard commodity name
    """
    if commodity is None or commodity.strip() == '':
        return 'Unknown'
    
    commodity = commodity.strip()
    mappings = _load_commodity_mappings(db)
    
    # Look up the mapping
    normalized = mappings.get(commodity, commodity)
    
    return normalized


def get_commodities_for_normalized_name(db: Session, normalized_name: str) -> list:
    """
    Get all commodity aliases that map to a given normalized name.
    Useful for filtering contracts by normalized commodity name.
    
    Args:
        db: Database session
        normalized_name: The normalized/standard commodity name
        
    Returns:
        List of all commodity aliases that map to this normalized name
    """
    mappings = _load_commodity_mappings(db)
    # Find all aliases that map to this normalized name
    aliases = [alias for alias, std_name in mappings.items() if std_name == normalized_name]
    # Also include the normalized name itself in case it's used directly
    if normalized_name not in aliases:
        aliases.append(normalized_name)
    return aliases


def get_all_normalized_commodities(db: Session, contracts: list) -> list:
    """
    Get a list of all unique normalized commodity names from a list of contracts.
    
    Args:
        db: Database session
        contracts: List of Contract objects
        
    Returns:
        Sorted list of unique normalized commodity names
    """
    normalized_names = set()
    for contract in contracts:
        if contract.commodity:
            normalized = normalize_commodity_name(db, contract.commodity)
            normalized_names.add(normalized)
    return sorted(list(normalized_names))


def clear_commodity_cache():
    """
    Clear the commodity mapping cache.
    Call this if the commodity_mappings table has been updated.
    """
    global _commodity_mapping_cache
    _commodity_mapping_cache = None
