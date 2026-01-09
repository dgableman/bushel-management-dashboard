"""
Crop year sales calculations for reporting.
"""
from typing import Dict, List
from sqlalchemy.orm import Session
from database.models import Contract, Settlement
from reports.commodity_utils import normalize_commodity_name
from reports.crop_year_utils import (
    is_date_in_crop_year,
    get_starting_bushels,
    calculate_settlement_revenue,
    calculate_partial_contract_remaining
)


def calculate_crop_year_sales(db: Session, crop_year: int) -> Dict[str, Dict]:
    """
    Calculate sold, contracted, and open revenue/bushels for each crop in a crop year.
    
    Args:
        db: Database session
        crop_year: Crop year to calculate for
        
    Returns:
        Dictionary with crop as key, containing:
        {
            'sold_revenue': float,
            'sold_bushels': int,
            'contracted_revenue': float,
            'contracted_bushels': int,
            'open_bushels': int,
            'open_revenue': float  # Will need price input
        }
    """
    results = {}
    
    # Get all settlements (need all for partial contract calculations)
    all_settlements = db.query(Settlement).all()
    settlements_in_year = [
        s for s in all_settlements 
        if s.date_delivered and is_date_in_crop_year(s.date_delivered, crop_year)
    ]
    
    # Debug: Log settlement counts
    # print(f"DEBUG: Total settlements: {len(all_settlements)}")
    # print(f"DEBUG: Settlements in crop year {crop_year}: {len(settlements_in_year)}")
    # for s in settlements_in_year[:5]:  # First 5
    #     print(f"  - {s.commodity}, {s.date_delivered}, status={s.status}")
    
    # Get all contracts (need all for partial contract calculations)
    all_contracts = db.query(Contract).all()
    contracts_in_year = [
        c for c in all_contracts
        if c.delivery_start and is_date_in_crop_year(c.delivery_start, crop_year)
    ]
    
    # Get unique crops from settlements and contracts
    crops = set()
    for s in settlements_in_year:
        if s.commodity:
            crops.add(normalize_commodity_name(db, s.commodity))
    for c in contracts_in_year:
        if c.commodity:
            crops.add(normalize_commodity_name(db, c.commodity))
    
    # Calculate for each crop
    for crop in crops:
        if crop == 'Unknown':
            continue
            
        # 1. Calculate SOLD revenue and bushels (header rows only)
        sold_revenue = 0.0
        sold_bushels = 0
        for s in settlements_in_year:
            normalized_crop = normalize_commodity_name(db, s.commodity)
            if normalized_crop == crop:
                # Check status - handle case-insensitive and various formats
                status = (s.status or '').strip()
                if status.lower() == 'header':
                    # Sold revenue from header
                    revenue = calculate_settlement_revenue(s)
                    sold_revenue += revenue
                    # Sold bushels from header only
                    if s.bushels:
                        sold_bushels += s.bushels
        
        # 2. Calculate CONTRACTED revenue and bushels (only Active contracts with fill_status None or Partial)
        contracted_revenue = 0.0
        contracted_bushels = 0
        
        for contract in contracts_in_year:
            # Filter by status='Active'
            contract_status = (contract.status or '').strip()
            if contract_status.lower() != 'active':
                continue
            
            normalized_crop = normalize_commodity_name(db, contract.commodity)
            if normalized_crop != crop:
                continue
            
            contract_bushels = contract.bushels or 0
            contract_price = contract.price or 0.0
            fill_status = contract.fill_status or 'None'
            
            # Only count contracts with fill_status None or Partial
            if fill_status == 'None':
                # Easy part: no bushels delivered
                contracted_revenue += contract_bushels * contract_price
                contracted_bushels += contract_bushels
            elif fill_status == 'Partial':
                # Partial: calculate remaining using reusable function
                remaining_revenue, remaining_bushels = calculate_partial_contract_remaining(
                    contract, all_settlements
                )
                contracted_revenue += remaining_revenue
                contracted_bushels += remaining_bushels
        
        # 3. Calculate OPEN bushels
        starting_bushels = get_starting_bushels(db, crop_year, crop)
        open_bushels = max(0, starting_bushels - sold_bushels - contracted_bushels)
        
        results[crop] = {
            'sold_revenue': sold_revenue,
            'sold_bushels': sold_bushels,
            'contracted_revenue': contracted_revenue,
            'contracted_bushels': contracted_bushels,
            'open_bushels': open_bushels,
            'open_revenue': 0.0  # Will be calculated with price input
        }
    
    return results
