"""
Free Tier Management for Chat Wallet

Provides free AI chat using Google Gemini's free tier.
Google subsidizes the free tier - no cost to app operator.
"""

import os
import streamlit as st
from typing import Tuple, Optional

# Free tier configuration - Google Gemini (free tier)
FREE_TIER_PROVIDER = "google"
FREE_TIER_MODEL = "gemini-2.0-flash"  # Fast, capable, free tier available


class FreeTier:
    """Manage free tier using Google Gemini's free API"""

    @staticmethod
    def get_app_api_key() -> Optional[str]:
        """Get the Google API key for free tier"""
        return os.getenv("GOOGLE_API_KEY")

    @staticmethod
    def is_available() -> bool:
        """Check if free tier is available (app has API key configured)"""
        return bool(FreeTier.get_app_api_key())

    @staticmethod
    def has_quota(user_id: str) -> bool:
        """Check if free tier is available (Gemini free tier has no per-user quota)"""
        return FreeTier.is_available()

    @staticmethod
    def check_and_get_config(user_id: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if user can use free tier and return config if so.

        Returns:
            (can_use_free_tier, config_dict or None)
        """
        if not FreeTier.is_available():
            return False, None

        # Google Gemini free tier - always available if API key set
        return True, {
            "provider": FREE_TIER_PROVIDER,
            "model": FREE_TIER_MODEL,
            "api_key": FreeTier.get_app_api_key(),
            "using_free_tier": True
        }

    @staticmethod
    def show_quota_status(user_id: str):
        """Show free tier status in UI"""
        if FreeTier.is_available():
            st.caption("Using Google Gemini (free tier)")

    @staticmethod
    def show_upgrade_prompt():
        """Show prompt to configure API access"""
        st.warning("AI not configured")
        st.markdown("""
**To start chatting, add a Google API key.**

Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
""")
