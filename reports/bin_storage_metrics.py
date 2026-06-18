"""
Shared bin balance calculations for desktop and Streamlit reporting.

Keep in sync with Bushel_Management/utils/bin_storage_metrics.py
"""
from __future__ import annotations

from typing import Dict, List, Tuple


def storage_type_rank(storage) -> int:
    """Prefer Actual rows over Estimate when the same bin has both."""
    return 0 if (getattr(storage, "type", None) or "").strip() == "Actual" else 1


def preferred_crop_storage_rows(crop_storage_list: List) -> List:
    """When Actual and Estimate share location+bin+crop, keep Actual only."""
    best_by_bin_crop: Dict[Tuple[str, str, str], object] = {}
    for cs in crop_storage_list:
        key = (cs.location or "", cs.bin_name or "", cs.crop or "")
        existing = best_by_bin_crop.get(key)
        if existing is None or storage_type_rank(cs) < storage_type_rank(existing):
            best_by_bin_crop[key] = cs
    return list(best_by_bin_crop.values())


def actual_crop_storage_rows(crop_storage_list: List) -> List:
    """Actual rows only, one per location+bin+crop."""
    return [
        entry
        for entry in preferred_crop_storage_rows(crop_storage_list)
        if (getattr(entry, "type", None) or "").strip() == "Actual"
    ]


def bin_sold_bushels(settled: int, contracted: int) -> int:
    """Bushels sold or committed: settled plus contracted not yet settled."""
    settled = settled or 0
    contracted = contracted or 0
    return settled + max(0, contracted - settled)


def not_sold_bushels(initial: int, settled: int, open_contract_bushels: int) -> int:
    """Bushels in the bin not settled and not under open/partial contracts."""
    return max(0, int(initial or 0) - int(settled or 0) - int(open_contract_bushels or 0))


def format_percent(numerator: int, denominator: int) -> str:
    if not denominator:
        return "N/A"
    return f"{(numerator / denominator) * 100:.1f}%"


def _open_contract_allocation_weight(entry) -> int:
    """Bushels still committed on this bin toward open contracts."""
    contracted = int(getattr(entry, "contracted_bushels", 0) or 0)
    settled = int(getattr(entry, "settled_bushels", 0) or 0)
    return max(0, contracted - settled)


def allocate_open_contract_bushels_by_bin_key(
    storage_entries: List,
    open_contracts_by_crop: Dict[str, int],
) -> Dict[Tuple[str, str, str], int]:
    """
    Split crop-level open/partial contract bushels across Actual bins by
    remaining per-bin assignment (contracted minus settled).
    Key: (location, bin_name, crop).
    """
    entries = actual_crop_storage_rows(storage_entries)
    assigned_by_crop: Dict[str, int] = {}
    for entry in entries:
        crop = entry.crop or "Unknown"
        assigned_by_crop[crop] = assigned_by_crop.get(crop, 0) + _open_contract_allocation_weight(
            entry
        )

    allocation: Dict[Tuple[str, str, str], int] = {}
    for entry in entries:
        crop = entry.crop or "Unknown"
        key = (entry.location or "", entry.bin_name or "", crop)
        open_total = open_contracts_by_crop.get(crop, 0)
        assigned_total = assigned_by_crop.get(crop, 0)
        weight = _open_contract_allocation_weight(entry)
        if assigned_total > 0 and weight > 0:
            allocation[key] = int(round(open_total * weight / assigned_total))
        else:
            allocation[key] = 0
    return allocation


def allocate_open_contract_bushels_by_storage_id(
    storage_entries: List,
    open_contracts_by_crop: Dict[str, int],
) -> Dict[int, int]:
    """Same allocation as by_bin_key, keyed by crop_storage.id (desktop table)."""
    by_key = allocate_open_contract_bushels_by_bin_key(
        storage_entries, open_contracts_by_crop
    )
    allocated: Dict[int, int] = {}
    for entry in actual_crop_storage_rows(storage_entries):
        key = (entry.location or "", entry.bin_name or "", entry.crop or "Unknown")
        allocated[entry.id] = by_key.get(key, 0)
    return allocated


