# Bushel Management Dashboard - How to Run

## Option 1: Run Locally (PyCharm/Terminal)

### Prerequisites
1. Install Streamlit:
   ```bash
   pip install streamlit plotly openpyxl
   ```

2. Make sure your database path is correct:
   - The script will auto-detect if you're running locally vs Colab
   - For local use, it defaults to: `{script_directory}/database/bushel_management.db`
   - If your database is elsewhere, set the `DB_PATH` environment variable:
     ```bash
     export DB_PATH="/path/to/your/bushel_management.db"
     ```

### Run the Dashboard

**In PyCharm:**
1. Right-click on `dashboard_app.py`
2. Select "Run 'dashboard_app'"
3. Or use the terminal in PyCharm:
   ```bash
   streamlit run dashboard_app.py
   ```

**In Terminal:**
```bash
cd /path/to/Bushel_Management_Reports
streamlit run dashboard_app.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

### Customize Database Path (if needed)

If your database is in a different location, you can either:

1. **Set environment variable:**
   ```bash
   export DB_PATH="/path/to/your/database/bushel_management.db"
   streamlit run dashboard_app.py
   ```

2. **Edit the script directly:**
   Open `dashboard_app.py` and modify the `DB_PATH` variable in the local paths section (around line 30).

---

## Option 2: Run in Google Colab

1. Open `colab_notebook.ipynb` in Google Colab
2. Run cells 1-3 (setup cells)
3. Run cell 5 (Standalone Dashboard Application)
4. Wait 10-20 seconds, then click the "Open Dashboard" link

---

## Features

- ?? **Sidebar Filters**: Filter by Commodity, Status, Date Range
- ?? **Overview Tab**: Summary statistics and quick charts
- ?? **Contracts Tab**: Detailed contract table
- ?? **Charts Tab**: Interactive Plotly charts
- ?? **Export Tab**: Export to Excel or CSV

---

## Troubleshooting

**Database not found:**
- Check that the `DB_PATH` is correct
- Make sure the database file exists
- Check the "Settings" expander in the sidebar for the current path

**Import errors:**
- Make sure all dependencies are installed: `pip install streamlit plotly openpyxl pandas sqlalchemy`
- Make sure the project structure is correct (database/ and reports/ folders exist)

**Port already in use:**
- Streamlit uses port 8501 by default
- If it's in use, Streamlit will automatically try the next available port
- Or specify a different port: `streamlit run dashboard_app.py --server.port=8502`
