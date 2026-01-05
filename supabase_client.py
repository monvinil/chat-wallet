"""
Supabase client and database operations
"""

import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from config import SUPABASE_URL, SUPABASE_ANON_KEY


def get_supabase_client() -> Optional[Client]:
    """Get Supabase client instance"""
    if not SUPABASE_AVAILABLE:
        st.error("⚠️ Supabase library not installed. Run: pip install supabase")
        return None

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        st.error("⚠️ Supabase credentials missing. Check SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
        return None

    try:
        return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        st.error(f"Supabase connection failed: {e}")
        return None


def create_user(email: str, primary_wallet_address: str = None, auth_provider: str = "email") -> Optional[Dict[str, Any]]:
    """Create a new user in the database"""
    try:
        client = get_supabase_client()
        if not client:
            return None

        # Try with primary_wallet_address first (if migration run)
        data = {
            "email": email,
            "auth_provider": auth_provider,
            "created_at": datetime.utcnow().isoformat()
        }

        # Only add primary_wallet_address if column exists
        if primary_wallet_address:
            data["primary_wallet_address"] = primary_wallet_address

        try:
            result = client.table("users").insert(data).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            # If error due to missing column, try without it
            if "primary_wallet_address" in str(e):
                st.warning("⚠️ Database needs migration. Creating user without primary_wallet_address field.")
                data_without = {
                    "email": email,
                    "auth_provider": auth_provider,
                    "created_at": datetime.utcnow().isoformat()
                }
                result = client.table("users").insert(data_without).execute()
                if result.data:
                    return result.data[0]
            else:
                raise e

        return None
    except Exception as e:
        st.error(f"Failed to create user: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    try:
        client = get_supabase_client()
        if not client:
            return None

        result = client.table("users").select("*").eq("email", email).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Failed to fetch user: {e}")
        return None


def save_wallet_address(user_id: str, address: str, chain: str = "evm", encrypted_wallet_data: str = None) -> bool:
    """Save a wallet address for a user with optional encrypted backup"""
    try:
        client = get_supabase_client()
        if not client:
            return False

        data = {
            "user_id": user_id,
            "chain": chain,
            "address": address,
            "created_at": datetime.utcnow().isoformat()
        }

        if encrypted_wallet_data:
            data["wallet_data_encrypted"] = encrypted_wallet_data

        client.table("wallets").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save wallet address: {e}")
        return False


def get_user_wallets(user_id: str) -> list:
    """Get all wallet addresses for a user"""
    try:
        client = get_supabase_client()
        if not client:
            return []

        result = client.table("wallets").select("*").eq("user_id", user_id).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Failed to fetch wallets: {e}")
        return []


def log_transaction(client: Client, user_id: str, wallet_id: str, tx_hash: str,
                    chain: str, tx_type: str, amount: float, currency: str,
                    fee: float = 0.0, status: str = "pending") -> bool:
    """Log a transaction"""
    try:
        client.table("transactions").insert({
            "user_id": user_id,
            "wallet_id": wallet_id,
            "tx_hash": tx_hash,
            "chain": chain,
            "type": tx_type,
            "amount": amount,
            "currency": currency,
            "fee_charged": fee,
            "status": status,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        return True
    except Exception as e:
        st.error(f"Failed to log transaction: {e}")
        return False


def get_user_transactions(client: Client, user_id: str, limit: int = 50) -> list:
    """Get transaction history for a user"""
    try:
        result = client.table("transactions").select("*").eq("user_id", user_id)\
            .order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Failed to fetch transactions: {e}")
        return []
