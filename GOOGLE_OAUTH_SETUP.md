# Google OAuth Setup Guide

This guide walks you through setting up Google OAuth for Gmail integration.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it "Chat Wallet" or similar
4. Click "Create"

## Step 2: Enable Gmail API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Gmail API"
3. Click on it and click **"Enable"**
4. Also enable "Google+ API" (for user info)

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **"External"** (unless you have Google Workspace)
3. Click **"Create"**

Fill in the required fields:
- **App name**: Chat Wallet
- **User support email**: Your email
- **Developer contact email**: Your email

4. Click **"Save and Continue"**

### Add Scopes:
5. Click **"Add or Remove Scopes"**
6. Add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` (Read Gmail)
   - `https://www.googleapis.com/auth/userinfo.email` (Get user email)
7. Click **"Update"** → **"Save and Continue"**

### Add Test Users (if in Testing mode):
8. Click **"Add Users"**
9. Add email addresses that can test the app
10. Click **"Save and Continue"**

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. Choose **"Web application"**
4. Name it "Chat Wallet Web Client"

### Authorized redirect URIs:
Add these redirect URIs:
- `http://localhost:8501/oauth/callback` (for local dev)
- `https://your-app.railway.app/oauth/callback` (for production)

Replace `your-app.railway.app` with your actual Railway domain.

5. Click **"Create"**

## Step 5: Get Credentials

After creating, you'll see:
- **Client ID** (looks like: `123456789-abcdef.apps.googleusercontent.com`)
- **Client Secret** (looks like: `GOCSPX-abc123...`)

**Copy both values** - you'll need them next.

## Step 6: Add to Railway Environment Variables

1. Go to your Railway project
2. Click on your service
3. Go to **Variables** tab
4. Add these two new variables:

```
GOOGLE_OAUTH_CLIENT_ID=<your-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>
APP_URL=https://your-app.railway.app
```

Replace the values with your actual credentials and Railway URL.

5. Click **Deploy** to restart with new variables

## Step 7: Test OAuth Flow

1. Go to your deployed app
2. Log in to your wallet
3. Go to **Settings** → **Connected Accounts** tab
4. Click **"Connect Gmail"**
5. Click the authorization link
6. Select your Google account
7. Grant permissions
8. You'll be redirected back to your app

## Troubleshooting

### "redirect_uri_mismatch" error
- Make sure the redirect URI in Google Cloud Console exactly matches your app URL
- Check for trailing slashes - should be `/oauth/callback` (no trailing slash)

### "Access blocked: This app's request is invalid"
- Make sure you've added the required scopes in OAuth consent screen
- Verify Gmail API is enabled

### "This app isn't verified"
- This is normal for apps in testing mode
- Click "Advanced" → "Go to Chat Wallet (unsafe)" to proceed
- Once you're ready for production, submit the app for verification

### Tokens not saving
- Check that `SETTINGS_ENCRYPTION_KEY` is set in Railway
- Check Supabase migrations have been run (user_oauth_connections table exists)

## Security Notes

- **Never commit** your Client ID or Client Secret to Git
- Keep them in Railway environment variables only
- Tokens are encrypted in the database using AES-256
- Refresh tokens allow long-term access - revoke in Google account settings if needed

## What Can the AI Do With Gmail Access?

With Gmail access, your AI wallet can:
- Read verification codes from emails (for phone number verification, 2FA, etc.)
- Find receipts and invoices
- Monitor for important notifications
- Parse order confirmations

The AI **cannot**:
- Send emails (we only request read access)
- Delete emails
- Modify your Gmail settings
- Access emails outside your granted scopes
