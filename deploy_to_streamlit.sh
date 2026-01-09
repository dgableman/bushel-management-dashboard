#!/bin/bash
# Deployment script to push all code changes to Streamlit Cloud
# This script stages, commits, and pushes changes to GitHub
# Streamlit Cloud automatically redeploys when changes are pushed

set -e  # Exit on error

echo "🚀 Deploying to Streamlit Cloud..."
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if there are any changes
if git diff --quiet && git diff --cached --quiet; then
    echo "ℹ️  No changes to commit"
    echo "   Checking if there are unpushed commits..."
    
    if git log origin/main..HEAD --oneline | grep -q .; then
        echo "   Found unpushed commits, pushing..."
        git push origin main
        echo ""
        echo "✅ Pushed to GitHub"
        echo "   Streamlit Cloud will auto-deploy in 1-2 minutes"
    else
        echo "   Everything is up to date!"
    fi
    exit 0
fi

# Show current status
echo "📋 Current changes:"
git status --short
echo ""

# Prompt for commit message
if [ -z "$1" ]; then
    echo "💬 Enter commit message (or press Enter to use default):"
    read -r commit_message
    if [ -z "$commit_message" ]; then
        commit_message="Update dashboard - $(date +'%Y-%m-%d %H:%M:%S')"
    fi
else
    commit_message="$1"
fi

# Stage all changes
echo ""
echo "📦 Staging all changes..."
git add .

# Show what will be committed
echo ""
echo "📝 Files to be committed:"
git status --short
echo ""

# Confirm before committing
echo "❓ Commit message: $commit_message"
echo "   Proceed with commit and push? (y/n)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# Commit
echo ""
echo "💾 Committing changes..."
git commit -m "$commit_message"

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo ""
echo "⏳ Streamlit Cloud will automatically redeploy in 1-2 minutes"
echo "   Check status at: https://share.streamlit.io/"
echo ""
