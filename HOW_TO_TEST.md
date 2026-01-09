# How to Test Commodity Normalization

## Quick Start

### Option 1: Test Script (Fastest - No Dashboard Needed)

This tests the normalization logic without needing Streamlit:

```bash
# Install dependencies first (if not already installed)
pip3 install sqlalchemy pandas

# Run the test script
python3 test_commodity_normalization.py
```

This will show you:
- How many commodity mappings exist
- Examples of normalization (e.g., "Yellow Corn" -> "Corn")
- How contracts are grouped by normalized names
- All unique normalized commodities in your database

### Option 2: Full Dashboard Test (Visual)

To see the normalization in action in the dashboard:

```bash
# Install all dependencies
pip3 install -r requirements.txt

# Run the dashboard
streamlit run dashboard_app.py
# OR if streamlit is not in PATH:
python3 -m streamlit run dashboard_app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## What to Check

### In the Test Script Output:

✅ **Good signs:**
- Mappings are found (e.g., "Yellow Corn" -> "Corn")
- Normalization works (variations map to standard names)
- Contracts are grouped correctly
- Multiple raw names map to the same normalized name

❌ **Problems:**
- No mappings found (normalization will still work but won't group)
- Errors connecting to database
- Normalization returns original names when mappings should exist

### In the Dashboard:

1. **Sidebar Filter:**
   - Should show only standard names: "Corn", "Soybeans", "Wheat"
   - Should NOT show: "Yellow Corn", "White Corn", "Beans", etc.

2. **Overview Tab - Charts:**
   - "Bushels by Commodity" should group all corn types together
   - One bar for "Corn" (not separate bars for each type)

3. **Contracts Tab:**
   - Commodity column should show normalized names only
   - All corn variations should display as "Corn"

4. **Filtering:**
   - Select "Corn" in filter
   - Should show contracts with "Yellow Corn", "White Corn", "Field Corn", etc.
   - All should display as "Corn" in the table

5. **Charts Tab:**
   - Bar chart should use normalized names
   - Scatter plot colors should use normalized names

6. **Export:**
   - Excel/CSV exports should have normalized commodity names

## Troubleshooting

### "ModuleNotFoundError" when running test script:

```bash
pip3 install sqlalchemy pandas
```

### "ModuleNotFoundError: No module named 'streamlit'":

```bash
pip3 install -r requirements.txt
```

### Database not found:

Make sure you've copied the database:
```bash
python3 update_database.py
```

### Normalization not working:

1. Check that `commodity_mappings` table exists in database
2. Verify mappings are populated (run test script to see)
3. Clear Streamlit cache (button in sidebar) or restart dashboard

## Expected Results

### Before Normalization:
- Filter: "Corn", "Yellow Corn", "White Corn", "Field Corn", "Soybeans", "Beans"
- Charts: Separate bars for each variation
- Totals: Split across variations

### After Normalization:
- Filter: "Corn", "Soybeans", "Wheat" (standard names only)
- Charts: One bar for "Corn" (includes all types)
- Totals: Combined correctly
- Filtering: Selecting "Corn" shows all corn variations

## Quick Verification

Run this one-liner to quickly check if normalization is working:

```bash
python3 -c "
from database.db_connection import create_db_session
from database.models import CommodityMapping
from reports.commodity_utils import normalize_commodity_name

db = create_db_session('data/bushel_management.db')
mappings = db.query(CommodityMapping).count()
print(f'Found {mappings} commodity mappings')

# Test a few
test = normalize_commodity_name(db, 'Yellow Corn')
print(f'Yellow Corn -> {test}')

test = normalize_commodity_name(db, 'Beans')
print(f'Beans -> {test}')
"
```

If you see "Yellow Corn -> Corn" and "Beans -> Soybeans", normalization is working!
