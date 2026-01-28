"""
Rate Limiting - Protect against brute force and abuse

Implements:
- Login attempt limiting (prevent password brute force)
- Activity-based session timeout (auto-lock wallet)
- Request deduplication for expensive operations
"""

import time
from typing import Tuple, Optional
import streamlit as st


class RateLimiter:
    """Rate limiting utilities for security-sensitive operations"""

    # Login rate limiting settings
    MAX_LOGIN_ATTEMPTS = 3
    LOGIN_LOCKOUT_SECONDS = 300  # 5 minutes

    # Session activity timeout - default 15 minutes (configurable per user)
    DEFAULT_TIMEOUT_MINUTES = 15
    SESSION_TIMEOUT_SECONDS = DEFAULT_TIMEOUT_MINUTES * 60

    @staticmethod
    def get_configured_timeout_seconds() -> int:
        """Get the user's configured timeout in seconds, or default."""
        user_id = st.session_state.get("user_id")
        if user_id:
            try:
                from settings_manager import SettingsManager
                settings = SettingsManager.get_user_settings(user_id)
                if settings and settings.get("auto_lock_minutes"):
                    return settings.get("auto_lock_minutes") * 60
            except Exception:
                pass
        return RateLimiter.SESSION_TIMEOUT_SECONDS

    @staticmethod
    def _get_login_key(email: str) -> str:
        """Get session key for tracking login attempts"""
        # Normalize email for consistent tracking
        return f"_login_attempts_{email.lower().strip()}"

    @staticmethod
    def check_login_allowed(email: str) -> Tuple[bool, Optional[str]]:
        """
        Check if login attempt is allowed for this email.

        Returns:
            Tuple of (allowed, error_message)
        """
        key = RateLimiter._get_login_key(email)
        lockout_key = f"{key}_lockout_until"

        # Check if currently locked out
        lockout_until = st.session_state.get(lockout_key, 0)
        if lockout_until > time.time():
            remaining = int(lockout_until - time.time())
            minutes = remaining // 60
            seconds = remaining % 60
            if minutes > 0:
                return False, f"Too many failed attempts. Try again in {minutes}m {seconds}s."
            return False, f"Too many failed attempts. Try again in {seconds} seconds."

        return True, None

    @staticmethod
    def record_login_attempt(email: str, success: bool) -> None:
        """
        Record a login attempt (success or failure).

        After MAX_LOGIN_ATTEMPTS failures, locks out for LOCKOUT_SECONDS.
        """
        key = RateLimiter._get_login_key(email)
        lockout_key = f"{key}_lockout_until"

        if success:
            # Clear attempt counter on success
            st.session_state[key] = 0
            st.session_state[lockout_key] = 0
        else:
            # Increment failure counter
            attempts = st.session_state.get(key, 0) + 1
            st.session_state[key] = attempts

            # Check if should lock out
            if attempts >= RateLimiter.MAX_LOGIN_ATTEMPTS:
                st.session_state[lockout_key] = time.time() + RateLimiter.LOGIN_LOCKOUT_SECONDS
                st.session_state[key] = 0  # Reset counter after lockout

    @staticmethod
    def get_remaining_attempts(email: str) -> int:
        """Get remaining login attempts before lockout"""
        key = RateLimiter._get_login_key(email)
        attempts = st.session_state.get(key, 0)
        return max(0, RateLimiter.MAX_LOGIN_ATTEMPTS - attempts)

    @staticmethod
    def update_activity() -> None:
        """Update last activity timestamp (call on user interactions)"""
        st.session_state._last_activity = time.time()

    @staticmethod
    def check_session_timeout() -> bool:
        """
        Check if session has timed out due to inactivity.

        Returns:
            True if session is still active, False if timed out
        """
        last_activity = st.session_state.get("_last_activity")

        if last_activity is None:
            # No activity recorded yet, initialize
            st.session_state._last_activity = time.time()
            return True

        elapsed = time.time() - last_activity
        timeout_seconds = RateLimiter.get_configured_timeout_seconds()
        return elapsed < timeout_seconds

    @staticmethod
    def get_time_until_timeout() -> int:
        """Get seconds remaining until session timeout"""
        last_activity = st.session_state.get("_last_activity", time.time())
        elapsed = time.time() - last_activity
        timeout_seconds = RateLimiter.get_configured_timeout_seconds()
        remaining = timeout_seconds - elapsed
        return max(0, int(remaining))


def check_and_handle_timeout() -> bool:
    """
    Check session timeout and lock wallet if expired.

    Returns:
        True if session is active, False if timed out (wallet locked)
    """
    # Skip if no wallet or already locked
    if not st.session_state.get("wallet_address"):
        return True
    if st.session_state.get("wallet_locked", True):
        return True

    if not RateLimiter.check_session_timeout():
        # Session timed out - use WalletManager to properly lock
        from wallet_manager import WalletManager
        WalletManager.lock_wallet()
        return False

    return True
