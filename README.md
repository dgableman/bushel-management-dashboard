# Bushel Management Reports

Read-only reporting and analysis dashboard for Bushel Management data. Built with Streamlit and deployed to Streamlit Cloud.

## Purpose

This is a separate, read-only project that provides reporting and analysis capabilities for the Bushel Management database. It:

- Provides an interactive web dashboard via Streamlit
- Offers read-only access to contracts, settlements, and crop year data
- Never modifies the database (all operations are read-only)
- Runs on Streamlit Cloud or locally
- Supports commodity normalization for consistent reporting

## Features

- 🌾 **Crop Year Sales Dashboard** - Interactive charts showing revenue and bushels by crop year
  - Sold, Contracted, and Open amounts
  - Stacked horizontal bar charts
  - Customizable crop prices
  - Automatic crop year calculations (Oct 1 - Sep 30)

- 📊 **Export Functionality** - Export contract and settlement data
  - Excel format (.xlsx)
  - CSV format
  - Filtered by commodity, status, and date range

- 🔄 **Commodity Normalization** - Automatic grouping of commodity aliases
  - Uses `commodity_mappings` table for consistent reporting
  - Example: "Yellow Corn" and "Corn" both normalized to "Corn"

- 📅 **Crop Year Management** - Automatic crop year date calculations
  - Crop year runs from Oct 1 to Sep 30
  - Based on the year of October 1st
  - Example: Crop Year 2025 = Oct 1, 2025 - Sep 30, 2026

## Quick Start

### Access the Dashboard

**Streamlit Cloud (Recommended):**
- Dashboard is deployed and accessible via Streamlit Cloud
- See [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md) for deployment details

### Run Locally

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure database file exists:**
   - The database should be at `data/bushel_management.db`
   - Or set `DB_PATH` environment variable to point to your database

3. **Launch the dashboard:**
   ```bash
   streamlit run dashboard_app.py
   ```

4. **Open in browser:**
   - The dashboard will open at `http://localhost:8501`

## Project Structure

```
Bushel_Management_Reports/
├── dashboard_app.py              # Main Streamlit dashboard application
├── requirements.txt              # Python dependencies
├── .streamlit/
│   └── config.toml              # Streamlit configuration
├── data/
│   └── bushel_management.db     # SQLite database (included in repo)
├── database/
│   ├── __init__.py
│   ├── db_connection.py         # Database connection utilities
│   └── models.py                # SQLAlchemy ORM models (read-only)
├── reports/
│   ├── __init__.py
│   ├── contract_queries.py      # Contract-related queries
│   ├── settlement_queries.py    # Settlement-related queries
│   ├── bin_queries.py           # Bin/storage-related queries
│   ├── commodity_utils.py       # Commodity normalization utilities
│   ├── crop_year_sales.py       # Crop year sales calculations
│   └── crop_year_utils.py       # Crop year date utilities
└── README.md                    # This file
```

## Database Schema

The database models match the main `Bushel_Management` project. When the main database schema changes, you should update `database/models.py` to match.

### Main Tables:

- **contracts**: Crop contracts with pricing, quantities, delivery dates, and fill status
- **settlements**: Settlement records linked to contracts (header and detail rows)
- **commodity_mappings**: Maps commodity aliases to standard names for normalization
- **crop_totals**: Crop year totals for starting bushels (type='actual')
- **harvest_actual**: Field-level harvest data for calculating starting bushels
- **bins**: Storage bin information (optional)
- **storage_records**: Storage transaction history (optional)

## Deployment

### Streamlit Cloud (Current)

✅ **Status:** Deployed and running  
✅ **Repository:** https://github.com/dgableman/bushel-management-dashboard  
✅ **Setup Guide:** See [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md)

The dashboard is already deployed to Streamlit Cloud. See the setup guide for:
- Initial setup documentation (for reference/reproduction)
- Update workflows (code changes, database updates, etc.)
- Troubleshooting guide

### Local Development

The dashboard can be run locally for development or testing:

```bash
# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run dashboard_app.py
```

The dashboard will automatically detect the environment and use the appropriate database path:
- Local: `data/bushel_management.db` (or `DB_PATH` environment variable)
- Streamlit Cloud: Checks Streamlit secrets, then `data/bushel_management.db`
- Google Colab: Can be configured (not the primary deployment method)

## Updating the Dashboard

### Code Changes

1. Make changes locally
2. Test with: `streamlit run dashboard_app.py`
3. Commit and push:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```
4. Streamlit Cloud automatically redeploys (1-2 minutes)

### Database Updates

When the database is updated from the main Bushel_Management project:

```bash
# Copy updated database from main project
cp ../Bushel_Management/data/bushel_management.db data/

# Commit and push
git add data/bushel_management.db
git commit -m "Update database from main project"
git push origin main
```

### Database Schema Changes

When the main database schema changes:

1. Update `database/models.py` to match the new schema
2. Test locally to ensure everything works
3. Update the database file (see above)
4. Commit all changes together

For detailed workflows, see [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md).

## Configuration

### Database Path

The dashboard automatically detects the database path based on environment:

- **Local:** `data/bushel_management.db` (default)
- **Environment Variable:** Set `DB_PATH` to override
- **Streamlit Cloud:** Configured via Streamlit Secrets (optional) or uses `data/bushel_management.db`

### Commodity Normalization

Commodities are automatically normalized using the `commodity_mappings` table:
- All queries use normalized commodity names
- Filters and exports use normalized names
- Chart displays use normalized names

### Crop Year Logic

- Crop year runs from **October 1 to September 30**
- Crop year is named after the year of October 1st
- Example: **Crop Year 2025** = Oct 1, 2025 - Sep 30, 2026
- Current crop year is automatically calculated

## Important Notes

- **Read-Only:** This project is designed to be read-only. No write operations are included.
- **Schema Sync:** When the main database schema changes, update `database/models.py` to match.
- **Database Location:** The database file is included in the repository at `data/bushel_management.db` for Streamlit Cloud deployment.
- **Commodity Normalization:** All commodities are normalized using the `commodity_mappings` table for consistent reporting.

## Documentation

- **[STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md)** - Complete Streamlit Cloud deployment guide
  - Setup status and completed steps
  - Update workflows for different scenarios
  - Troubleshooting guide
  - Quick reference commands

- **[README_STREAMLIT.md](README_STREAMLIT.md)** - Quick reference for Streamlit dashboard
  - Deployment status
  - Quick start guide
  - Feature overview

- **[DASHBOARD_INSTRUCTIONS.md](DASHBOARD_INSTRUCTIONS.md)** - Detailed local development instructions

- **[UPDATE_DATABASE.md](UPDATE_DATABASE.md)** - Guide for updating the database from the main project

## Development

### Requirements

See `requirements.txt` for all dependencies. Key packages:
- `streamlit>=1.28.0` - Web framework
- `plotly>=5.17.0` - Interactive charts
- `pandas>=2.0.0` - Data manipulation
- `sqlalchemy>=2.0.0` - Database ORM

### Running Tests

Test locally before deploying:
```bash
streamlit run dashboard_app.py
```

Check that:
- Database connection works
- All tabs load correctly
- Charts display properly
- Export functions work
- Commodity normalization is applied

## Support

For issues or questions:
1. Check [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md) troubleshooting section
2. Verify database file exists and schema matches models
3. Check Streamlit Cloud deployment logs if deployed
4. Test locally to isolate issues

---

**Note:** This project has evolved from a Colab-focused reporting tool to a full Streamlit dashboard deployed on Streamlit Cloud. The dashboard is the primary interface, though the underlying query functions can still be used programmatically if needed.
