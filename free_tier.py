"""
Free Tier Management for Chat Wallet

Provides new users with free AI chat messages using the app's API key.
After quota exhausted, users are prompted to add their own API key.
"""

import os
import streamlit as st
from typing import Tuple, Optional
from datetime import datetime

# Free tier configuration
FREE_TIER_MESSAGES = 50  # Messages per user
FREE_TIER_PROVIDER = "google"
FREE_TIER_MODEL = "gemini-2.0-flash"


class FreeTier:
    """Manage free tier quota for users"""

    @staticmethod
    def get_app_api_key() -> Optional[str]:
        """Get the app's API key for free tier users (Google Gemini)"""
        return os.getenv("GOOGLE_API_KEY")

    @staticmethod
    def is_available() -> bool:
        """Check if free tier is available (app has API key configured)"""
        return bool(FreeTier.get_app_api_key())

    @staticmethod
    def get_usage(user_id: str) -> int:
        """Get current message count for user"""
        from supabase_client import get_supabase_client

        try:
            client = get_supabase_client(use_service_key=True)
            if not client:
                return 0

            result = client.table("user_settings").select(
                "free_tier_messages_used"
            ).eq("user_id", user_id).execute()

            if result.data and len(result.data) > 0:
                return result.data[0].get("free_tier_messages_used", 0) or 0
            return 0
        except Exception:
            # Column might not exist yet - return 0
            return 0

    @staticmethod
    def increment_usage(user_id: str) -> bool:
        """Increment message count for user atomically (call after successful message)"""
        from supabase_client import get_supabase_client

        try:
            client = get_supabase_client(use_service_key=True)
            if not client:
                return False

            # Try atomic increment via RPC first (requires Supabase function)
            try:
                client.rpc("increment_free_tier_usage", {"p_user_id": user_id}).execute()
                return True
            except Exception:
                pass  # RPC not available, fall back to upsert

            # Fallback: upsert with current value (not fully atomic but acceptable)
            current = FreeTier.get_usage(user_id)
            client.table("user_settings").upsert({
                "user_id": user_id,
                "free_tier_messages_used": current + 1,
                "updated_at": datetime.utcnow().isoformat()
            }, on_conflict="user_id").execute()

            return True
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Failed to increment free tier usage: {e}")
            return False

    @staticmethod
    def get_remaining(user_id: str) -> int:
        """Get remaining free messages for user"""
        used = FreeTier.get_usage(user_id)
        return max(0, FREE_TIER_MESSAGES - used)

    @staticmethod
    def has_quota(user_id: str) -> bool:
        """Check if user has free tier quota remaining"""
        if not FreeTier.is_available():
            return False
        return FreeTier.get_remaining(user_id) > 0

    @staticmethod
    def check_and_get_config(user_id: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if user can use free tier and return config if so.

        Returns:
            (can_use_free_tier, config_dict or None)
        """
        if not FreeTier.is_available():
            return False, None

        if not FreeTier.has_quota(user_id):
            return False, None

        # User can use free tier
        return True, {
            "provider": FREE_TIER_PROVIDER,
            "model": FREE_TIER_MODEL,
            "api_key": FreeTier.get_app_api_key(),
            "using_free_tier": True,
            "remaining_messages": FreeTier.get_remaining(user_id)
        }

    @staticmethod
    def show_quota_status(user_id: str):
        """Show free tier quota status in UI"""
        if not FreeTier.is_available():
            return

        remaining = FreeTier.get_remaining(user_id)
        total = FREE_TIER_MESSAGES

        if remaining > 0:
            # Show subtle indicator
            pct = remaining / total
            if pct > 0.5:
                st.caption(f"{remaining} free messages remaining")
            elif pct > 0.2:
                st.warning(f"{remaining} free messages remaining")
            else:
                st.warning(f"Only {remaining} free messages left! Add your own API key in Settings.")
        else:
            st.error("Free tier exhausted. Add your own API key in Settings to continue.")

    @staticmethod
    def show_upgrade_prompt():
        """Show upgrade prompt when quota exhausted"""
        st.error("You've used all your free messages!")
        st.markdown("""
**To continue chatting, add your own API key:**

1. **Google Gemini (Free)** - Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. **Anthropic Claude** - Sign up at [console.anthropic.com](https://console.anthropic.com)
3. **OpenAI GPT** - Sign up at [platform.openai.com](https://platform.openai.com)

Click **Settings** in the sidebar to add your key.
""")
