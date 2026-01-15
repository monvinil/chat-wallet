"""
Settings Manager - Handle user settings, LLM config, and OAuth connections
"""

import os
from typing import Dict, Any, Optional, List
from supabase_client import get_supabase_client
import streamlit as st

# Import centralized utilities
from utils.encryption import SettingsEncryption
from utils.logger import logger


class SettingsManager:
    """Manage user settings and encrypted credentials"""

    @staticmethod
    def _encrypt(data: str) -> str:
        """
        Encrypt sensitive data (API keys, OAuth tokens)

        Args:
            data: Plain text data

        Returns:
            Encrypted data (base64 string)
        """
        return SettingsEncryption.encrypt(data)

    @staticmethod
    def _decrypt(encrypted_data: str) -> str | None:
        """
        Decrypt sensitive data

        Args:
            encrypted_data: Encrypted data (base64 string)

        Returns:
            Decrypted plain text, or None if decryption fails
        """
        return SettingsEncryption.decrypt(encrypted_data)

    @staticmethod
    def get_user_settings(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user settings from database"""
        # Handle guest users - they store settings in session state, not database
        if user_id and user_id.startswith("guest_"):
            guest_settings = st.session_state.get(f"guest_settings_{user_id}", {})
            return guest_settings if guest_settings else None

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return None
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
            logger.error(f"Error fetching settings for user {user_id}: {e}")
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
        # Handle guest users - store in session state only
        if user_id and user_id.startswith("guest_"):
            guest_settings = {
                "user_id": user_id,
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                "llm_api_key": llm_api_key,  # No encryption needed for session-only storage
                "daily_spend_limit": daily_spend_limit,
                "require_approval_above": require_approval_above,
                "allow_recurring_payments": allow_recurring_payments,
                "allow_account_access": allow_account_access
            }
            st.session_state[f"guest_settings_{user_id}"] = guest_settings
            return True

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return False

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
    def get_llm_config(user_id: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get LLM configuration for user (cached per session for performance)
        Falls back to env var only for development (production requires user API key)
        """
        # Default config - only uses env var if set (for development)
        default_config = {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),  # Will be None in production
            "using_default": True
        }

        if not user_id:
            return default_config

        # Check session cache first (avoids repeated DB calls)
        cache_key = f"_llm_config_{user_id}"
        if not force_refresh and cache_key in st.session_state:
            return st.session_state[cache_key]

        settings = SettingsManager.get_user_settings(user_id)
        if not settings or not settings.get("llm_api_key"):
            return default_config

        config = {
            "provider": settings.get("llm_provider", "anthropic"),
            "model": settings.get("llm_model", "claude-sonnet-4-20250514"),
            "api_key": settings.get("llm_api_key"),
            "using_default": False
        }

        # Cache for this session
        st.session_state[cache_key] = config
        return config

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
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return False

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
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return None
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
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return []
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
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return False
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
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return None

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
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return False

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

    @staticmethod
    def update_llm_settings(
        user_id: str,
        provider: str,
        api_key: str,
        model: str
    ) -> bool:
        """
        Convenience method to update only LLM settings without affecting other settings
        Preserves existing settings for spend limits, approvals, etc.
        """
        # Get existing settings to preserve them
        existing = SettingsManager.get_user_settings(user_id)

        success = SettingsManager.save_user_settings(
            user_id=user_id,
            llm_provider=provider,
            llm_model=model,
            llm_api_key=api_key,
            daily_spend_limit=existing.get("daily_spend_limit", 100.00) if existing else 100.00,
            require_approval_above=existing.get("require_approval_above", 50.00) if existing else 50.00,
            allow_recurring_payments=existing.get("allow_recurring_payments", False) if existing else False,
            allow_account_access=existing.get("allow_account_access", False) if existing else False
        )

        # Invalidate LLM config cache on update
        if success:
            cache_key = f"_llm_config_{user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]

        return success

    @staticmethod
    def clear_all_settings(user_id: str) -> bool:
        """Clear all user settings (reset to defaults)"""
        try:
            # Handle guest users
            if user_id and user_id.startswith("guest_"):
                guest_key = f"guest_settings_{user_id}"
                if guest_key in st.session_state:
                    del st.session_state[guest_key]
                # Clear LLM config cache
                cache_key = f"_llm_config_{user_id}"
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                return True

            # For database users, delete from Supabase
            supabase = get_supabase_client()
            if not supabase:
                return False

            supabase.table("user_settings").delete().eq("user_id", user_id).execute()

            # Clear cache
            cache_key = f"_llm_config_{user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]

            return True
        except Exception as e:
            logger.error(f"Failed to clear settings: {e}")
            return False

    @staticmethod
    def disconnect_all_oauth(user_id: str) -> bool:
        """Disconnect all OAuth accounts for a user"""
        try:
            # Handle guest users - they don't have OAuth
            if user_id and user_id.startswith("guest_"):
                return True

            supabase = get_supabase_client()
            if not supabase:
                return False

            # Delete all OAuth connections
            supabase.table("oauth_connections").delete().eq("user_id", user_id).execute()

            return True
        except Exception as e:
            logger.error(f"Failed to disconnect OAuth accounts: {e}")
            return False
