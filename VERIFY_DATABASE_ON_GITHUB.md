# Verify Database File on GitHub

## What You're Seeing

If you see:
- File name: `bushel_management.db`
- Status: "Add database file" (instead of a file size)

This usually means the file wasn't fully committed or pushed.

## Quick Fix

### Step 1: Verify Locally

```bash
cd /path/to/Bushel_Management_Reports

# Check if file exists locally
ls -lh data/bushel_management.db

# Check git status
git status
```

### Step 2: Make Sure File is Tracked

```bash
# Check if git sees the file
git ls-files data/bushel_management.db

# If nothing shows, the file isn't tracked. Add it:
git add data/bushel_management.db

# Verify it's staged
git status
# Should show: data/bushel_management.db (new file or modified)

# Commit it
git commit -m "Add database file"

# Push to GitHub
git push
```

### Step 3: Verify on GitHub

1. Go to: `https://github.com/dgableman/bushel-management-dashboard/tree/main/data`
2. Refresh the page (Ctrl+F5 or Cmd+Shift+R)
3. You should now see:
   - File name: `bushel_management.db`
   - File size: (e.g., "2.5 MB" or similar)
   - NOT "Add database file"

### Step 4: If Still Not Working

The file might be too large or blocked. Try:

```bash
# Force add (ignores .gitignore)
git add -f data/bushel_management.db

# Check file size
du -h data/bushel_management.db

# If over 100MB, GitHub won't accept it
# You'll need to use Streamlit Secrets instead (see below)

# Commit and push
git commit -m "Force add database file"
git push
```

## Alternative: If File is Too Large (>100MB)

GitHub has a 100MB file size limit. If your database is larger:

### Option 1: Use Streamlit Secrets

1. Upload database to Google Drive or cloud storage
2. Get a shareable/download link
3. In Streamlit Cloud: Settings ? Secrets
4. Add:
   ```toml
   DB_PATH = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"
   ```

### Option 2: Compress the Database

```bash
# Compress the database
gzip data/bushel_management.db
# Creates: data/bushel_management.db.gz

# Update code to handle .gz files (would need code changes)
```

## Check File Size

```bash
# Check actual file size
ls -lh data/bushel_management.db

# If it shows something like:
# -rw-r--r-- 1 user user 150M Dec 19 15:00 data/bushel_management.db
# 
# Then it's 150MB, which is too large for GitHub
```

## After Fixing

1. Wait 1-2 minutes for Streamlit Cloud to auto-redeploy
2. Or manually reboot: Streamlit Cloud ? ? menu ? Reboot app
3. Check your dashboard - it should now find the database!
