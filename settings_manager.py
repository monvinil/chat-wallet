"""
Settings Manager - Handle user settings, LLM config, and OAuth connections
"""

import os
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from supabase_client import get_supabase_client
import streamlit as st


class SettingsManager:
    """Manage user settings and encrypted credentials"""

    # Encryption key - MUST be set in environment for production
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    _ENCRYPTION_KEY = None
    _encryption_warning_shown = False

    @classmethod
    def _get_encryption_key(cls) -> bytes:
        """Get encryption key from environment (required for production)"""
        if cls._ENCRYPTION_KEY is None:
            key_str = os.getenv("SETTINGS_ENCRYPTION_KEY")
            if key_str:
                cls._ENCRYPTION_KEY = key_str.encode() if isinstance(key_str, str) else key_str
            else:
                # Development fallback - warn but don't crash
                if not cls._encryption_warning_shown:
                    st.warning("⚠️ SETTINGS_ENCRYPTION_KEY not set. Using temporary key - encrypted data will be lost on restart!")
                    cls._encryption_warning_shown = True
                # Generate a session-stable key using a fixed seed for development
                cls._ENCRYPTION_KEY = Fernet.generate_key()
        return cls._ENCRYPTION_KEY

    @staticmethod
    def _get_cipher():
        """Get Fernet cipher for encryption/decryption"""
        return Fernet(SettingsManager._get_encryption_key())

    @staticmethod
    def _encrypt(data: str) -> str:
        """Encrypt sensitive data"""
        cipher = SettingsManager._get_cipher()
        return cipher.encrypt(data.encode()).decode()

    @staticmethod
    def _decrypt(encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            cipher = SettingsManager._get_cipher()
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return None

    @staticmethod
    def get_user_settings(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user settings from database"""
        try:
            supabase = get_supabase_client()
            result = supabase.table("user_settings").select("*").eq("user_id", user_id).execute()

            if result.data and len(result.data) > 0:
                settings = result.data[0]

                # Decrypt API key if present
                if settings.get("llm_api_key_encrypted"):
                    settings["llm_api_key"] = SettingsManager._decrypt(
                        settings["llm_api_key_encrypted"]
                    )

                return settings
            return None
        except Exception as e:
            st.error(f"Error fetching settings: {e}")
            return None

    @staticmethod
    def save_user_settings(
        user_id: str,
        llm_provider: str = "anthropic",
        llm_model: str = "claude-sonnet-4-20250514",
        llm_api_key: Optional[str] = None,
        daily_spend_limit: float = 100.00,
        require_approval_above: float = 50.00,
        allow_recurring_payments: bool = False,
        allow_account_access: bool = False
    ) -> bool:
        """Save or update user settings"""
        try:
            supabase = get_supabase_client()

            # Encrypt API key if provided
            encrypted_key = None
            if llm_api_key:
                encrypted_key = SettingsManager._encrypt(llm_api_key)

            data = {
                "user_id": user_id,
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                "llm_api_key_encrypted": encrypted_key,
                "daily_spend_limit": daily_spend_limit,
                "require_approval_above": require_approval_above,
                "allow_recurring_payments": allow_recurring_payments,
                "allow_account_access": allow_account_access
            }

            # Try to update first, insert if doesn't exist
            result = supabase.table("user_settings").upsert(data).execute()

            return True
        except Exception as e:
            st.error(f"Error saving settings: {e}")
            return False

    @staticmethod
    def get_llm_config(user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get LLM configuration for user
        Falls back to default if user hasn't configured custom LLM
        """
        default_config = {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "using_default": True
        }

        if not user_id:
            return default_config

        settings = SettingsManager.get_user_settings(user_id)
        if not settings or not settings.get("llm_api_key"):
            return default_config

        return {
            "provider": settings.get("llm_provider", "anthropic"),
            "model": settings.get("llm_model", "claude-sonnet-4-20250514"),
            "api_key": settings.get("llm_api_key"),
            "using_default": False
        }

    @staticmethod
    def save_oauth_connection(
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        provider_user_id: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        expires_at: Optional[str] = None
    ) -> bool:
        """Save OAuth connection tokens (encrypted)"""
        try:
            supabase = get_supabase_client()

            data = {
                "user_id": user_id,
                "provider": provider,
                "provider_user_id": provider_user_id,
                "access_token_encrypted": SettingsManager._encrypt(access_token),
                "refresh_token_encrypted": SettingsManager._encrypt(refresh_token) if refresh_token else None,
                "scopes": scopes,
                "expires_at": expires_at,
                "is_active": True
            }

            result = supabase.table("user_oauth_connections").upsert(data).execute()
            return True
        except Exception as e:
            st.error(f"Error saving OAuth connection: {e}")
            return False

    @staticmethod
    def get_oauth_connection(user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get OAuth connection for a provider"""
        try:
            supabase = get_supabase_client()
            result = supabase.table("user_oauth_connections")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .eq("is_active", True)\
                .execute()

            if result.data and len(result.data) > 0:
                conn = result.data[0]

                # Decrypt tokens
                conn["access_token"] = SettingsManager._decrypt(conn["access_token_encrypted"])
                if conn.get("refresh_token_encrypted"):
                    conn["refresh_token"] = SettingsManager._decrypt(conn["refresh_token_encrypted"])

                return conn
            return None
        except Exception as e:
            st.error(f"Error fetching OAuth connection: {e}")
            return None

    @staticmethod
    def list_connected_accounts(user_id: str) -> List[Dict[str, Any]]:
        """List all connected OAuth accounts for user"""
        try:
            supabase = get_supabase_client()
            result = supabase.table("user_oauth_connections")\
                .select("provider, provider_user_id, scopes, is_active, last_used_at, created_at")\
                .eq("user_id", user_id)\
                .execute()

            return result.data if result.data else []
        except Exception as e:
            st.error(f"Error listing connections: {e}")
            return []

    @staticmethod
    def disconnect_account(user_id: str, provider: str) -> bool:
        """Disconnect an OAuth account"""
        try:
            supabase = get_supabase_client()
            result = supabase.table("user_oauth_connections")\
                .update({"is_active": False})\
                .eq("user_id", user_id)\
                .eq("provider", provider)\
                .execute()

            return True
        except Exception as e:
            st.error(f"Error disconnecting account: {e}")
            return False

    @staticmethod
    def create_approval_request(
        user_id: str,
        task_type: str,
        task_description: str,
        estimated_cost: float,
        expires_at: Optional[str] = None
    ) -> Optional[str]:
        """Create an approval request for a task"""
        try:
            supabase = get_supabase_client()

            data = {
                "user_id": user_id,
                "task_type": task_type,
                "task_description": task_description,
                "estimated_cost": estimated_cost,
                "expires_at": expires_at,
                "status": "pending"
            }

            result = supabase.table("approval_history").insert(data).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            return None
        except Exception as e:
            st.error(f"Error creating approval request: {e}")
            return None

    @staticmethod
    def approve_task(approval_id: str) -> bool:
        """Approve a pending task"""
        try:
            supabase = get_supabase_client()

            result = supabase.table("approval_history")\
                .update({
                    "approved": True,
                    "approved_at": "now()",
                    "status": "approved"
                })\
                .eq("id", approval_id)\
                .execute()

            return True
        except Exception as e:
            st.error(f"Error approving task: {e}")
            return False
