#!/usr/bin/env python3
"""
Quick diagnostic script to check Supabase sessions table
Run with: python debug_sessions.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Get credentials
url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"Supabase URL: {url}")
print(f"Service Key: {'SET' if service_key else 'MISSING'}")

if not url or not service_key:
    print("\n❌ Missing credentials in .env file")
    exit(1)

try:
    from supabase import create_client

    client = create_client(url, service_key)
    print("\n✅ Connected to Supabase successfully\n")

    # Check sessions table
    print("=" * 50)
    print("SESSIONS TABLE")
    print("=" * 50)

    result = client.table("sessions").select("*").execute()

    if result.data:
        print(f"Found {len(result.data)} session(s):\n")
        for session in result.data:
            print(f"  User ID: {session.get('user_id', 'N/A')[:20]}...")
            print(f"  Email: {session.get('email', 'N/A')}")
            print(f"  Token: {session.get('session_token', 'N/A')[:20]}...")
            print(f"  Created: {session.get('created_at', 'N/A')}")
            print(f"  Expires: {session.get('expires_at', 'N/A')}")
            print()
    else:
        print("❌ No sessions found in database")
        print("   This means session creation is failing during login")

    # Check users table
    print("=" * 50)
    print("USERS TABLE")
    print("=" * 50)

    result = client.table("users").select("id, email, created_at").limit(5).execute()

    if result.data:
        print(f"Found {len(result.data)} user(s):\n")
        for user in result.data:
            print(f"  ID: {user.get('id', 'N/A')[:20]}...")
            print(f"  Email: {user.get('email', 'N/A')}")
            print(f"  Created: {user.get('created_at', 'N/A')}")
            print()
    else:
        print("No users found")

    # Check wallets table
    print("=" * 50)
    print("WALLETS TABLE")
    print("=" * 50)

    result = client.table("wallets").select("user_id, address, chain, created_at").limit(5).execute()

    if result.data:
        print(f"Found {len(result.data)} wallet(s):\n")
        for wallet in result.data:
            print(f"  User ID: {wallet.get('user_id', 'N/A')[:20]}...")
            print(f"  Address: {wallet.get('address', 'N/A')[:20]}...")
            print(f"  Chain: {wallet.get('chain', 'N/A')}")
            print()
    else:
        print("No wallets found")

except ImportError:
    print("\n❌ Supabase library not installed. Run: pip install supabase")
except Exception as e:
    print(f"\n❌ Error: {e}")
