"""
Analytics Module - Track key events for USDChat
MVP: Simple local tracking, can upgrade to Mixpanel/Amplitude later
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st

# Analytics provider (future: mixpanel, amplitude)
ANALYTICS_PROVIDER = os.getenv("ANALYTICS_PROVIDER", "local")
MIXPANEL_TOKEN = os.getenv("MIXPANEL_TOKEN", "")


class Analytics:
    """Simple analytics tracker"""

    # Event types
    EVENT_WALLET_CREATED = "wallet_created"
    EVENT_WALLET_IMPORTED = "wallet_imported"
    EVENT_MESSAGE_SENT = "message_sent"
    EVENT_TRANSACTION_PREVIEW = "transaction_preview"
    EVENT_TRANSACTION_APPROVED = "transaction_approved"
    EVENT_TRANSACTION_COMPLETED = "transaction_completed"
    EVENT_GIFT_CARD_SEARCH = "gift_card_search"
    EVENT_GIFT_CARD_PURCHASE = "gift_card_purchase"
    EVENT_EMAIL_CONNECTED = "email_connected"
    EVENT_VERIFICATION_CODE_READ = "verification_code_read"
    EVENT_SHOWCASE_AGENT_USED = "showcase_agent_used"
    EVENT_API_KEY_CONFIGURED = "api_key_configured"
    EVENT_FREE_TIER_USED = "free_tier_used"

    @staticmethod
    def track(
        event: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Track an analytics event.

        Args:
            event: Event name (use EVENT_* constants)
            properties: Optional event properties
            user_id: Optional user ID (uses session if not provided)
        """
        if not user_id:
            user_id = st.session_state.get("user_id", "anonymous")

        props = properties or {}
        props["timestamp"] = datetime.utcnow().isoformat()
        props["session_id"] = st.session_state.get("session_id", "")

        if ANALYTICS_PROVIDER == "mixpanel" and MIXPANEL_TOKEN:
            Analytics._track_mixpanel(event, props, user_id)
        else:
            Analytics._track_local(event, props, user_id)

    @staticmethod
    def _track_local(event: str, properties: Dict, user_id: str) -> None:
        """Local tracking - store in session for demo"""
        if "_analytics_events" not in st.session_state:
            st.session_state._analytics_events = []

        st.session_state._analytics_events.append({
            "event": event,
            "user_id": user_id,
            "properties": properties
        })

        # Also log for debugging
        from utils.logger import logger
        logger.debug(f"Analytics: {event} | user={user_id} | props={properties}")

    @staticmethod
    def _track_mixpanel(event: str, properties: Dict, user_id: str) -> None:
        """Send to Mixpanel"""
        try:
            import requests
            import base64
            import json

            data = {
                "event": event,
                "properties": {
                    **properties,
                    "distinct_id": user_id,
                    "token": MIXPANEL_TOKEN
                }
            }

            encoded = base64.b64encode(json.dumps(data).encode()).decode()
            requests.get(
                f"https://api.mixpanel.com/track?data={encoded}",
                timeout=2
            )
        except Exception:
            # Fail silently - analytics shouldn't break the app
            pass

    @staticmethod
    def get_session_events() -> list:
        """Get events tracked in current session (for demo/debugging)"""
        return st.session_state.get("_analytics_events", [])

    @staticmethod
    def get_session_summary() -> Dict[str, int]:
        """Get summary counts of events in session"""
        events = Analytics.get_session_events()
        summary = {}
        for e in events:
            event_name = e["event"]
            summary[event_name] = summary.get(event_name, 0) + 1
        return summary


# Convenience functions
def track_wallet_created(chain: str = "evm"):
    Analytics.track(Analytics.EVENT_WALLET_CREATED, {"chain": chain})


def track_message_sent(provider: str = "unknown", is_free_tier: bool = False):
    Analytics.track(Analytics.EVENT_MESSAGE_SENT, {
        "provider": provider,
        "is_free_tier": is_free_tier
    })


def track_transaction_completed(amount: float, network: str, success: bool):
    Analytics.track(Analytics.EVENT_TRANSACTION_COMPLETED, {
        "amount_usd": amount,
        "network": network,
        "success": success
    })


def track_gift_card_purchase(brand: str, amount: float):
    Analytics.track(Analytics.EVENT_GIFT_CARD_PURCHASE, {
        "brand": brand,
        "amount_usd": amount
    })


def track_showcase_agent(agent_id: str, agent_name: str):
    Analytics.track(Analytics.EVENT_SHOWCASE_AGENT_USED, {
        "agent_id": agent_id,
        "agent_name": agent_name
    })
