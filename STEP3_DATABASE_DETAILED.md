# Step 3: Database Setup - Detailed Instructions

## Overview

Your dashboard needs access to the `bushel_management.db` file. For Streamlit Cloud, you have a few options. Here's the **easiest method** with detailed steps:

## Method 1: Include Database in Repository (Recommended for Getting Started)

### Step-by-Step:

#### 1. Find Your Database File

First, locate where your database file is currently stored:
- **Local:** Usually at `/path/to/Bushel_Management/data/bushel_management.db`
- **Colab/Drive:** `/content/drive/MyDrive/Colab_Notebooks/Grain_Manager/database/bushel_management.db`

#### 2. Create the `data` Folder in Your Project

```bash
cd /path/to/Bushel_Management_Reports

# Create data folder if it doesn't exist
mkdir -p data
```

#### 3. Copy Your Database File

**If database is on your local machine:**
```bash
# Replace /path/to/your/database with your actual path
cp /path/to/Bushel_Management/data/bushel_management.db data/bushel_management.db

# Verify it copied
ls -lh data/bushel_management.db
```

**If database is in Google Drive (from Colab):**
1. Download the database file from Google Drive to your local machine
2. Then copy it:
```bash
cp ~/Downloads/bushel_management.db data/bushel_management.db
```

**If you're using PyCharm:**
1. Right-click on the `Bushel_Management_Reports` folder
2. Select "New" ? "Directory"
3. Name it `data`
4. Copy your `bushel_management.db` file into that `data` folder

#### 4. Update `.gitignore` to Allow the Database File

The `.gitignore` file currently excludes all `.db` files. We need to allow this specific one:

**Option A: Edit `.gitignore` manually**

Open `.gitignore` and find this line:
```
*.db
```

Change it to:
```
*.db
!data/bushel_management.db
```

The `!` means "don't ignore this file" - it's an exception to the `*.db` rule.

**Option B: Use command line**

```bash
# Add exception to .gitignore
echo "!data/bushel_management.db" >> .gitignore
```

**Option C: Using PyCharm**
1. Open `.gitignore` file
2. Add a new line at the end: `!data/bushel_management.db`
3. Save the file

#### 5. Verify Files Are Ready

```bash
# Check that database file exists
ls -lh data/bushel_management.db

# Check .gitignore allows it
cat .gitignore | grep bushel_management.db
# Should show: !data/bushel_management.db
```

#### 6. Add and Commit to Git

```bash
# Add the database file and updated .gitignore
git add data/bushel_management.db .gitignore

# Verify what will be committed
git status

# Commit
git commit -m "Add database file for Streamlit Cloud"

# Push to GitHub
git push
```

#### 7. Verify on GitHub

1. Go to your GitHub repository: `https://github.com/Dave/bushel-management-dashboard`
2. Click on the `data` folder
3. You should see `bushel_management.db` listed
4. If you see it, you're good to go!

## Method 2: Use Streamlit Secrets (For Production/Sensitive Data)

If your database contains sensitive data, use Streamlit Cloud secrets instead:

### Step 1: Upload Database to a Cloud Storage

Upload your database to:
- Google Drive (and share link)
- Dropbox
- AWS S3
- Or any cloud storage

### Step 2: Set Up Streamlit Secrets

1. **After deploying to Streamlit Cloud**, go to your app
2. Click the **"?" (three dots)** menu ? **"Settings"**
3. Click **"Secrets"** tab
4. Add your database path or connection string:

```toml
DB_PATH = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"
```

Or if using a cloud database:
```toml
DATABASE_URL = "postgresql://user:pass@host:port/dbname"
```

### Step 3: Update `dashboard_app.py`

The code already supports this! It will automatically read from `st.secrets` if available.

## Troubleshooting

### "Database file not found" error in Streamlit Cloud

1. **Check the file is in GitHub:**
   - Go to: `https://github.com/dgableman/bushel-management-dashboard/tree/main/data`
   - Verify `bushel_management.db` is there

2. **Check the path in code:**
   - The code looks for: `data/bushel_management.db`
   - Make sure the file is exactly at that location

3. **Check file size:**
   - GitHub has a 100MB file size limit
   - If your database is larger, use Method 2 (Streamlit Secrets)

### Database file is too large for GitHub

- GitHub free accounts have a 100MB file size limit
- If your database is larger:
  - Use Method 2 (Streamlit Secrets)
  - Or compress the database first
  - Or use a cloud database service

### ".gitignore not working"

Make sure the exception comes AFTER the rule:
```gitignore
# This is correct:
*.db
!data/bushel_management.db

# This is WRONG (exception before rule):
!data/bushel_management.db
*.db
```

## Quick Checklist

- [ ] Database file copied to `data/bushel_management.db`
- [ ] `.gitignore` updated with `!data/bushel_management.db`
- [ ] Files added to git: `git add data/bushel_management.db .gitignore`
- [ ] Committed: `git commit -m "Add database file"`
- [ ] Pushed to GitHub: `git push`
- [ ] Verified file appears on GitHub in the `data/` folder

## After Setup

Once the database is in your GitHub repo:
1. Streamlit Cloud will automatically include it when deploying
2. Your dashboard will find it at `data/bushel_management.db`
3. No additional configuration needed!
