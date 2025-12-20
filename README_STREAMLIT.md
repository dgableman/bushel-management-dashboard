# Bushel Management Dashboard

Interactive web dashboard for managing bushel contracts, settlements, and storage bins.

## ?? Quick Start

### Run Locally
```bash
pip install -r requirements.txt
streamlit run dashboard_app.py
```

### Deploy to Streamlit Cloud
See [STREAMLIT_CLOUD_SETUP.md](STREAMLIT_CLOUD_SETUP.md) for detailed instructions.

## ?? Features

- ?? **Interactive Dashboard** - Filter contracts by commodity, status, and date range
- ?? **Visualizations** - Interactive Plotly charts and Matplotlib visualizations
- ?? **Export** - Export data to Excel or CSV
- ?? **Real-time Filtering** - Filter contracts dynamically
- ?? **Responsive Design** - Works on desktop, tablet, and mobile

## ??? Requirements

See `requirements.txt` for all dependencies.

## ?? Project Structure

```
??? dashboard_app.py          # Main Streamlit application
??? requirements.txt          # Python dependencies
??? .streamlit/
?   ??? config.toml          # Streamlit configuration
??? database/                 # Database connection and models
?   ??? db_connection.py
?   ??? models.py
??? reports/                  # Query functions
    ??? contract_queries.py
    ??? settlement_queries.py
    ??? bin_queries.py
```

## ?? Configuration

Set the `DB_PATH` environment variable to point to your database file, or place it in the `data/` folder.

## ?? Documentation

- [Streamlit Cloud Setup Guide](STREAMLIT_CLOUD_SETUP.md)
- [Local Development Instructions](DASHBOARD_INSTRUCTIONS.md)
- [Colab Setup](COLAB_SETUP_CHECKLIST.md)
