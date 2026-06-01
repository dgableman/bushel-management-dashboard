# Bushel Management Dashboard

Interactive web dashboard for managing bushel contracts, settlements, and crop year sales.

## ✅ Deployment Status

**Streamlit Cloud:** ✅ Deployed and Running  
**Repository:** https://github.com/dgableman/bushel-management-dashboard  
**Database:** Single shared database (`data/bushel_management.db`)  
**Setup Guide:** See [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md) for complete setup documentation and update workflows.

## 🚀 Quick Start

### Run Locally
```bash
pip install -r requirements.txt
streamlit run dashboard_app.py
```

### Deploy to Streamlit Cloud
The dashboard is already deployed! See [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md) for:
- Initial setup steps (completed)
- Future update workflows (code changes, database updates, etc.)
- Troubleshooting guide

## 🌟 Features

- 🌾 **Crop Year Sales** - View revenue and bushels by crop year with sold, contracted, and open amounts
- 📊 **Interactive Visualizations** - Stacked horizontal bar charts with hover details
- 🔄 **Commodity Normalization** - Automatic grouping of commodity aliases to standard names
- 📥 **Export** - Export contract and settlement data to Excel or CSV
- 📅 **Crop Year Management** - Automatic crop year calculations (Oct 1 - Sep 30)
- 🔍 **Real-time Filtering** - Filter by normalized commodity, status, and date range

## 📋 Requirements

See `requirements.txt` for all dependencies. Key packages:
- `streamlit` - Web framework
- `plotly` - Interactive charts
- `pandas` - Data manipulation
- `sqlalchemy` - Database ORM

## 📁 Project Structure

```
Bushel_Management_Reports/
├── dashboard_app.py              # Main Streamlit application
├── requirements.txt              # Python dependencies
├── .streamlit/
│   └── config.toml              # Streamlit configuration
├── data/
│   └── bushel_management.db     # SQLite database
├── database/
│   ├── __init__.py
│   ├── db_connection.py         # Database connection utilities
│   └── models.py                # SQLAlchemy ORM models
└── reports/
    ├── __init__.py
    ├── contract_queries.py      # Contract query functions
    ├── settlement_queries.py    # Settlement query functions
    ├── commodity_utils.py       # Commodity normalization utilities
    ├── crop_year_sales.py       # Crop year sales calculations
    └── crop_year_utils.py       # Crop year date utilities
```

## ⚙️ Configuration

**Database Path:**
- Local: `data/bushel_management.db` (defaults to the main Bushel_Management project's database if present)
- Can be set via the `DB_PATH` environment variable (overrides the default)
- For Streamlit Cloud: Can be configured via Streamlit Secrets: `DB_PATH=/path/to/database.db`

**Crop Year:**
- Defaults to current crop year (Oct 1 - Sep 30)
- Based on year of October 1st
- Example: Crop Year 2025 = Oct 1, 2025 - Sep 30, 2026

## 📚 Documentation

- **[Streamlit Cloud Setup Guide](STREAMLIT_CLOUD_SETUP.md)** - Complete deployment documentation including:
  - Initial setup (completed)
  - Update workflows (code, database, dependencies, schema)
  - Troubleshooting guide
  - Quick reference commands

- **[Local Development](DASHBOARD_INSTRUCTIONS.md)** - Instructions for local development

- **[Database Updates](UPDATE_DATABASE.md)** - Guide for updating the database from the main project

## 🔄 Updating the Dashboard

### Quick Update (Code Changes)
```bash
# Make changes, then:
git add .
git commit -m "Description of changes"
git push origin main
# Streamlit Cloud auto-deploys in 1-2 minutes
```

### Update Database
```bash
# Copy from main project
cp ../Bushel_Management/data/bushel_management.db data/
git add data/bushel_management.db
git commit -m "Update database"
git push origin main
```

See [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md) for detailed workflows.

## 🐛 Troubleshooting

### Database Not Found
- Check sidebar → Settings → Verify database path
- Ensure database exists at `data/bushel_management.db`
- For Streamlit Cloud: Verify file is in GitHub repository

### Deployment Issues
- Check Streamlit Cloud deployment logs
- Verify all dependencies in `requirements.txt`
- Test locally first: `streamlit run dashboard_app.py`

### Import Errors
- Verify all `__init__.py` files exist
- Check `requirements.txt` has all packages
- Ensure `database/` and `reports/` folders are present

See [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md) for detailed troubleshooting.

## 📝 Notes

- **Commodity Normalization:** All commodities are normalized using the `commodity_mappings` table
- **Crop Year Logic:** Automatically calculates crop year based on Oct 1 - Sep 30 period
- **Database:** Read-only access for reporting (updates should be made in main Bushel_Management project)