def get_bin_storage_metrics(
    crop_storage,
    capacity: int = 0,
    open_contract_bushels: float = 0,
) -> dict:
    """
    Bushel metrics for bin charts and summary tables.

    Reference height: bin capacity (finite) or initial fill (unlimited).
    Stack (bottom to top): settled, open contracts, not sold in-bin, empty space.
    """
    capacity = int(capacity or 0)
    is_unlimited = capacity == 0

    if crop_storage is None:
        reference = float(capacity) if capacity > 0 else 1.0
        return _empty_bin_metrics(capacity, is_unlimited, reference)

    current = int(getattr(crop_storage, "current_content", 0) or 0)
    initial = int(getattr(crop_storage, "initial_content", 0) or 0)
    settled = int(getattr(crop_storage, "settled_bushels", 0) or 0)
    bin_contracted_assigned = int(getattr(crop_storage, "contracted_bushels", 0) or 0)
    open_contracts = float(max(0, open_contract_bushels))

    if is_unlimited:
        reference = float(max(initial, settled + current, 1))
    else:
        reference = float(capacity)

    contracted_chart = float(min(open_contracts, max(current, 0)))
    over_contracted = float(max(0, open_contracts - current))
    not_sold = float(not_sold_bushels(initial, settled, int(open_contracts)))
    chart_not_sold = float(max(0, current - contracted_chart))
    chart_settled = float(settled)
    chart_empty = float(max(0.0, reference - settled - current))
    not_sold_pct = (not_sold / reference * 100.0) if reference > 0 else 0.0

    if current == 0 and settled > 0 and chart_empty <= 0:
        availability_label = "Empty — all settled"
    elif over_contracted > 0:
        availability_label = (
            f"Not sold: {not_sold:,.0f} bu ({not_sold_pct:.0f}%)\n"
            f"Over-contracted: {over_contracted:,.0f} bu"
        )
    else:
        availability_label = f"Not sold: {not_sold:,.0f} bu ({not_sold_pct:.0f}%)"

    return {
        "current": float(current),
        "initial": float(initial),
        "settled": float(settled),
        "contracted": contracted_chart,
        "contracted_raw": float(bin_contracted_assigned),
        "open_contracts": open_contracts,
        "not_sold": not_sold,
        "capacity": float(capacity),
        "is_unlimited": is_unlimited,
        "reference": reference,
        "chart_settled": chart_settled,
        "chart_contracted": contracted_chart,
        "chart_not_sold": chart_not_sold,
        "chart_uncontracted": chart_not_sold,
        "chart_empty": chart_empty,
        "empty_uses_settled_color": False,
        "not_sold_market": not_sold,
        "available_to_market": not_sold,
        "available_pct": not_sold_pct,
        "over_contracted": over_contracted,
        "is_empty_bin": False,
        "availability_label": availability_label,
    }


def _empty_bin_metrics(capacity: int, is_unlimited: bool, reference: float) -> dict:
    return {
        "current": 0.0,
        "initial": 0.0,
        "settled": 0.0,
        "contracted": 0.0,
        "contracted_raw": 0.0,
        "open_contracts": 0.0,
        "not_sold": 0.0,
        "capacity": float(capacity),
        "is_unlimited": is_unlimited,
        "reference": reference,
        "chart_settled": 0.0,
        "chart_contracted": 0.0,
        "chart_not_sold": 0.0,
        "chart_uncontracted": 0.0,
        "chart_empty": reference,
        "empty_uses_settled_color": True,
        "not_sold_market": 0.0,
        "available_to_market": 0.0,
        "available_pct": 0.0,
        "over_contracted": 0.0,
        "is_empty_bin": True,
        "availability_label": "Empty bin",
    }
