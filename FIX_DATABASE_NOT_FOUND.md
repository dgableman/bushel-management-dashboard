# Fix: Database File Not Found in Streamlit Cloud

## Error Message
```
Database file not found: /mount/src/bushel-management-dashboard/data/bushel_management.db
```

## Quick Fix Steps

### Step 1: Verify File is in GitHub

1. Go to your GitHub repository:
   ```
   https://github.com/dgableman/bushel-management-dashboard
   ```

2. Click on the `data` folder

3. Check if `bushel_management.db` is listed there

### Step 2A: If File is NOT in GitHub

The file wasn't pushed. Do this:

```bash
cd /path/to/Bushel_Management_Reports

# 1. Make sure data folder exists
mkdir -p data

# 2. Copy your database file to data folder
# Replace with your actual database location:
cp /path/to/your/bushel_management.db data/bushel_management.db

# 3. Check .gitignore - make sure it allows the file
# Open .gitignore and ensure it has:
#   *.db
#   !data/bushel_management.db

# 4. Add and commit
git add data/bushel_management.db
git status  # Verify it shows the file

# 5. Commit
git commit -m "Add database file to data folder"

# 6. Push to GitHub
git push

# 7. Wait 1-2 minutes for Streamlit Cloud to redeploy
```

### Step 2B: If File IS in GitHub but Still Not Found

1. **Check file size:**
   - GitHub has a 100MB limit
   - If your database is larger, it might not have uploaded

2. **Check .gitignore:**
   - Make sure `.gitignore` has: `!data/bushel_management.db`
   - The exception must come AFTER the `*.db` rule

3. **Force add the file:**
   ```bash
   git add -f data/bushel_management.db
   git commit -m "Force add database file"
   git push
   ```

### Step 3: Verify on GitHub

After pushing, verify:
1. Go to: `https://github.com/dgableman/bushel-management-dashboard/tree/main/data`
2. You should see `bushel_management.db` with a file size
3. Click on it - you should see "This file is binary" or similar

### Step 4: Redeploy on Streamlit Cloud

1. Go to your Streamlit Cloud app
2. Click the "?" menu ? "Reboot app"
3. Or just wait - it should auto-redeploy when you push to GitHub

## Alternative: Use Streamlit Secrets (If Database is Too Large)

If your database is larger than 100MB, use Streamlit Secrets:

### Step 1: Upload Database to Cloud Storage

Upload to:
- Google Drive (get shareable link)
- Dropbox
- AWS S3
- Or any cloud storage

### Step 2: Set Streamlit Secret

1. In Streamlit Cloud, go to your app
2. Click "?" ? "Settings" ? "Secrets"
3. Add:
   ```toml
   DB_PATH = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"
   ```

### Step 3: Update Code (Already Done!)

The code already reads from `os.getenv('DB_PATH')`, so it will automatically use the secret if set.

## Troubleshooting Checklist

- [ ] Database file exists in `data/` folder locally
- [ ] `.gitignore` has `!data/bushel_management.db` (exception rule)
- [ ] File was added: `git add data/bushel_management.db`
- [ ] File was committed: `git commit`
- [ ] File was pushed: `git push`
- [ ] File appears on GitHub in `data/` folder
- [ ] File size is under 100MB
- [ ] Streamlit Cloud app was redeployed/rebooted

## Still Not Working?

1. **Check the dashboard sidebar:**
   - Click the "?? Settings" expander
   - It will show what files are in the data folder
   - This helps debug the issue

2. **Check Streamlit Cloud logs:**
   - In Streamlit Cloud, click "Manage app" ? "Logs"
   - Look for any file system errors

3. **Try absolute path:**
   - In Streamlit Secrets, set:
     ```toml
     DB_PATH = "/mount/src/bushel-management-dashboard/data/bushel_management.db"
     ```
