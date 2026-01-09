#!/bin/bash
# Helper script to add a username-specific database to the repository

if [ -z "$1" ]; then
    echo "Usage: ./add_user_database.sh <username>"
    echo "Example: ./add_user_database.sh dgableman"
    exit 1
fi

USERNAME=$1
SOURCE_DB="$HOME/PycharmProjects/Bushel_Management/data/bushel_management.db"
TARGET_DB="data/${USERNAME}_bushel_management.db"

if [ ! -f "$SOURCE_DB" ]; then
    echo "Error: Source database not found at: $SOURCE_DB"
    exit 1
fi

echo "Copying database for user: $USERNAME"
cp "$SOURCE_DB" "$TARGET_DB"

if [ -f "$TARGET_DB" ]; then
    echo "✅ Created: $TARGET_DB"
    echo ""
    echo "To add to git and push:"
    echo "  git add $TARGET_DB"
    echo "  git commit -m \"Add database for user: $USERNAME\""
    echo "  git push origin main"
else
    echo "❌ Failed to create database file"
    exit 1
fi
