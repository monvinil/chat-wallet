"""
Spending Limits Enforcement - Enforces user-configured transaction limits

Checks:
1. Daily spending limit (total spend per day)
2. Per-transaction approval threshold
3. Daily spend tracking
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
import streamlit as st
from settings_manager import SettingsManager


class SpendingLimits:
    """Enforce user-configured spending limits before transactions"""

    # Session key for tracking daily spending
    _DAILY_SPEND_KEY = "_daily_spending"
    _DAILY_SPEND_DATE_KEY = "_daily_spending_date"

    @staticmethod
    def get_user_limits(user_id: str) -> Dict[str, float]:
        """Get user's spending limit settings"""
        settings = SettingsManager.get_user_settings(user_id)

        return {
            "daily_limit": float(settings.get("daily_spend_limit", 100.0)) if settings else 100.0,
            "approval_threshold": float(settings.get("require_approval_above", 50.0)) if settings else 50.0
        }

    @staticmethod
    def get_daily_spend(user_id: str) -> float:
        """Get user's spending for current day (tracked in session)"""
        today = date.today().isoformat()

        # Reset if new day
        if st.session_state.get(SpendingLimits._DAILY_SPEND_DATE_KEY) != today:
            st.session_state[SpendingLimits._DAILY_SPEND_KEY] = 0.0
            st.session_state[SpendingLimits._DAILY_SPEND_DATE_KEY] = today

        return float(st.session_state.get(SpendingLimits._DAILY_SPEND_KEY, 0.0))

    @staticmethod
    def record_spend(user_id: str, amount: float) -> None:
        """Record a spend transaction for daily tracking"""
        today = date.today().isoformat()

        # Initialize if needed
        if st.session_state.get(SpendingLimits._DAILY_SPEND_DATE_KEY) != today:
            st.session_state[SpendingLimits._DAILY_SPEND_KEY] = 0.0
            st.session_state[SpendingLimits._DAILY_SPEND_DATE_KEY] = today

        current = float(st.session_state.get(SpendingLimits._DAILY_SPEND_KEY, 0.0))
        st.session_state[SpendingLimits._DAILY_SPEND_KEY] = current + amount

    @staticmethod
    def check_transaction(
        user_id: str,
        amount: float,
        description: str = "transaction"
    ) -> Tuple[bool, Optional[str], bool]:
        """
        Check if a transaction is allowed under user's spending limits.

        Args:
            user_id: User ID
            amount: Transaction amount in USD
            description: Description for error messages

        Returns:
            Tuple of (allowed, error_message, requires_approval)
            - allowed: True if transaction can proceed
            - error_message: Reason if not allowed (None if allowed)
            - requires_approval: True if user must confirm (even if allowed)
        """
        limits = SpendingLimits.get_user_limits(user_id)
        daily_limit = limits["daily_limit"]
        approval_threshold = limits["approval_threshold"]

        current_daily_spend = SpendingLimits.get_daily_spend(user_id)
        new_total = current_daily_spend + amount

        # Check daily limit
        if new_total > daily_limit:
            remaining = max(0, daily_limit - current_daily_spend)
            return (
                False,
                f"This {description} (${amount:.2f}) would exceed your daily spending limit of ${daily_limit:.2f}. "
                f"You've spent ${current_daily_spend:.2f} today. Remaining: ${remaining:.2f}. "
                f"You can adjust your limit in Settings.",
                False
            )

        # Check if approval required
        requires_approval = amount > approval_threshold

        if requires_approval:
            return (
                True,
                None,
                True  # Requires explicit confirmation
            )

        return (True, None, False)

    @staticmethod
    def format_approval_request(
        amount: float,
        description: str,
        recipient: Optional[str] = None
    ) -> str:
        """Format an approval request message for the user"""
        msg = f"**Approval Required**\n\n"
        msg += f"This transaction exceeds your approval threshold.\n\n"
        msg += f"- **Amount:** ${amount:.2f}\n"
        msg += f"- **Description:** {description}\n"

        if recipient:
            msg += f"- **Recipient:** {recipient}\n"

        msg += f"\nPlease confirm by saying 'yes' or 'approve' to proceed."

        return msg

    @staticmethod
    def get_remaining_daily_budget(user_id: str) -> Dict[str, float]:
        """Get user's remaining daily spending budget"""
        limits = SpendingLimits.get_user_limits(user_id)
        daily_limit = limits["daily_limit"]
        current_spend = SpendingLimits.get_daily_spend(user_id)
        remaining = max(0, daily_limit - current_spend)

        return {
            "daily_limit": daily_limit,
            "spent_today": current_spend,
            "remaining": remaining,
            "approval_threshold": limits["approval_threshold"]
        }


def check_spending_limit(user_id: str, amount: float, description: str = "transaction") -> Tuple[bool, Optional[str]]:
    """
    Convenience function to check spending limits before a transaction.

    Returns:
        Tuple of (can_proceed, message)
        - can_proceed: False means hard block, True means continue (may need approval)
        - message: Error message or approval request message
    """
    allowed, error, requires_approval = SpendingLimits.check_transaction(
        user_id, amount, description
    )

    if not allowed:
        return (False, error)

    if requires_approval:
        approval_msg = SpendingLimits.format_approval_request(amount, description)
        return (True, approval_msg)

    return (True, None)
