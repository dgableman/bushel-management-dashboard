# Streamlit Cloud Setup Guide

**Status: ✅ Setup Complete** (as of January 2026)

This guide documents the Streamlit Cloud deployment setup for the Bushel Management Dashboard.

## 📋 Current Setup Status

✅ **Repository:** https://github.com/dgableman/bushel-management-dashboard  
✅ **GitHub Username:** `dgableman`  
✅ **Authentication:** Personal Access Token (PAT) configured  
✅ **Database:** Username-based database files (`{username}_bushel_management.db`)  
✅ **Streamlit Secrets:** Supported (configured in `dashboard_app.py`)  
✅ **Remote URL:** `https://github.com/dgableman/bushel-management-dashboard.git`  
✅ **Username Feature:** Users must enter username on first load to access their database

---

## 🚀 Initial Setup (Completed - For Reference)

### Step 1: Repository Setup

1. **Created GitHub repository:**
   - Repository: `bushel-management-dashboard`
   - URL: https://github.com/dgableman/bushel-management-dashboard
   - Visibility: Public (required for free Streamlit Cloud)

2. **Configured Git remote:**
   ```bash
   git remote add origin https://github.com/dgableman/bushel-management-dashboard.git
   ```

### Step 2: GitHub Authentication Setup

**Username:** `dgableman`

**Authentication Method:** Personal Access Token (PAT)

1. **Created Personal Access Token:**
   - Go to: https://github.com/settings/tokens
   - Generate new token (classic)
   - Scope: `repo` (full control of private repositories)
   - Copy token immediately (only shown once)

2. **Using the token:**
   - When prompted for password during `git push`, use the Personal Access Token
   - Username: `dgableman`
   - Password: `[your Personal Access Token]`

3. **Optional - Store credentials:**
   ```bash
   git config --global credential.helper store
   ```
   This saves your credentials so you don't need to enter them each time.

### Step 3: Database Configuration

**Method Used:** Username-based database files

1. **Username-based database paths:**
   - Each user enters their username on first load
   - Database file: `{username}_bushel_management.db`
   - Location: `data/{username}_bushel_management.db`
   - Allows multiple users to have separate databases

2. **Database files:**
   - Can be committed to repository (one per user)
   - Or stored externally and accessed via Streamlit Secrets
   - Format: `{username}_bushel_management.db`

3. **Configured `.gitignore`:**
   - Can add exceptions for specific user databases: `!data/*_bushel_management.db`
   - Or ignore all and use Streamlit Secrets for database paths

**⚠️ Note:** If databases contain sensitive data, use Streamlit Secrets (Option 2) instead of committing to repository.

### Step 4: Code Deployment

1. **Committed initial setup:**
   ```bash
   git add dashboard_app.py database/models.py reports/*.py data/bushel_management.db
   git commit -m "Add Crop Year Sales tab with commodity normalization"
   ```

2. **Key files included:**
   - `dashboard_app.py` - Main Streamlit application
   - `requirements.txt` - Python dependencies
   - `database/` - Database models and connection
   - `reports/` - Query functions and utilities
   - `data/bushel_management.db` - Database file
   - `.streamlit/config.toml` - Streamlit configuration

3. **Push to GitHub:**
   ```bash
   git push origin main
   ```
   (Requires authentication with username `dgableman` and Personal Access Token)

### Step 5: Streamlit Cloud Deployment

1. **Sign up/Login:**
   - Go to: https://share.streamlit.io/
   - Connect GitHub account (`dgableman`)

2. **Create new app:**
   - Repository: `dgableman/bushel-management-dashboard`
   - Branch: `main`
   - Main file: `dashboard_app.py`
   - Click "Deploy"

3. **App URL:**
   - Format: `https://bushel-management-dashboard.streamlit.app`
   - (Or custom URL if configured)

---

## 🔄 Future Updates - Different Workflows

### Workflow 1: Code Changes Only (Most Common)

**When:** Making changes to Python code, adding features, fixing bugs

**Steps:**
1. Make changes to your code locally
2. Stage changes:
   ```bash
   git add <changed_files>
   # Or stage all changes:
   git add .
   ```
3. Commit changes:
   ```bash
   git commit -m "Description of changes"
   ```
4. Push to GitHub:
   ```bash
   git push origin main
   ```
   - Username: `dgableman`
   - Password: Your Personal Access Token
5. **Streamlit Cloud automatically redeploys** (takes 1-2 minutes)
6. Verify at your Streamlit Cloud URL

**Example:**
```bash
git add dashboard_app.py reports/crop_year_sales.py
git commit -m "Update chart colors and hover information"
git push origin main
```

### Workflow 2: Database Update

**When:** Database file has been updated from the main Bushel_Management project

**Steps:**
1. **Copy updated database with username prefix:**
   ```bash
   # From the main Bushel_Management project
   # Replace 'username' with the actual username
   cp /path/to/Bushel_Management/data/bushel_management.db \
      /path/to/Bushel_Management_Reports/data/{username}_bushel_management.db
   ```

2. **Verify database file exists:**
   ```bash
   ls -lh data/{username}_bushel_management.db
   ```

3. **Stage and commit:**
   ```bash
   git add data/{username}_bushel_management.db
   git commit -m "Update database for user: {username}"
   ```

4. **Push to GitHub:**
   ```bash
   git push origin main
   ```

5. **Streamlit Cloud will redeploy** with the new database

**⚠️ Note:** 
- Each user has their own database file: `{username}_bushel_management.db`
- If database file is large (>100MB), consider using Streamlit Secrets instead (see Option 2 below)
- Users enter their username on first load to access their specific database

### Workflow 3: Adding New Dependencies

