# Git Setup - Step by Step

## Fix the "main" branch error

This error happens when you haven't made any commits yet. Here's the correct sequence:

### Option 1: If you haven't initialized git yet

```bash
cd /path/to/Bushel_Management_Reports

# Initialize git
git init

# Add all files
git add .

# Make your first commit (this creates the branch)
git commit -m "Initial commit - Bushel Management Dashboard"

# Check what branch you're on (might be 'master' or 'main')
git branch

# If it says 'master', rename it to 'main'
git branch -M main

# Add your GitHub repository
git remote add origin https://github.com/dgableman/bushel-management-dashboard.git

# Now push (this should work)
git push -u origin main
```

### Option 2: If git is already initialized

```bash
cd /path/to/Bushel_Management_Reports

# Check if you have any commits
git log

# If no commits, make one:
git add .
git commit -m "Initial commit - Bushel Management Dashboard"

# Check your branch name
git branch

# If it says 'master', rename to 'main':
git branch -M main

# Add remote (if not already added)
git remote add origin https://github.com/Dave/bushel-management-dashboard.git

# Or if remote already exists, update it:
git remote set-url origin https://github.com/Dave/bushel-management-dashboard.git

# Push
git push -u origin main
```

### Option 3: If your branch is already called 'master'

```bash
# Just push to master instead
git push -u origin master
```

Then in Streamlit Cloud, select branch `master` instead of `main`.

## Common Issues

### "Repository not found"
- Make sure the repository exists on GitHub
- Check the URL is correct: `https://github.com/dgableman/bushel-management-dashboard.git`
- Make sure you're logged into GitHub

### "Permission denied"
- You may need to authenticate with GitHub
- Use GitHub Desktop, or set up SSH keys, or use a personal access token

### "Nothing to commit"
- Make sure you're in the right directory
- Check that files exist: `ls -la`
- Make sure files aren't all in `.gitignore`
