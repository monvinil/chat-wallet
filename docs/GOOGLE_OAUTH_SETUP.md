# Google OAuth Setup Guide

This guide walks you through setting up "Sign in with Google" for Chat Wallet. Once configured, users can sign in with one click and use AI chat for free (using their own Google Gemini quota).

**Time required:** ~10 minutes

---

## Step 1: Create Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown at the top
3. Click **New Project**
4. Name: `Chat Wallet` (or any name)
5. Click **Create**
6. Wait for creation, then select it from the dropdown

---

## Step 2: Enable the Generative Language API

1. In the search bar at the top, type `Generative Language API`
2. Click on **Generative Language API** in the results
3. Click **Enable**
4. Wait for it to enable (~10 seconds)

**Note:** If you can't find it via search, go to **APIs & Services** > **Library** and search there.

---

## Step 3: Configure OAuth Consent Screen

### Navigate to Google Auth Platform

1. Click the hamburger menu (☰) in the top left
2. Go to **Google Auth platform** > **Overview**
   - If you see "APIs & Services" instead, look for "Google Auth platform" in the menu
   - Or go directly to: `console.cloud.google.com/auth/overview`

### Configure Your App

3. Click **Get Started** or **Configure**
4. Fill in the form:
   - **App name:** `Chat Wallet`
   - **User support email:** Select your email
   - **Audience:** Select **External**
5. Click **Next** or **Save and Continue**

### Add Scopes

6. Click **Add or remove scopes** (or **Add scopes**)
7. In the search/filter box, search for each of these and check them:
   - `generative-language.retriever` - for Gemini API access
   - `userinfo.email` - for getting user's email
8. Click **Update** or **Add**
9. Click **Save and Continue**

### Add Test Users

10. Click **Add users**
11. Enter your email address
12. Click **Add** then **Save and Continue**

---

## Step 4: Create OAuth Credentials

### Navigate to Clients

1. Go to **Google Auth platform** > **Clients**
   - Or: `console.cloud.google.com/auth/clients`

### Create Web Application Client

2. Click **+ Create Client**
3. Select **Web application** as the application type
4. Name: `Chat Wallet Web`

### Add Authorized Redirect URIs

5. Under **Authorized redirect URIs**, click **+ Add URI**
6. Add your redirect URIs:

**For local development:**
```
http://localhost:8501/oauth/callback
```

**For production (Railway):**
```
https://YOUR-APP-NAME.up.railway.app/oauth/callback
```

Replace `YOUR-APP-NAME` with your actual Railway app name. You can find this in your Railway dashboard.

**Important:**
- `http://` is only allowed for `localhost`
- Production URLs must use `https://`
- URIs must match **exactly** (no trailing slash differences)

7. Click **Create**

---

## Step 5: Copy Your Credentials

After clicking Create, you'll see:

- **Client ID:** Something like `123456789-abc123.apps.googleusercontent.com`
- **Client Secret:** Something like `GOCSPX-abc123xyz...`

**Copy both values immediately** - the secret is only shown once at creation time.

If you need to see them again:
1. Go to **Google Auth platform** > **Clients**
2. Click on your client name
3. Client ID is always visible; for a new secret, you must create a new one

---

## Step 6: Add to Environment Variables

### For Local Development

Edit your `.env` file:

```env
GOOGLE_OAUTH_CLIENT_ID=123456789-abc123.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-abc123xyz...
APP_URL=http://localhost:8501
```

### For Railway (Production)

1. Go to [railway.app](https://railway.app) and open your project
2. Click on your service
3. Go to **Variables** tab
4. Add these variables:

| Variable | Value |
|----------|-------|
| `GOOGLE_OAUTH_CLIENT_ID` | Your Client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Your Client Secret |
| `APP_URL` | `https://YOUR-APP-NAME.up.railway.app` |

5. Railway will auto-redeploy

---

## Step 7: Test It

1. Start your app: `streamlit run app.py`
2. Create an account or log in
3. You should see **"Sign in with Google"** button
4. Click it and follow the authorization link
5. Select your Google account
6. Grant permissions
7. You'll be redirected back and connected

---

## Troubleshooting

### "redirect_uri_mismatch" error

The redirect URI in your request doesn't match what's configured in Google Cloud. Check:
- The URI must be **exactly** `http://localhost:8501/oauth/callback` (no trailing slash)
- For production: `https://YOUR-APP.up.railway.app/oauth/callback`
- Case sensitive - must match exactly

### "Access blocked: This app's request is invalid"

- Verify you enabled the **Generative Language API** (Step 2)
- Check that you added the correct scopes (Step 3)
- Make sure your email is added as a test user

### "This app isn't verified"

Normal for apps in testing mode:
1. Click **Advanced**
2. Click **Go to Chat Wallet (unsafe)**
3. Continue with authorization

To remove this warning, you'd need to submit for Google verification (only needed for production with many users).

### "Sign in with Google" button doesn't appear

- Check that `GOOGLE_OAUTH_CLIENT_ID` is set in your environment
- Restart your Streamlit app after changing `.env`

### Changes not taking effect

Google OAuth changes can take 5 minutes to a few hours to propagate. Wait and try again.

---

## How It Works

1. User clicks "Sign in with Google"
2. Redirects to Google consent screen
3. User grants permission to use Gemini API
4. Google sends auth code back to your app
5. App exchanges code for access/refresh tokens
6. Tokens stored encrypted in database
7. App uses tokens to call Gemini API on user's behalf
8. User's own free Gemini quota is used (~1500 requests/day)

**Result:** Zero cost to you, unlimited users.

---

## Security Notes

- Never commit Client ID/Secret to Git
- Tokens are encrypted with AES-256 in the database
- Refresh tokens allow long-term access
- Users can revoke access anytime at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

---

## Finding Your Railway URL

If you don't know your Railway deployment URL:

1. Go to [railway.app](https://railway.app)
2. Open your project
3. Click on your service
4. Look at the **Deployments** tab - your URL is shown there
5. Or click **Settings** > **Networking** to see/configure your domain

Typical format: `https://your-project-name-production.up.railway.app`

---

## Sources

- [Google OAuth Quickstart for Gemini API](https://ai.google.dev/gemini-api/docs/oauth)
- [OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Manage OAuth Clients - Google Cloud Console Help](https://support.google.com/cloud/answer/15549257)
