# How to Update the Database

This guide explains how to copy/update the database from your main Bushel_Management project to this reporting project.

## Quick Method: Use the Update Script

### Option 1: Automatic Detection
The script will try to find your database in common locations:

```bash
python update_database.py
```

### Option 2: Specify Source Path
Provide the path to your source database:

```bash
python update_database.py /path/to/Bushel_Management/data/bushel_management.db
```

### Option 3: Interactive
If automatic detection fails, the script will prompt you for the path.

## Manual Method

### Step 1: Find Your Source Database
Locate the database file in your main Bushel_Management project:
- Usually at: `Bushel_Management/data/bushel_management.db`
- Or: `Bushel_Management/database/bushel_management.db`

### Step 2: Copy the Database
**Using command line:**
```bash
# Replace with your actual source path
cp /path/to/Bushel_Management/data/bushel_management.db data/bushel_management.db
```

**Using PyCharm:**
1. Navigate to your main Bushel_Management project
2. Find `data/bushel_management.db` (or `database/bushel_management.db`)
3. Right-click → Copy
4. Navigate to this project's `data/` folder
5. Right-click → Paste (overwrite if it exists)

**Using file manager:**
1. Open both project folders
2. Copy `bushel_management.db` from source project's `data/` folder
3. Paste into this project's `data/` folder

### Step 3: Verify
Check that the file was copied:
```bash
ls -lh data/bushel_management.db
```

## What the Update Script Does

1. **Finds your source database** - Checks common locations or uses the path you provide
2. **Creates a backup** - Saves a timestamped backup of your current database (if it exists)
3. **Copies the database** - Copies from source to `data/bushel_management.db`
4. **Verifies the copy** - Checks that the file was copied correctly

## Common Source Database Locations

The script checks these locations automatically:
- `~/PycharmProjects/Bushel_Management/data/bushel_management.db`
- `~/PycharmProjects/Bushel_Management/database/bushel_management.db`

If your database is elsewhere, you can:
1. Provide the path as a command-line argument
2. Or let the script prompt you for it

## Notes

- The script creates backups with timestamps (e.g., `bushel_management_backup_20240101_120000.db`)
- Old backups are not automatically deleted - you can clean them up manually if needed
- The database file is already configured in `.gitignore` to be tracked in git (for Streamlit Cloud)

## Troubleshooting

**Error: "Source database not found"**
- Check that the path is correct
- Make sure the database file exists in your source project
- Use absolute paths if relative paths don't work

**Error: "Permission denied"**
- Make sure you have read access to the source database
- Make sure you have write access to the `data/` folder in this project

**Database seems outdated after update**
- Make sure you're copying from the correct source project
- Check the file modification dates to verify it's the latest version
