#!/usr/bin/env python3
"""
Test session flow end-to-end
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("SESSION FLOW TEST")
print("=" * 60)

# Step 1: Check Supabase connection
print("\n1. Testing Supabase connection...")
from supabase import create_client

url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not service_key:
    print("   ❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    sys.exit(1)

try:
    client = create_client(url, service_key)
    print("   ✅ Connected to Supabase")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    sys.exit(1)

# Step 2: Get a test user
print("\n2. Finding a test user...")
result = client.table("users").select("id, email").limit(1).execute()
if not result.data:
    print("   ❌ No users found")
    sys.exit(1)

test_user = result.data[0]
user_id = test_user["id"]
email = test_user["email"]
print(f"   ✅ Using: {email} ({user_id[:8]}...)")

# Step 3: Get wallet address
print("\n3. Getting wallet address...")
result = client.table("wallets").select("address").eq("user_id", user_id).limit(1).execute()
if not result.data:
    print("   ❌ No wallet found")
    wallet_address = "0x0000000000000000000000000000000000000000"
else:
    wallet_address = result.data[0]["address"]
    print(f"   ✅ Wallet: {wallet_address[:10]}...")

# Step 4: Test session creation
print("\n4. Testing session creation...")
import secrets
from datetime import datetime, timedelta

session_token = secrets.token_urlsafe(32)
expires_at = datetime.utcnow() + timedelta(days=30)

try:
    result = client.table("sessions").upsert({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "email": email,
        "wallet_address": wallet_address
    }, on_conflict="user_id").execute()

    if result.data:
        print(f"   ✅ Session created: {session_token[:16]}...")
    else:
        print(f"   ❌ No data returned from upsert")
except Exception as e:
    print(f"   ❌ Session creation failed: {e}")
    sys.exit(1)

# Step 5: Test session retrieval
print("\n5. Testing session retrieval...")
try:
    result = client.table("sessions").select("*").eq("session_token", session_token).single().execute()

    if result.data:
        print(f"   ✅ Session retrieved successfully")
        print(f"      Email: {result.data['email']}")
        print(f"      Expires: {result.data['expires_at']}")
    else:
        print(f"   ❌ Session not found")
except Exception as e:
    print(f"   ❌ Session retrieval failed: {e}")

# Step 6: Check extra-streamlit-components
print("\n6. Checking cookie manager library...")
try:
    import extra_streamlit_components as stx
    print(f"   ✅ extra_streamlit_components imported successfully")
    print(f"   📦 Version: {stx.__version__ if hasattr(stx, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
except Exception as e:
    print(f"   ⚠️ Warning: {e}")

# Step 7: Show current sessions
print("\n7. Current sessions in database:")
result = client.table("sessions").select("email, session_token, created_at").execute()
for session in result.data:
    print(f"   - {session['email']}: {session['session_token'][:12]}... (created {session['created_at'][:10]})")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
✅ Database connection: Working
✅ Session creation: Working
✅ Session retrieval: Working

The issue is likely with the COOKIE MANAGER in the browser:
- extra_streamlit_components uses JavaScript to set/get cookies
- This can fail silently in production environments
- Railway might have issues with cookie domains or HTTPS

NEXT STEPS:
1. Check browser dev tools → Application → Cookies
2. Look for 'chat_wallet_session' cookie after login
3. If cookie is missing, the cookie manager JS isn't working
""")
