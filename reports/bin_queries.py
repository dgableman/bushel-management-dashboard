"""
Bin and storage-related read-only queries.
Includes functions for grouping bins by crop or location.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Tuple
from database.models import BinName, CropStorage, Contract, Settlement
from reports.commodity_utils import normalize_commodity_name
from reports.crop_year_utils import (
    calculate_partial_contract_remaining,
    is_date_in_crop_year,
)
from reports.bin_storage_metrics import (
    preferred_crop_storage_rows,
    allocate_open_contract_bushels_by_bin_key,
    get_bin_storage_metrics as _shared_bin_storage_metrics,
)


def get_all_bin_names(db: Session) -> List[BinName]:
    """Get all bin names from bin_names table."""
    try:
        return db.query(BinName).all()
    except Exception:
        # bin_names table may not exist in all databases
        return []


def _bin_names_lookup(bin_names: List[BinName]) -> Dict[Tuple[str, str], BinName]:
    lookup: Dict[Tuple[str, str], BinName] = {}
    for bin_obj in bin_names:
        lookup[(bin_obj.location, bin_obj.bin_name)] = bin_obj
        if bin_obj.location and bin_obj.bin_name:
            stripped = (str(bin_obj.location).strip(), str(bin_obj.bin_name).strip())
            lookup.setdefault(stripped, bin_obj)
    return lookup


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
        crop_storage_list = preferred_crop_storage_rows(
            get_crop_storage_for_year(db, crop_year)
        )
        bin_lookup = _bin_names_lookup(bin_names)

        bins_by_crop: Dict[str, List[Tuple[BinName, Optional[CropStorage]]]] = {}
        bins_with_storage = set()

        for cs in crop_storage_list:
            crop = cs.crop
            if not crop:
                continue
            bin_obj = bin_lookup.get((cs.location, cs.bin_name))
            if bin_obj is None and cs.location and cs.bin_name:
                bin_obj = bin_lookup.get(
                    (str(cs.location).strip(), str(cs.bin_name).strip())
                )
            if bin_obj is None:
                continue
            bins_with_storage.add((bin_obj.location, bin_obj.bin_name))
            bins_by_crop.setdefault(crop, []).append((bin_obj, cs))

        if include_empty:
            for bin_obj in bin_names:
                key = (bin_obj.location, bin_obj.bin_name)
                if key in bins_with_storage:
                    continue
                crop = (
                    bin_obj.preferred_crop
                    if hasattr(bin_obj, "preferred_crop") and bin_obj.preferred_crop
                    else "Unknown"
                )
                bins_by_crop.setdefault(crop, []).append((bin_obj, None))

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
        crop_storage_list = preferred_crop_storage_rows(
            get_crop_storage_for_year(db, crop_year)
        )
        bin_lookup = _bin_names_lookup(bin_names)

        bins_by_location: Dict[str, List[Tuple[BinName, Optional[CropStorage]]]] = {}

        for cs in crop_storage_list:
            location = str(cs.location).strip() if cs.location else ""
            if not location:
                continue
            bin_obj = bin_lookup.get((cs.location, cs.bin_name))
            if bin_obj is None and cs.bin_name:
                bin_obj = bin_lookup.get((location, str(cs.bin_name).strip()))
            if bin_obj is None:
                continue
            bins_by_location.setdefault(location, []).append((bin_obj, cs))

        if include_empty:
            for bin_obj in bin_names:
                if not bin_obj.location:
                    continue
                location = str(bin_obj.location).strip()
                has_storage = any(
                    entry[0].location == bin_obj.location
                    and entry[0].bin_name == bin_obj.bin_name
                    for entry in bins_by_location.get(location, [])
                )
                if not has_storage:
                    bins_by_location.setdefault(location, []).append((bin_obj, None))

        return bins_by_location
    except Exception as e:
        # Log error for debugging but return empty dict
        import logging
        logging.error(f"Error in get_bins_with_storage_by_location: {e}")
        return {}


def get_open_contract_bushels_by_crop(db: Session, crop_year: int) -> Dict[str, int]:
    """Remaining bushels on active open and partial contracts for the crop year, by crop."""
    all_contracts = db.query(Contract).all()
    all_settlements = db.query(Settlement).all()
    totals: Dict[str, int] = {}

    for contract in all_contracts:
        contract_status = (contract.status or "").strip()
        if contract_status.lower() != "active":
            continue
        if not contract.delivery_start or not is_date_in_crop_year(
            contract.delivery_start, crop_year
        ):
            continue
        if not contract.commodity:
            continue
        crop = normalize_commodity_name(db, contract.commodity)
        if not crop:
            continue

        fill_status = contract.fill_status or "None"
        if fill_status not in ("None", "Partial"):
            continue

        if fill_status == "None":
            remaining = contract.bushels or 0
        else:
            _, remaining = calculate_partial_contract_remaining(contract, all_settlements)

        if remaining > 0:
            totals[crop] = totals.get(crop, 0) + int(remaining)

    return totals


def build_open_contract_allocation_by_bin(
    db: Session,
    crop_year: int,
    storage_entries: Optional[List[CropStorage]] = None,
) -> Dict[Tuple[str, str, str], int]:
    """
    Allocate crop-level open/partial contract bushels to Actual storage rows by
    contracted_bushels share. Key: (location, bin_name, crop).
    """
    if storage_entries is None:
        storage_entries = get_crop_storage_for_year(db, crop_year)

    open_by_crop = get_open_contract_bushels_by_crop(db, crop_year)
    return allocate_open_contract_bushels_by_bin_key(storage_entries, open_by_crop)


def get_bin_storage_metrics(
    crop_storage,
    bin_name,
    open_contract_bushels: float = 0,
) -> dict:
    """Bushel metrics for bin charts; delegates to shared bin_storage_metrics."""
    capacity = int(bin_name.capacity or 0) if bin_name else 0
    return _shared_bin_storage_metrics(
        crop_storage, capacity=capacity, open_contract_bushels=open_contract_bushels
    )
