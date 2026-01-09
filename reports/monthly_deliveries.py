"""
Monthly deliveries calculations for reporting.
"""
from datetime import date
from typing import Dict, List, Tuple
from calendar import month_name
from sqlalchemy.orm import Session
from database.models import Contract, Settlement
from reports.commodity_utils import normalize_commodity_name
from reports.crop_year_utils import (
    get_crop_year_date_range,
    is_date_in_crop_year,
    calculate_settlement_revenue,
    calculate_partial_contract_remaining
)


def calculate_settlement_gross_amount(settlement: Settlement) -> float:
    """
    Calculate gross amount for a settlement row.
    Uses gross_amount -> bushels*price (not net_amount).
    
    Args:
        settlement: Settlement object
        
    Returns:
        Gross amount (float)
    """
    if settlement.gross_amount is not None:
        return float(settlement.gross_amount)
    elif settlement.bushels is not None and settlement.price is not None:
        return float(settlement.bushels) * float(settlement.price)
    return 0.0


def get_crop_year_month_number(d: date, crop_year: int) -> int:
    """
    Get the month number within a crop year (1-12).
    October = 1, November = 2, ..., September = 12.
    
    Args:
        d: Date to check
        crop_year: Crop year
        
    Returns:
        Month number (1-12) or None if date is not in crop year
    """
    if not is_date_in_crop_year(d, crop_year):
        return None
    
    # Crop year starts in October (month 10)
    if d.month >= 10:
        # October = 1, November = 2, December = 3
        return d.month - 9
    else:
        # January = 4, February = 5, ..., September = 12
        return d.month + 3


def get_month_name_for_crop_year(month_num: int) -> str:
    """
    Get month name for crop year month number.
    Month 1 = October, Month 12 = September.
    
    Args:
        month_num: Month number (1-12)
        
    Returns:
        Month name (e.g., "October", "November", etc.)
    """
    if month_num <= 3:
        # October, November, December (months 10, 11, 12)
        return month_name[month_num + 9]
    else:
        # January through September (months 1-9)
        return month_name[month_num - 3]


def calculate_monthly_deliveries(
    db: Session, 
    crop_year: int,
    all_contracts: List[Contract] = None,
    all_settlements: List[Settlement] = None
) -> Dict[str, Dict[int, Dict[str, float]]]:
    """
    Calculate monthly deliveries for each crop in a crop year.
    
    For each month in the crop year, calculates:
    - Bushels (sold + contracted)
    - Gross amount (revenue from sold + contracted)
    - Average price (gross_amount / bushels)
    
    Only includes months that have data.
    
    Args:
        db: Database session
        crop_year: Crop year to calculate for
        all_contracts: Optional pre-fetched contracts list
        all_settlements: Optional pre-fetched settlements list
        
    Returns:
        Dictionary with crop as key, then month number, then data:
        {
            'Corn': {
                3: {  # December (month 3 of crop year)
                    'bushels': 5000.0,
                    'gross_amount': 20000.0,
                    'price': 4.0
                },
                4: {  # January
                    ...
                }
            },
            ...
        }
    """
    # Get all data if not provided
    if all_settlements is None:
        all_settlements = db.query(Settlement).all()
    if all_contracts is None:
        all_contracts = db.query(Contract).all()
    
    # Filter to crop year
    start_date, end_date = get_crop_year_date_range(crop_year)
    
    settlements_in_year = [
        s for s in all_settlements
        if s.date_delivered and is_date_in_crop_year(s.date_delivered, crop_year)
    ]
    
    contracts_in_year = [
        c for c in all_contracts
        if c.delivery_start and is_date_in_crop_year(c.delivery_start, crop_year)
    ]
    
    # Get unique crops
    crops = set()
    for s in settlements_in_year:
        if s.commodity:
            crops.add(normalize_commodity_name(db, s.commodity))
    for c in contracts_in_year:
        if c.commodity:
            crops.add(normalize_commodity_name(db, c.commodity))
    
    results = {}
    
    # Calculate for each crop
    for crop in crops:
        if crop == 'Unknown':
            continue
        
        crop_monthly_data = {}
        
        # Group settlements by month
        for settlement in settlements_in_year:
            normalized_crop = normalize_commodity_name(db, settlement.commodity)
            if normalized_crop != crop:
                continue
            
            month_num = get_crop_year_month_number(settlement.date_delivered, crop_year)
            if month_num is None:
                continue
            
            # Use gross_amount for settlements (as specified)
            bushels = settlement.bushels or 0
            gross_amount = calculate_settlement_gross_amount(settlement)
            
            if month_num not in crop_monthly_data:
                crop_monthly_data[month_num] = {
                    'bushels': 0.0,
                    'gross_amount': 0.0
                }
            
            crop_monthly_data[month_num]['bushels'] += bushels
            crop_monthly_data[month_num]['gross_amount'] += gross_amount
        
        # Group contracts by month (delivery_start month)
        for contract in contracts_in_year:
            normalized_crop = normalize_commodity_name(db, contract.commodity)
            if normalized_crop != crop:
                continue
            
            # Only process open or partial contracts
            fill_status = contract.fill_status or 'None'
            if fill_status not in ['None', 'Partial']:
                continue
            
            month_num = get_crop_year_month_number(contract.delivery_start, crop_year)
            if month_num is None:
                continue
            
            # Calculate contracted bushels and revenue for this month
            contract_bushels = 0
            contract_revenue = 0.0
            
            if fill_status == 'None':
                # Open contract: use full bushels and revenue
                contract_bushels = contract.bushels or 0
                contract_price = contract.price or 0.0
                contract_revenue = contract_bushels * contract_price
            elif fill_status == 'Partial':
                # Partial contract: calculate remaining
                remaining_revenue, remaining_bushels = calculate_partial_contract_remaining(
                    contract, all_settlements
                )
                # Ensure non-negative
                contract_bushels = max(0, remaining_bushels)
                contract_revenue = max(0.0, remaining_revenue)
            
            # Only add if we have positive values
            if contract_bushels > 0 or contract_revenue > 0:
                if month_num not in crop_monthly_data:
                    crop_monthly_data[month_num] = {
                        'bushels': 0.0,
                        'gross_amount': 0.0
                    }
                
                crop_monthly_data[month_num]['bushels'] += contract_bushels
                crop_monthly_data[month_num]['gross_amount'] += contract_revenue
        
        # Calculate average price for each month and remove months with no data
        final_monthly_data = {}
        for month_num, data in crop_monthly_data.items():
            if data['bushels'] > 0:
                data['price'] = data['gross_amount'] / data['bushels']
                final_monthly_data[month_num] = data
        
        # Only add crop if it has data
        if final_monthly_data:
            results[crop] = final_monthly_data
    
    return results
