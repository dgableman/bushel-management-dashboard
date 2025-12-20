# Bushel Management Reports

Read-only reporting application for Bushel Management data. Designed to run in Google Colab.

## Purpose

This is a separate, read-only project that provides reporting and analysis capabilities for the Bushel Management database. It is designed to:

- Run in Google Colab (Chrome browser environment)
- Access the database file from Google Drive
- Provide read-only queries and reports
- Never modify the database

## Project Structure

```
Bushel_Management_Reports/
├── database/
│   ├── __init__.py
│   ├── models.py          # Database table definitions (read-only)
│   └── db_connection.py   # Database connection utilities
├── reports/
│   ├── __init__.py
│   ├── contract_queries.py    # Contract-related queries
│   ├── settlement_queries.py  # Settlement-related queries
│   └── bin_queries.py         # Bin/storage-related queries
├── colab_notebook.ipynb       # Google Colab notebook template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Setup

### For Google Colab:

1. Upload this project to Google Drive or GitHub
2. Open `colab_notebook.ipynb` in Google Colab
3. The notebook will:
   - Mount Google Drive
   - Download the database file from Drive
   - Set up the database connection
   - Provide example queries

### For Local Development:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Download the database file from Google Drive to your local machine

3. Use the connection utilities:
   ```python
   from database.db_connection import create_db_session
   from reports.contract_queries import get_all_contracts
   
   db = create_db_session('/path/to/bushel_management.db')
   contracts = get_all_contracts(db)
   ```

## Database Schema

The database models match the main `Bushel_Management` project. When the main database schema changes, you should update `database/models.py` to match.

### Main Tables:

- **contracts**: Crop contracts with pricing, quantities, and delivery dates
- **settlements**: Settlement records linked to contracts
- **bins**: Storage bin information
- **storage_records**: Storage transaction history

## Usage Examples

See `colab_notebook.ipynb` for complete examples.

### Basic Query Example:

```python
from database.db_connection import create_db_session
from reports.contract_queries import get_active_contracts

# Connect to database
db = create_db_session('/content/drive/MyDrive/bushel_management.db')

# Get active contracts
contracts = get_active_contracts(db)

# Process results
for contract in contracts:
    print(f"{contract.contract_number}: {contract.commodity} - {contract.bushels} bushels")
```

## Important Notes

- **Read-Only**: This project is designed to be read-only. No write operations are included.
- **Schema Sync**: When the main database schema changes, manually update `database/models.py`
- **Database Location**: The database file should be synced to Google Drive using the main Bushel_Management application's "Sync Database to Google Drive" feature

## Updating Database Models

When the main `Bushel_Management/database/models.py` changes:

1. Copy the updated model definitions to `database/models.py` in this project
2. Remove any write-specific functionality (relationships with cascade deletes, etc.)
3. Keep only the table structure and read-only properties


