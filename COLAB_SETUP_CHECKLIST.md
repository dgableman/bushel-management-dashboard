# Files Needed in Google Drive for dashboard_app.py in Colab

## Required File Structure

Your Google Drive should have this structure:
```
Colab_Notebooks/
??? Grain_Manager/          (or whatever folder name you use)
    ??? dashboard_app.py     ? The dashboard script
    ??? database/
    ?   ??? __init__.py
    ?   ??? db_connection.py
    ?   ??? models.py
    ??? reports/
    ?   ??? __init__.py
    ?   ??? contract_queries.py
    ?   ??? settlement_queries.py
    ?   ??? bin_queries.py
    ??? database/            ? OR data/ (see note below)
        ??? bushel_management.db
```

## Required Files List

### 1. Main Script
- ? `dashboard_app.py` - The Streamlit dashboard application

### 2. Database Module Files
- ? `database/__init__.py` - Python package marker
- ? `database/db_connection.py` - Database connection functions
- ? `database/models.py` - SQLAlchemy models

### 3. Reports Module Files
- ? `reports/__init__.py` - Python package marker
- ? `reports/contract_queries.py` - Contract query functions
- ? `reports/settlement_queries.py` - Settlement query functions
- ? `reports/bin_queries.py` - Bin storage query functions

### 4. Database File
- ? `database/bushel_management.db` - OR `data/bushel_management.db`
  - **Note:** The script currently looks for it in `database/` folder in Colab
  - If your database is in `data/` folder, you'll need to either:
    - Move it to `database/` folder in Google Drive, OR
    - Update the `DB_PATH` in the Colab cell to point to `data/` folder

## Quick Upload Checklist

1. **Upload the entire project folder structure:**
   - Upload `dashboard_app.py` to your Google Drive folder
   - Upload the `database/` folder (with all 3 files inside)
   - Upload the `reports/` folder (with all 4 files inside)
   - Upload your `bushel_management.db` file to either:
     - `database/bushel_management.db` (matches current script), OR
     - `data/bushel_management.db` (if you prefer, update DB_PATH in Colab)

2. **Verify the structure in Google Drive:**
   ```
   /content/drive/MyDrive/Colab_Notebooks/Grain_Manager/
   ??? dashboard_app.py
   ??? database/
   ?   ??? __init__.py
   ?   ??? db_connection.py
   ?   ??? models.py
   ?   ??? bushel_management.db  ? Database file here
   ??? reports/
       ??? __init__.py
       ??? contract_queries.py
       ??? settlement_queries.py
       ??? bin_queries.py
   ```

## Using the Upload Feature

If you're using the "Upload Reports Project to Google Drive" feature from the Admin tab:
- It should upload all the necessary Python files
- **Make sure to also upload your database file separately** if it's not included in the upload

## Database Path Note

**Important:** The `dashboard_app.py` script in Colab looks for the database at:
```
/content/drive/MyDrive/Colab_Notebooks/Grain_Manager/database/bushel_management.db
```

If your database is in a `data/` folder instead, you have two options:

1. **Move the database file** to the `database/` folder in Google Drive
2. **Update the DB_PATH in the Colab cell** (cell 5) to:
   ```python
   os.environ['DB_PATH'] = '/content/drive/MyDrive/Colab_Notebooks/Grain_Manager/data/bushel_management.db'
   ```

## Testing

After uploading, test by running the Colab cell. If you get import errors, check:
- All `__init__.py` files are present (they can be empty)
- Folder structure matches exactly
- File names are correct (case-sensitive)
