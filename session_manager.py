"""
Session Manager - Persistent sessions across page refreshes using cookies
"""

import streamlit as st
import extra_streamlit_components as stx
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class SessionManager:
    """Manage persistent user sessions using cookies"""

    COOKIE_NAME = "chat_wallet_session"
    SESSION_EXPIRY_DAYS = 30
    _cookie_manager = None

    @staticmethod
    def get_cookie_manager():
        """Get cookie manager instance (created once per session)"""
        if "_cookie_manager_init" not in st.session_state:
            st.session_state._cookie_manager_init = True
            st.session_state.cookie_manager = stx.CookieManager(key="chat_wallet_cookies")
        return st.session_state.cookie_manager

    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure random session token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_session(user_id: str, email: str, wallet_address: str) -> Optional[str]:
        """Create a new session and store in database"""
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return None

            session_token = SessionManager.generate_session_token()
            expires_at = datetime.utcnow() + timedelta(days=SessionManager.SESSION_EXPIRY_DAYS)

            # Store session in database
            result = supabase.table("sessions").upsert({
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "email": email,
                "wallet_address": wallet_address
            }, on_conflict="user_id").execute()

            if result.data:
                return session_token
            return None

        except Exception as e:
            print(f"Error creating session: {e}")
            return None

    @staticmethod
    def get_session(session_token: str) -> Optional[Dict[str, Any]]:
        """Retrieve session from database"""
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return None

            result = supabase.table("sessions").select("*").eq(
                "session_token", session_token
            ).single().execute()

            if result.data:
                # Check if expired
                expires_at = datetime.fromisoformat(result.data["expires_at"].replace("Z", "+00:00"))
                if expires_at.replace(tzinfo=None) > datetime.utcnow():
                    return result.data
                else:
                    # Session expired, delete it
                    SessionManager.delete_session(session_token)
            return None

        except Exception as e:
            print(f"Error getting session: {e}")
            return None

    @staticmethod
    def delete_session(session_token: str) -> bool:
        """Delete session from database"""
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return False

            supabase.table("sessions").delete().eq(
                "session_token", session_token
            ).execute()
            return True

        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    @staticmethod
    def save_session_cookie(session_token: str):
        """Save session token to browser cookie"""
        cookie_manager = SessionManager.get_cookie_manager()
        cookie_manager.set(
            SessionManager.COOKIE_NAME,
            session_token,
            expires_at=datetime.now() + timedelta(days=SessionManager.SESSION_EXPIRY_DAYS)
        )

    @staticmethod
    def get_session_cookie() -> Optional[str]:
        """Get session token from browser cookie"""
        cookie_manager = SessionManager.get_cookie_manager()
        return cookie_manager.get(SessionManager.COOKIE_NAME)

    @staticmethod
    def clear_session_cookie():
        """Clear session cookie from browser"""
        cookie_manager = SessionManager.get_cookie_manager()
        cookie_manager.delete(SessionManager.COOKIE_NAME)

    @staticmethod
    def restore_session() -> bool:
        """Try to restore session from cookie on page load"""
        # Skip if already logged in
        if st.session_state.get("wallet_address") and st.session_state.get("user_id"):
            return True

        # Skip if we already attempted restoration this session
        if st.session_state.get("_session_restore_attempted"):
            return False

        # Skip if cookie manager not ready yet (prevents multiple reruns)
        if "_cookie_manager_init" not in st.session_state:
            return False

        st.session_state._session_restore_attempted = True

        try:
            # Check for session cookie
            session_token = SessionManager.get_session_cookie()
            if not session_token:
                return False

            # Validate session in database
            session_data = SessionManager.get_session(session_token)
            if not session_data:
                SessionManager.clear_session_cookie()
                return False

            # Restore session state
            st.session_state.user_id = session_data["user_id"]
            st.session_state.user_email = session_data["email"]
            st.session_state.wallet_address = session_data["wallet_address"]
            st.session_state.session_token = session_token

            # Try to restore encrypted wallet from cloud
            from supabase_client import get_encrypted_wallet
            encrypted_wallet = get_encrypted_wallet(session_data["user_id"])

            if encrypted_wallet:
                st.session_state.wallet_encrypted = encrypted_wallet["encrypted_data"]
                st.session_state.wallet_salt = encrypted_wallet["salt"]
                st.session_state.wallet_locked = True  # Will need password to unlock
            else:
                st.session_state.wallet_locked = True

            return True
        except Exception as e:
            print(f"Session restore error: {e}")
            return False

    @staticmethod
    def login(user_id: str, email: str, wallet_address: str) -> bool:
        """Complete login: create session and set cookie"""
        session_token = SessionManager.create_session(user_id, email, wallet_address)
        if session_token:
            SessionManager.save_session_cookie(session_token)
            st.session_state.session_token = session_token
            return True
        return False

    @staticmethod
    def logout():
        """Complete logout: clear session and cookie"""
        session_token = st.session_state.get("session_token")
        if session_token:
            SessionManager.delete_session(session_token)

        SessionManager.clear_session_cookie()

        # Clear session state
        for key in ["user_id", "user_email", "wallet_address", "wallet_encrypted",
                    "wallet_salt", "wallet_key", "wallet_locked", "session_token",
                    "balances", "agent", "messages"]:
            if key in st.session_state:
                del st.session_state[key]
