# How to Get a GitHub Personal Access Token

## Quick Steps

### Step 1: Go to GitHub Settings

1. Log into GitHub: https://github.com
2. Click your profile picture (top right)
3. Click **"Settings"**

### Step 2: Create Personal Access Token

1. In the left sidebar, scroll down and click **"Developer settings"**
2. Click **"Personal access tokens"** ? **"Tokens (classic)"**
   - Or go directly: https://github.com/settings/tokens
3. Click **"Generate new token"** ? **"Generate new token (classic)"**

### Step 3: Configure Token

1. **Note:** Give it a name like "Streamlit Cloud Deployment" or "Bushel Management"
2. **Expiration:** Choose how long it lasts:
   - **30 days** (for testing)
   - **90 days** (recommended)
   - **No expiration** (for convenience, but less secure)
3. **Select scopes:** Check these boxes:
   - ? **`repo`** (Full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
   - ? **`workflow`** (if you use GitHub Actions)

### Step 4: Generate and Copy Token

1. Scroll down and click **"Generate token"**
2. **?? IMPORTANT:** Copy the token immediately!
   - It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - You won't be able to see it again!
   - If you lose it, you'll need to create a new one

### Step 5: Use Token for Git Push

When you run `git push`, it will ask for:
- **Username:** `dgableman` (your GitHub username)
- **Password:** Paste your token here (NOT your GitHub password!)

## Alternative: Use GitHub Desktop (Easier!)

If you prefer a GUI:

1. **Download GitHub Desktop:** https://desktop.github.com/
2. **Sign in** with your GitHub account
3. **Add your repository:**
   - File ? Add Local Repository
   - Select your `Bushel_Management_Reports` folder
4. **Commit and push** using the GUI buttons
   - No token needed - it handles authentication automatically!

## Alternative: Use SSH (Most Secure)

If you want to avoid tokens entirely:

### Step 1: Generate SSH Key

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept default location
# Optionally set a passphrase
```

### Step 2: Add SSH Key to GitHub

1. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. Go to GitHub: https://github.com/settings/keys
3. Click **"New SSH key"**
4. Paste your public key
5. Click **"Add SSH key"**

### Step 3: Change Remote URL to SSH

```bash
cd /path/to/Bushel_Management_Reports
git remote set-url origin git@github.com:dgableman/bushel-management-dashboard.git
```

Now `git push` will use SSH instead of HTTPS (no token needed).

## Quick Reference

**Token URL:** https://github.com/settings/tokens

**Token Format:** `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**When pushing:**
- Username: `dgableman`
- Password: `[paste your token]`

## Security Tips

- ? **Don't share your token** - treat it like a password
- ? **Use different tokens** for different purposes
- ? **Set expiration dates** - rotate tokens regularly
- ? **Revoke old tokens** if you suspect they're compromised
- ? **Use SSH** for long-term projects (more secure)

## Troubleshooting

### "Authentication failed"
- Make sure you're using the token, not your GitHub password
- Check the token hasn't expired
- Verify you selected the `repo` scope

### "Permission denied"
- Make sure the token has `repo` scope
- Check you're using the correct username (`dgableman`)

### "Token not found"
- Tokens are only shown once when created
- If you lost it, create a new one
