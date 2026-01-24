# Project Info

Quick reference for essential project details.

## Deployment

| Item | Value |
|------|-------|
| GitHub Repo | `monvinil/chat-wallet` |
| Railway URL | `TODO: add your Railway URL here` |
| Supabase Project | `cxvywtrtxclwaobwnmwr.supabase.co` |

## OAuth Redirect URIs

For Google Cloud Console:
- Local: `http://localhost:8501/oauth/callback`
- Production: `https://YOUR-RAILWAY-URL/oauth/callback`

## Environment Variables

### Required for Google OAuth
```
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
APP_URL=https://YOUR-RAILWAY-URL
```

### Supabase (configured)
```
SUPABASE_URL=https://cxvywtrtxclwaobwnmwr.supabase.co
SUPABASE_ANON_KEY=configured
SUPABASE_SERVICE_KEY=configured
```

## Notes

- App auto-deploys from GitHub to Railway on push
- OAuth callback uses `APP_URL` env var to build redirect URI
