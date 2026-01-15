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

from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
from utils.logger import logger


def _safe_error(operation: str, e: Exception) -> None:
    """Show generic error to user, log details server-side"""
    logger.error(f"{operation}: {str(e)}")
    st.error(f"Unable to {operation.lower()}. Please try again.")


@st.cache_resource
def _get_cached_supabase_client(use_service_key: bool = False) -> Optional[Client]:
    """
    Cached Supabase client instance (created once per session type)
    Internal function - use get_supabase_client() instead
    """
    if not SUPABASE_AVAILABLE or not SUPABASE_URL:
        return None

    key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_ANON_KEY
    if not key:
        return None

    try:
        return create_client(SUPABASE_URL, key)
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return None


def get_supabase_client(use_service_key: bool = False) -> Optional[Client]:
    """
    Get Supabase client instance (with caching for performance)

    Args:
        use_service_key: If True, uses service role key (bypasses RLS, for admin operations)
                        If False, uses anon key (respects RLS, for user operations)
    """
    if not SUPABASE_AVAILABLE:
        st.error("⚠️ Supabase library not installed. Run: pip install supabase")
        return None

    if not SUPABASE_URL:
        st.error("⚠️ SUPABASE_URL environment variable missing.")
        return None

    if use_service_key and not SUPABASE_SERVICE_KEY:
        st.error("⚠️ SUPABASE_SERVICE_KEY environment variable missing.")
        return None

    if not use_service_key and not SUPABASE_ANON_KEY:
        st.error("⚠️ SUPABASE_ANON_KEY environment variable missing.")
        return None

    # Use cached client (50-100ms faster on subsequent calls)
    return _get_cached_supabase_client(use_service_key)


def create_user(email: str, primary_wallet_address: str = None, auth_provider: str = "email", password_hash: str = None) -> Optional[Dict[str, Any]]:
    """Create a new user in the database with password hash for verification"""
    try:
        # Use service key for admin operation (bypasses RLS)
        client = get_supabase_client(use_service_key=True)
        if not client:
            return None

        # Build data dict with required fields
        data = {
            "email": email,
            "auth_provider": auth_provider,
            "created_at": datetime.utcnow().isoformat()
        }

        # Add optional fields if column exists
        if primary_wallet_address:
            data["primary_wallet_address"] = primary_wallet_address
        if password_hash:
            data["password_hash"] = password_hash

        try:
            result = client.table("users").insert(data).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            error_str = str(e)
            # If error due to missing columns, try with minimal fields
            if "primary_wallet_address" in error_str or "password_hash" in error_str:
                st.warning("⚠️ Database needs migration for new columns.")
                data_minimal = {
                    "email": email,
                    "auth_provider": auth_provider,
                    "created_at": datetime.utcnow().isoformat()
                }
                result = client.table("users").insert(data_minimal).execute()
                if result.data:
                    return result.data[0]
            else:
                raise e

        return None
    except Exception as e:
        _safe_error("Create account", e)
        return None


def update_user_password_hash(user_id: str, password_hash: str) -> bool:
    """Update user's password hash"""
    try:
        client = get_supabase_client(use_service_key=True)
        if not client:
            return False

        client.table("users").update({
            "password_hash": password_hash,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        # Column might not exist yet - log but don't show error
        logger.error(f"Update password hash: {e}")
        return False


def get_user_password_hash(user_id: str) -> Optional[str]:
    """Get user's password hash for verification"""
    try:
        client = get_supabase_client(use_service_key=True)
        if not client:
            return None

        result = client.table("users").select("password_hash").eq("id", user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("password_hash")
        return None
    except Exception as e:
        # Column might not exist yet - silently return None
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    try:
        # Use service key to bypass RLS (needed for login check)
        client = get_supabase_client(use_service_key=True)
        if not client:
            return None

        result = client.table("users").select("*").eq("email", email).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        _safe_error("Find account", e)
        return None


def save_wallet_address(user_id: str, address: str, chain: str = "evm",
                        encrypted_wallet_data: str = None, encryption_salt: str = None) -> bool:
    """Save a wallet address for a user with optional encrypted backup"""
    try:
        # Use service key for admin operation (bypasses RLS)
        client = get_supabase_client(use_service_key=True)
        if not client:
            return False

        data = {
            "user_id": user_id,
            "chain": chain,
            "address": address,
            "created_at": datetime.utcnow().isoformat()
        }

        # Store encrypted wallet data for cloud backup
        if encrypted_wallet_data:
            data["wallet_data_encrypted"] = encrypted_wallet_data
        if encryption_salt:
            data["encryption_salt"] = encryption_salt

        # Use upsert to handle existing wallet records (e.g., from guest mode)
        # This will update the encrypted data if wallet already exists
        client.table("wallets").upsert(data, on_conflict="user_id,chain").execute()
        return True
    except Exception as e:
        # Check if columns don't exist yet
        error_str = str(e)
        if "wallet_data_encrypted" in error_str or "encryption_salt" in error_str:
            # Try without encrypted data columns (need migration)
            st.warning("⚠️ Database needs migration for encrypted wallet backup. Run supabase_migration_wallet_backup.sql")
            data_minimal = {
                "user_id": user_id,
                "chain": chain,
                "address": address,
                "created_at": datetime.utcnow().isoformat()
            }
            try:
                client.table("wallets").upsert(data_minimal, on_conflict="user_id,chain").execute()
                return True
            except Exception as e2:
                _safe_error("Save wallet", e2)
                return False
        _safe_error("Save wallet", e)
        return False


def get_encrypted_wallet(user_id: str, chain: str = "evm") -> Optional[Dict[str, Any]]:
    """Get encrypted wallet data for a user (for cloud backup restoration)"""
    try:
        client = get_supabase_client(use_service_key=True)
        if not client:
            return None

        result = client.table("wallets").select(
            "address, wallet_data_encrypted, encryption_salt"
        ).eq("user_id", user_id).eq("chain", chain).execute()

        if result.data and len(result.data) > 0:
            wallet = result.data[0]
            # Only return if we have encrypted data
            if wallet.get("wallet_data_encrypted") and wallet.get("encryption_salt"):
                return {
                    "address": wallet["address"],
                    "encrypted_data": wallet["wallet_data_encrypted"],
                    "salt": wallet["encryption_salt"]
                }
        return None
    except Exception as e:
        # Columns might not exist - return None silently
        return None


def get_user_wallets(user_id: str) -> list:
    """Get all wallet addresses for a user"""
    try:
        client = get_supabase_client(use_service_key=True)
        if not client:
            return []

        result = client.table("wallets").select("*").eq("user_id", user_id).execute()
        wallets = result.data if result.data else []

        # Normalize field names for consistency
        for wallet in wallets:
            if "address" in wallet and "wallet_address" not in wallet:
                wallet["wallet_address"] = wallet["address"]

        return wallets
    except Exception as e:
        _safe_error("Load wallets", e)
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
        logger.error(f"Log transaction: {e}")
        return False


def get_user_transactions(client: Client, user_id: str, limit: int = 50) -> list:
    """Get transaction history for a user"""
    try:
        result = client.table("transactions").select("*").eq("user_id", user_id)\
            .order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Fetch transactions: {e}")
        return []