**When:** Adding new Python packages

**Steps:**
1. Install package locally:
   ```bash
   pip install <package_name>
   ```

2. Update `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   # Or manually edit requirements.txt to add the package
   ```

3. Commit and push:
   ```bash
   git add requirements.txt
   git commit -m "Add new dependency: <package_name>"
   git push origin main
   ```

4. Streamlit Cloud will install the new dependency and redeploy

### Workflow 4: Database Schema Changes

**When:** Database structure changes (new tables, columns, etc.)

**Steps:**
1. **Update SQLAlchemy models** in `database/models.py`:
   - Add new model classes
   - Update existing models with new columns
   - Ensure models match actual database schema

2. **Test locally:**
   ```bash
   streamlit run dashboard_app.py
   ```
   Verify everything works with the updated schema

3. **Update database file** (see Workflow 2)

4. **Update code** that uses the new schema

5. **Commit all changes:**
   ```bash
   git add database/models.py dashboard_app.py reports/*.py data/bushel_management.db
   git commit -m "Update models for new database schema"
   git push origin main
   ```

### Workflow 5: Using Streamlit Secrets (Alternative Database Method)

**When:** Database file is too large for GitHub, or data is sensitive

**Steps:**
1. **Upload database to cloud storage:**
   - Google Drive (get shareable link)
   - Dropbox, AWS S3, etc.

2. **Configure Streamlit Secrets:**
   - In Streamlit Cloud: Go to app → Settings → Secrets
   - Add:
     ```toml
     DB_PATH = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"
     ```
   - Or for absolute path:
     ```toml
     DB_PATH = "/mount/src/bushel-management-dashboard/data/bushel_management.db"
     ```

3. **Code already supports secrets!**
   - `dashboard_app.py` automatically checks `st.secrets.get("DB_PATH")`
   - No code changes needed

4. **Update `.gitignore`:**
   - Remove database file from repository:
     ```bash
     git rm --cached data/bushel_management.db
     git commit -m "Remove database from repo, using Streamlit secrets"
     ```

---

## 📁 Repository Structure

```
bushel-management-dashboard/
├── dashboard_app.py              # Main Streamlit application ✅
├── requirements.txt              # Python dependencies ✅
├── .streamlit/
│   └── config.toml              # Streamlit configuration ✅
├── data/
│   └── bushel_management.db     # Database file ✅
├── database/
│   ├── __init__.py              ✅
│   ├── db_connection.py         ✅
│   └── models.py                ✅
└── reports/
    ├── __init__.py              ✅
    ├── contract_queries.py      ✅
    ├── settlement_queries.py    ✅
    ├── bin_queries.py           ✅
    ├── commodity_utils.py       ✅ (New)
    ├── crop_year_sales.py       ✅ (New)
    └── crop_year_utils.py       ✅ (New)
```

---

## 🔍 Verification & Troubleshooting

### Check Deployment Status

1. **GitHub Repository:**
   - Visit: https://github.com/dgableman/bushel-management-dashboard
   - Verify latest commit is pushed
   - Check that `data/bushel_management.db` exists

2. **Streamlit Cloud:**
   - Go to: https://share.streamlit.io/
   - Check app status (should show "Running")
   - View deployment logs if needed

3. **Dashboard:**
   - Open your Streamlit Cloud URL
   - Check sidebar "Settings" expander
   - Verify database path is correct
   - Check that data loads correctly

### Common Issues

#### Push Authentication Failed
- **Error:** `fatal: could not read Username`
- **Solution:** 
  - Username: `dgableman`
  - Password: Use Personal Access Token (not GitHub password)
  - Create token at: https://github.com/settings/tokens

#### Database Not Found
- **Check:** Dashboard sidebar → Settings → Verify database path
- **Verify:** Database exists in GitHub at `data/bushel_management.db`
- **Fix:** Update database (Workflow 2) or configure Streamlit Secrets

#### Deployment Fails
- **Check:** Streamlit Cloud deployment logs
- **Common causes:**
  - Missing dependencies in `requirements.txt`
  - Syntax errors in code
  - Import errors (missing `__init__.py` files)

#### Import Errors
- **Verify:** All `__init__.py` files exist in `database/` and `reports/` folders
- **Check:** `requirements.txt` includes all packages
- **Test:** Run locally first: `streamlit run dashboard_app.py`

---

## 📝 Quick Reference

### Git Commands

```bash
# Check status
git status

# Stage all changes
git add .

# Stage specific files
git add dashboard_app.py reports/new_file.py

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push origin main

# View commit history
git log --oneline

# Check remote
git remote -v
```

### Common Update Patterns

**Quick code fix:**
```bash
# Edit file, then:
git add dashboard_app.py
git commit -m "Fix bug in crop year calculation"
git push origin main
```

**Database update:**
```bash
cp ../Bushel_Management/data/bushel_management.db data/
git add data/bushel_management.db
git commit -m "Update database"
git push origin main
```

**Multiple file update:**
```bash
git add dashboard_app.py reports/*.py database/models.py
git commit -m "Add new feature and update models"
git push origin main
```

---

## 🎯 Summary

✅ **Setup is complete and working**  
✅ **Repository:** `dgableman/bushel-management-dashboard`  
✅ **Authentication:** Personal Access Token configured  
✅ **Database:** Included in repository at `data/bushel_management.db`  

**For future updates:**
- Code changes: Edit → Commit → Push → Auto-deploy
- Database updates: Copy → Commit → Push → Auto-deploy
- New dependencies: Update `requirements.txt` → Commit → Push → Auto-deploy

Streamlit Cloud automatically redeploys when you push to the `main` branch!
