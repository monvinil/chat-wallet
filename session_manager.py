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
        if "cookie_manager" not in st.session_state:
            st.session_state.cookie_manager = stx.CookieManager(key="chat_wallet_cookies")
            st.session_state._cookie_manager_init = True
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
            print(f"[Session] create_session called for user_id={user_id[:8]}...")
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                print("[Session] ERROR: Could not get Supabase client")
                return None

            session_token = SessionManager.generate_session_token()
            expires_at = datetime.utcnow() + timedelta(days=SessionManager.SESSION_EXPIRY_DAYS)

            print(f"[Session] Inserting session with token={session_token[:8]}...")

            # Store session in database
            result = supabase.table("sessions").upsert({
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "email": email,
                "wallet_address": wallet_address
            }, on_conflict="user_id").execute()

            print(f"[Session] Upsert result: {result.data}")

            if result.data:
                print(f"[Session] Session created successfully")
                return session_token
            print(f"[Session] No data returned from upsert")
            return None

        except Exception as e:
            print(f"[Session] ERROR creating session: {e}")
            import traceback
            traceback.print_exc()
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
        try:
            print(f"[Session] Saving cookie with token={session_token[:8]}...")
            cookie_manager = SessionManager.get_cookie_manager()
            cookie_manager.set(
                SessionManager.COOKIE_NAME,
                session_token,
                expires_at=datetime.now() + timedelta(days=SessionManager.SESSION_EXPIRY_DAYS)
            )
            print(f"[Session] Cookie save called successfully")
        except Exception as e:
            print(f"[Session] ERROR saving cookie: {e}")
            import traceback
            traceback.print_exc()

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
        import os
        debug = os.getenv("DEBUG_SESSION") == "true"

        # Skip if already logged in (with both user_id AND wallet_address set)
        # This prevents unnecessary restoration attempts after successful login
        if st.session_state.get("wallet_address") and st.session_state.get("user_id"):
            if debug:
                print(f"[Session] Already logged in, skipping restore")
            return True

        try:
            # Check for session cookie
            session_token = SessionManager.get_session_cookie()

            if debug:
                print(f"[Session] Cookie read attempt, token={session_token[:8] if session_token else 'None'}...")

            # Cookie manager may return None on first render - need rerun
            # Track attempts to prevent infinite rerun loops
            if session_token is None:
                attempts = st.session_state.get("_cookie_read_attempts", 0)
                if debug:
                    print(f"[Session] Cookie is None, attempt {attempts + 1}/2")
                if attempts < 2:
                    st.session_state._cookie_read_attempts = attempts + 1
                    # Cookie manager needs a rerun to read cookies from browser
                    st.rerun()
                # After max attempts, no cookie found - user not logged in
                if debug:
                    print(f"[Session] No cookie after 2 attempts - user not logged in")
                return False

            # Reset attempts counter on successful read
            st.session_state._cookie_read_attempts = 0

            if debug:
                print(f"[Session] Found cookie, validating in database...")

            # Validate session in database
            session_data = SessionManager.get_session(session_token)
            if not session_data:
                # Session invalid or expired - clear stale cookie
                if debug:
                    print(f"[Session] Session not found in database - clearing stale cookie")
                SessionManager.clear_session_cookie()
                return False

            if debug:
                print(f"[Session] Session valid, restoring state for {session_data.get('email')}")

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
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def login(user_id: str, email: str, wallet_address: str) -> bool:
        """Complete login: create session and set cookie"""
        print(f"[Session] Creating session for user {user_id[:8]}...")
        session_token = SessionManager.create_session(user_id, email, wallet_address)
        if session_token:
            print(f"[Session] Session created, saving cookie...")
            SessionManager.save_session_cookie(session_token)
            st.session_state.session_token = session_token
            print(f"[Session] Login complete")
            return True
        print(f"[Session] Failed to create session")
        return False

    @staticmethod
    def logout():
        """Complete logout: clear session, cookie, and all user caches"""
        session_token = st.session_state.get("session_token")
        if session_token:
            SessionManager.delete_session(session_token)

        SessionManager.clear_session_cookie()

        # Clear all user-specific caches (LLM config, balance cache, spending, etc.)
        keys_to_clear = []
        for key in st.session_state:
            if any(prefix in key for prefix in [
                "_llm_config_",
                "_balance_cache",
                "_daily_spending",
                "_last_activity",
                "guest_settings_",
                "_send_",
                "_seed_verify"
            ]):
                keys_to_clear.append(key)

        for key in keys_to_clear:
            del st.session_state[key]

        # Clear core session state
        for key in ["user_id", "user_email", "wallet_address", "wallet_encrypted",
                    "wallet_salt", "wallet_key", "wallet_locked", "session_token",
                    "balances", "agent", "messages", "guest_mode", "guest_wallet_address",
                    "guest_mnemonic", "_guest_user_id"]:
            if key in st.session_state:
                del st.session_state[key]
