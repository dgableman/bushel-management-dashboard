# Streamlit Cloud Setup Guide

This guide will help you deploy your Bushel Management Dashboard to Streamlit Cloud for free!

## ?? Quick Setup (5 minutes)

### Step 1: Prepare Your Code

Your code is already ready! The following files are needed:
- ? `dashboard_app.py` - Main dashboard application
- ? `requirements.txt` - All dependencies (already updated)
- ? `database/` folder - Database connection files
- ? `reports/` folder - Query functions
- ? `.streamlit/config.toml` - Streamlit configuration (already created)

### Step 2: Push to GitHub

1. **Create a GitHub repository** (if you don't have one):
   - Go to https://github.com/new
   - Name it something like `bushel-management-dashboard`
   - Make it **Public** (required for free Streamlit Cloud)
   - Click "Create repository"

2. **Push your code to GitHub**:
   ```bash
   cd /path/to/Bushel_Management_Reports
   git init
   git add .
   git commit -m "Initial commit - Bushel Management Dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/bushel-management-dashboard.git
   git push -u origin main
   ```

   **Or use GitHub Desktop/GitHub web interface** to upload your files.

### Step 3: Deploy to Streamlit Cloud

1. **Sign up for Streamlit Cloud**:
   - Go to https://share.streamlit.io/
   - Click "Sign up" and connect your GitHub account
   - Authorize Streamlit Cloud to access your repositories

2. **Create a new app**:
   - Click "New app" button
   - Select your repository: `bushel-management-dashboard`
   - Select branch: `main`
   - Main file path: `dashboard_app.py`
   - Click "Deploy"

3. **Wait for deployment** (usually 1-2 minutes)

4. **Get your URL**:
   - Once deployed, you'll get a URL like: `https://bushel-management-dashboard.streamlit.app`
   - **Bookmark this URL!** This is your permanent dashboard link.

## ?? Database Setup Options

Your dashboard needs access to the database file. Here are your options:

### Option 1: Include Database in Repository (Easiest)

1. **Temporarily allow database files in git:**
   - Edit `.gitignore` and comment out or remove the `*.db` line
   - Or add an exception: `!data/bushel_management.db`

2. **Copy your database file:**
   ```bash
   # Create data folder if it doesn't exist
   mkdir -p data
   # Copy your database file
   cp /path/to/your/bushel_management.db data/bushel_management.db
   ```

3. **Commit and push:**
   ```bash
   git add data/bushel_management.db
   git commit -m "Add database file"
   git push
   ```

4. The dashboard will automatically find it at `data/bushel_management.db`

**⚠️ Important:** This makes your database public (since the repo is public). Only use this if your data is not sensitive or if you're okay with public data.

### Option 2: Use Streamlit Secrets (Recommended for Production)

1. In Streamlit Cloud, go to your app settings
2. Click "Secrets" tab
3. Add your database path or connection string:
   ```toml
   DB_PATH = "/path/to/your/database.db"
   ```
4. Update `dashboard_app.py` to read from secrets:
   ```python
   DB_PATH = st.secrets.get("DB_PATH", "data/bushel_management.db")
   ```

### Option 3: Host Database Separately

- Upload database to Google Drive and access via API
- Use a cloud database service (SQLite Cloud, etc.)
- Set DB_PATH via Streamlit secrets

## ? After Deployment

Once deployed, you can:
- ? Open your dashboard anytime at your Streamlit Cloud URL
- ? Share the URL with others (they can view your dashboard)
- ? Push code changes to GitHub ? Streamlit Cloud auto-updates
- ? No more clicking through Colab cells!

## ?? Updating Your Dashboard

1. Make changes to your code locally
2. Push to GitHub: `git push`
3. Streamlit Cloud automatically redeploys (usually takes 1-2 minutes)
4. Your dashboard updates automatically!

## ?? Troubleshooting

### App won't deploy
- Check that `requirements.txt` includes all dependencies
- Make sure `dashboard_app.py` is in the root of your repo
- Check the deployment logs in Streamlit Cloud

### Database not found
- Verify database file is in `data/` folder (if using Option 1)
- Check that DB_PATH is set correctly in secrets (if using Option 2)
- Check deployment logs for path errors

### Import errors
- Make sure `database/` and `reports/` folders are in your repo
- Verify all `__init__.py` files are present
- Check `requirements.txt` has all packages

## ?? Files Needed in GitHub Repo

```
bushel-management-dashboard/
??? dashboard_app.py          ? Main app (required)
??? requirements.txt          ? Dependencies (required)
??? .streamlit/
?   ??? config.toml          ? Streamlit config (optional but recommended)
??? data/
?   ??? bushel_management.db ? Database file (if using Option 1)
??? database/
?   ??? __init__.py
?   ??? db_connection.py
?   ??? models.py
??? reports/
    ??? __init__.py
    ??? contract_queries.py
    ??? settlement_queries.py
    ??? bin_queries.py
```

## ?? That's It!

Once set up, you'll have a permanent URL that you can bookmark and open anytime. No more Colab cells, no more ngrok, just a simple URL!
