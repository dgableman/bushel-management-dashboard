# Testing Commodity Normalization

This guide explains how to test that commodity normalization is working correctly in the dashboard.

## Quick Test Steps

### 1. Start the Dashboard

From the project directory, run:

```bash
streamlit run dashboard_app.py
```

Or if streamlit is not in your PATH:

```bash
python3 -m streamlit run dashboard_app.py
```

The dashboard will open in your browser (usually at `http://localhost:8501`).

### 2. Verify Normalization is Working

#### Test 1: Check Filter Dropdown
1. Look at the **Commodity** filter in the sidebar
2. You should see **normalized names only** (e.g., "Corn", "Soybeans", "Wheat")
3. You should **NOT** see variations like "Yellow Corn", "White Corn", "Beans", etc.

#### Test 2: Check Summary Statistics
1. Go to the **📊 Overview** tab
2. Look at the **"Bushels by Commodity (Contracts)"** chart
3. All variations of the same commodity should be grouped together:
   - "Yellow Corn", "White Corn", "Field Corn" should all appear as "Corn"
   - "Beans", "Soy Beans", "Soybean" should all appear as "Soybeans"

#### Test 3: Check Contract Details
1. Go to the **📋 Contracts** tab
2. Look at the **Commodity** column in the table
3. All commodity names should be normalized (standard names only)

#### Test 4: Test Filtering
1. In the sidebar, select a normalized commodity (e.g., "Corn")
2. The filtered results should include **all variations**:
   - Contracts with "Yellow Corn" should appear
   - Contracts with "White Corn" should appear
   - Contracts with "Field Corn" should appear
   - All should show as "Corn" in the table

#### Test 5: Check Charts
1. Go to the **📈 Charts** tab
2. Check the **"Total Bushels by Commodity"** bar chart
3. Commodities should be grouped by normalized names
4. Check the **"Price vs Bushels"** scatter plot
5. Color coding should use normalized commodity names

#### Test 6: Check Exports
1. Go to the **📥 Export** tab
2. Export to Excel or CSV
3. Open the exported file
4. Verify that the **Commodity** column contains normalized names only

## Expected Behavior

### Before Normalization:
- Filter dropdown might show: "Corn", "Yellow Corn", "White Corn", "Field Corn", "Soybeans", "Beans", "Soy Beans"
- Charts would show separate bars for each variation
- Totals would be split across variations

### After Normalization:
- Filter dropdown shows: "Corn", "Soybeans", "Wheat", etc. (standard names only)
- Charts group all variations together (one bar for "Corn" includes all corn types)
- Totals are combined correctly
- Filtering by "Corn" shows all corn variations

## Troubleshooting

### If normalization doesn't appear to work:

1. **Check database connection:**
   - Look at the sidebar "Settings" section
   - Verify the database path is correct
   - Check that the database file exists

2. **Check commodity_mappings table:**
   - The table should exist in the database
   - It should have mappings defined
   - Run this to check:
   ```python
   python3 -c "from database.db_connection import create_db_session; from database.models import CommodityMapping; db = create_db_session('data/bushel_management.db'); mappings = db.query(CommodityMapping).all(); print(f'Found {len(mappings)} mappings'); [print(f'{m.alias} -> {m.standard_name}') for m in mappings[:10]]"
   ```

3. **Clear Streamlit cache:**
   - Click the "🔄 Clear Cache & Retry Connection" button in the sidebar
   - Or restart the Streamlit server

4. **Check for errors:**
   - Look at the terminal where Streamlit is running
   - Check for any error messages in red in the dashboard

## Manual Verification Query

You can also verify the mappings directly:

```python
from database.db_connection import create_db_session
from database.models import CommodityMapping, Contract
from reports.commodity_utils import normalize_commodity_name

db = create_db_session('data/bushel_management.db')

# Check mappings
mappings = db.query(CommodityMapping).all()
print(f"Total mappings: {len(mappings)}")
for m in mappings[:10]:
    print(f"  {m.alias} -> {m.standard_name}")

# Check some contracts
contracts = db.query(Contract).limit(10).all()
print("\nSample contracts:")
for c in contracts:
    if c.commodity:
        normalized = normalize_commodity_name(db, c.commodity)
        print(f"  {c.contract_number}: '{c.commodity}' -> '{normalized}'")
```

## What to Look For

✅ **Success indicators:**
- Filter dropdown shows only standard commodity names
- Charts group variations together
- Filtering works across all variations
- Exports use normalized names
- No duplicate commodity groups in summaries

❌ **Problem indicators:**
- Filter dropdown shows variations (Yellow Corn, White Corn, etc.)
- Charts show separate bars for variations
- Filtering doesn't include all variations
- Totals are split incorrectly
