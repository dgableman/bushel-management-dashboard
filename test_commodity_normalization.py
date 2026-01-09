#!/usr/bin/env python3
"""
Quick test script to verify commodity normalization is working.
Run this to check that normalization functions correctly without starting the full dashboard.
"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.db_connection import create_db_session
from database.models import CommodityMapping, Contract
from reports.commodity_utils import (
    normalize_commodity_name,
    get_commodities_for_normalized_name,
    get_all_normalized_commodities
)

def test_normalization():
    """Test commodity normalization functionality."""
    print("=" * 60)
    print("Testing Commodity Normalization")
    print("=" * 60)
    
    # Connect to database
    db_path = project_root / 'data' / 'bushel_management.db'
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("   Please make sure the database file exists.")
        return False
    
    try:
        db = create_db_session(str(db_path))
        print(f"✅ Connected to database: {db_path}")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False
    
    print("\n" + "-" * 60)
    print("1. Checking commodity_mappings table...")
    print("-" * 60)
    
    # Check mappings
    mappings = db.query(CommodityMapping).all()
    if not mappings:
        print("⚠️  No commodity mappings found in database!")
        print("   The normalization will still work, but will use original names.")
    else:
        print(f"✅ Found {len(mappings)} commodity mappings")
        print("\n   Sample mappings:")
        for m in mappings[:10]:
            print(f"     '{m.alias}' -> '{m.standard_name}'")
        if len(mappings) > 10:
            print(f"     ... and {len(mappings) - 10} more")
    
    print("\n" + "-" * 60)
    print("2. Testing normalization function...")
    print("-" * 60)
    
    # Test normalization
    test_cases = [
        "Yellow Corn",
        "White Corn",
        "Field Corn",
        "Corn",
        "Soybeans",
        "Beans",
        "Soy Beans",
        "Wheat",
        "Hard Red Wheat",
        "Unknown Commodity",
        None,
        ""
    ]
    
    print("   Testing various commodity names:")
    for commodity in test_cases:
        normalized = normalize_commodity_name(db, commodity)
        status = "✅" if normalized else "❌"
        print(f"   {status} '{commodity}' -> '{normalized}'")
    
    print("\n" + "-" * 60)
    print("3. Testing reverse lookup (for filtering)...")
    print("-" * 60)
    
    # Test reverse lookup
    test_normalized = ["Corn", "Soybeans", "Wheat"]
    for norm_name in test_normalized:
        aliases = get_commodities_for_normalized_name(db, norm_name)
        print(f"   '{norm_name}' maps to: {aliases}")
    
    print("\n" + "-" * 60)
    print("4. Checking actual contracts in database...")
    print("-" * 60)
    
    # Check actual contracts
    contracts = db.query(Contract).limit(20).all()
    if not contracts:
        print("⚠️  No contracts found in database")
    else:
        print(f"✅ Found {len(contracts)} contracts (showing first 20)")
        
        # Group by normalized name
        normalized_groups = {}
        raw_commodities = set()
        
        for c in contracts:
            if c.commodity:
                raw_commodities.add(c.commodity)
                normalized = normalize_commodity_name(db, c.commodity)
                if normalized not in normalized_groups:
                    normalized_groups[normalized] = []
                normalized_groups[normalized].append(c.commodity)
        
        print(f"\n   Raw commodity names found: {len(raw_commodities)}")
        print(f"   Normalized commodity names: {len(normalized_groups)}")
        
        print("\n   Grouping examples:")
        for norm_name, aliases in list(normalized_groups.items())[:5]:
            unique_aliases = sorted(set(aliases))
            if len(unique_aliases) > 1:
                print(f"     '{norm_name}' groups: {unique_aliases}")
            else:
                print(f"     '{norm_name}': {unique_aliases[0]}")
    
    print("\n" + "-" * 60)
    print("5. Testing get_all_normalized_commodities...")
    print("-" * 60)
    
    all_contracts = db.query(Contract).all()
    normalized_list = get_all_normalized_commodities(db, all_contracts)
    print(f"✅ Found {len(normalized_list)} unique normalized commodities:")
    for norm in sorted(normalized_list):
        count = sum(1 for c in all_contracts 
                   if c.commodity and normalize_commodity_name(db, c.commodity) == norm)
        print(f"     {norm} ({count} contracts)")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\nIf you see normalized names grouping correctly above,")
    print("the normalization is working as expected.")
    print("\nNext step: Run the dashboard with:")
    print("  streamlit run dashboard_app.py")
    print("  (or: python3 -m streamlit run dashboard_app.py)")
    
    db.close()
    return True

if __name__ == "__main__":
    success = test_normalization()
    sys.exit(0 if success else 1)
