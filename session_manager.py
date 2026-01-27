"""
Session Manager - Persistent sessions across page refreshes using cookies

Uses direct JavaScript cookie manipulation for reliability in production.
Falls back to extra_streamlit_components if needed.
"""

import streamlit as st
import streamlit.components.v1 as components
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Try to import extra_streamlit_components, but don't require it
try:
    import extra_streamlit_components as stx
    STX_AVAILABLE = True
except ImportError:
    STX_AVAILABLE = False


class SessionManager:
    """Manage persistent user sessions using cookies"""

    COOKIE_NAME = "chat_wallet_session"
    SESSION_EXPIRY_DAYS = 30
    _cookie_manager = None

    @staticmethod
    def get_cookie_manager():
        """Get cookie manager instance (created once per session)"""
        if not STX_AVAILABLE:
            return None
        if "cookie_manager" not in st.session_state:
            st.session_state.cookie_manager = stx.CookieManager(key="chat_wallet_cookies")
            st.session_state._cookie_manager_init = True
        return st.session_state.cookie_manager

    @staticmethod
    def _get_all_cookies() -> dict:
        """Get all cookies (cached to avoid multiple get_all calls)"""
        # Cache cookies in session state to avoid multiple component calls
        if "_cached_cookies" not in st.session_state:
            cookie_manager = SessionManager.get_cookie_manager()
            if cookie_manager:
                cookies = cookie_manager.get_all(key="all_cookies")
                # Only cache if we got at least one cookie (JS may not have loaded yet)
                if cookies:
                    st.session_state._cached_cookies = cookies
                else:
                    return {}
            else:
                st.session_state._cached_cookies = {}
        return st.session_state._cached_cookies

    @staticmethod
    def _set_cookie_js(name: str, value: str, days: int = 30):
        """Set cookie using direct JavaScript injection (more reliable)"""
        import re
        # Sanitize inputs to prevent XSS - only allow alphanumeric, underscore, hyphen, and base64 chars
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError("Invalid cookie name")
        if not re.match(r'^[a-zA-Z0-9_=-]+$', value):
            raise ValueError("Invalid cookie value")

        js_code = f"""
        <script>
        (function() {{
            var date = new Date();
            date.setTime(date.getTime() + ({days} * 24 * 60 * 60 * 1000));
            var expires = "expires=" + date.toUTCString();
            document.cookie = "{name}={value};" + expires + ";path=/;SameSite=Lax;Secure";
        }})();
        </script>
        """
        components.html(js_code, height=0)

    @staticmethod
    def _get_cookie_js(name: str) -> Optional[str]:
        """
        Read cookie value. Note: JavaScript can't return values to Python,
        so we use the stx cookie manager for reading (it's more reliable for reads).
        """
        cookie_manager = SessionManager.get_cookie_manager()
        if cookie_manager:
            return cookie_manager.get(name)
        return None

    @staticmethod
    def _delete_cookie_js(name: str):
        """Delete cookie using JavaScript"""
        import re
        # Sanitize name to prevent XSS
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError("Invalid cookie name")

        js_code = f"""
        <script>
        document.cookie = "{name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;Secure";
        </script>
        """
        components.html(js_code, height=0)

    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure random session token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_session(user_id: str, email: str, wallet_address: str, solana_address: str = None) -> Optional[str]:
        """Create a new session and store in database"""
        from supabase_client import get_supabase_client
        from utils.logger import logger

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                logger.error("Session creation failed: no database connection")
                return None

            session_token = SessionManager.generate_session_token()
            expires_at = datetime.utcnow() + timedelta(days=SessionManager.SESSION_EXPIRY_DAYS)

            # Store session in database
            session_data = {
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "email": email,
                "wallet_address": wallet_address
            }
            if solana_address:
                session_data["solana_address"] = solana_address

            result = supabase.table("sessions").upsert(session_data, on_conflict="user_id").execute()

            if result.data:
                logger.debug("Session created successfully")
                return session_token
            logger.warning("Session creation returned no data")
            return None

        except Exception as e:
            logger.error(f"Session creation error: {type(e).__name__}")
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
            from utils.logger import logger
            logger.debug(f"Session lookup error: {type(e).__name__}")
            return None

    @staticmethod
    def delete_session(session_token: str) -> bool:
        """Delete session from database"""
        from supabase_client import get_supabase_client
        from utils.logger import logger

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return False

            supabase.table("sessions").delete().eq(
                "session_token", session_token
            ).execute()
            return True

        except Exception as e:
            logger.error(f"Session deletion error: {type(e).__name__}")
            return False

    @staticmethod
    def save_session_cookie(session_token: str):
        """Save session token to browser cookie using multiple methods for reliability"""
        from utils.logger import logger

        # Method 1: Direct JavaScript injection (most reliable in production)
        try:
            SessionManager._set_cookie_js(
                SessionManager.COOKIE_NAME,
                session_token,
                SessionManager.SESSION_EXPIRY_DAYS
            )
        except Exception as e:
            logger.debug(f"JS cookie set failed: {type(e).__name__}")

        # Method 2: stx cookie manager (backup)
        try:
            cookie_manager = SessionManager.get_cookie_manager()
            if cookie_manager:
                cookie_manager.set(
                    SessionManager.COOKIE_NAME,
                    session_token,
                    expires_at=datetime.now() + timedelta(days=SessionManager.SESSION_EXPIRY_DAYS)
                )
        except Exception as e:
            logger.debug(f"stx cookie set failed: {type(e).__name__}")

        # Also store in session state as ultimate fallback
        st.session_state._session_token_backup = session_token

    @staticmethod
    def get_session_cookie() -> Optional[str]:
        """Get session token from browser cookie"""
        # Use cached cookies to avoid multiple get_all() component calls
        all_cookies = SessionManager._get_all_cookies()
        token = all_cookies.get(SessionManager.COOKIE_NAME)
        if token:
            return token

        # Fallback to session state backup (won't survive refresh, but useful for same session)
        return st.session_state.get("_session_token_backup")

    @staticmethod
    def clear_session_cookie():
        """Clear session cookie from browser"""
        # Method 1: Direct JavaScript
        try:
            SessionManager._delete_cookie_js(SessionManager.COOKIE_NAME)
            SessionManager._delete_cookie_js("chat_wallet_key")  # Also clear wallet key
        except Exception:
            pass

        # Method 2: stx cookie manager
        try:
            cookie_manager = SessionManager.get_cookie_manager()
            if cookie_manager:
                cookie_manager.delete(SessionManager.COOKIE_NAME)
        except Exception:
            pass

        # Clear session state backup
        if "_session_token_backup" in st.session_state:
            del st.session_state["_session_token_backup"]

    @staticmethod
    def save_wallet_key(wallet_key: str):
        """
        DEPRECATED: No longer saves wallet key to cookie for security.
        Wallet key is only stored in session state (memory).
        Users must re-enter password after page refresh.
        """
        # SECURITY: Intentionally does nothing
        # Keeping method signature for backwards compatibility
        pass

    @staticmethod
    def get_wallet_key() -> Optional[str]:
        """
        DEPRECATED: No longer reads wallet key from cookie for security.
        Always returns None - wallet must be unlocked with password.
        """
        # SECURITY: Intentionally returns None
        # Keeping method signature for backwards compatibility
        return None

    @staticmethod
    def clear_wallet_key():
        """Clear wallet key cookie (when user explicitly locks wallet)"""
        try:
            SessionManager._delete_cookie_js("chat_wallet_key")
        except Exception:
            pass

    @staticmethod
    def restore_session() -> bool:
        """Try to restore session from cookie on page load"""
        from utils.logger import logger

        # Skip if already logged in (with both user_id AND wallet_address set)
        # This prevents unnecessary restoration attempts after successful login
        if st.session_state.get("wallet_address") and st.session_state.get("user_id"):
            return True

        try:
            # Check for session cookie
            session_token = SessionManager.get_session_cookie()

            # Cookie manager may return None on first render - need rerun
            # Track attempts to prevent infinite rerun loops
            if session_token is None:
                attempts = st.session_state.get("_cookie_read_attempts", 0)
                if attempts < 2:
                    st.session_state._cookie_read_attempts = attempts + 1
                    # Clear cached cookies so next render fetches fresh
                    if "_cached_cookies" in st.session_state:
                        del st.session_state["_cached_cookies"]
                    # Cookie manager needs a rerun to read cookies from browser
                    st.rerun()
                # After max attempts, no cookie found - user not logged in
                return False

            # Reset attempts counter on successful read
            st.session_state._cookie_read_attempts = 0

            # Validate session in database
            session_data = SessionManager.get_session(session_token)
            if not session_data:
                # Session invalid or expired - clear stale cookie
                SessionManager.clear_session_cookie()
                return False

            # Restore session state
            st.session_state.user_id = session_data["user_id"]
            st.session_state.user_email = session_data["email"]
            st.session_state.wallet_address = session_data["wallet_address"]
            st.session_state.session_token = session_token

            # Restore Solana address if stored
            if session_data.get("solana_address"):
                st.session_state.solana_address = session_data["solana_address"]

            # Try to restore encrypted wallet from cloud
            from supabase_client import get_encrypted_wallet
            encrypted_wallet = get_encrypted_wallet(session_data["user_id"])

            if encrypted_wallet:
                st.session_state.wallet_encrypted = encrypted_wallet["encrypted_data"]
                st.session_state.wallet_salt = encrypted_wallet["salt"]
                # Don't force lock - let user browse/chat freely
                # Transaction signing will prompt for unlock when wallet_key is needed

            return True
        except Exception as e:
            logger.error(f"Session restore error: {type(e).__name__}")
            return False

    @staticmethod
    def login(user_id: str, email: str, wallet_address: str, solana_address: str = None) -> bool:
        """Complete login: create session and set cookie"""
        from utils.logger import logger

        session_token = SessionManager.create_session(user_id, email, wallet_address, solana_address)
        if session_token:
            SessionManager.save_session_cookie(session_token)
            st.session_state.session_token = session_token
            logger.debug("Login successful")
            return True
        logger.warning("Login failed: session creation error")
        return False

    @staticmethod
    def update_session_solana_address(solana_address: str) -> bool:
        """Update the current session with Solana address (after wallet unlock)"""
        from supabase_client import get_supabase_client
        from utils.logger import logger

        session_token = st.session_state.get("session_token")
        if not session_token or not solana_address:
            return False

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return False

            supabase.table("sessions").update({
                "solana_address": solana_address
            }).eq("session_token", session_token).execute()

            st.session_state.solana_address = solana_address
            return True
        except Exception as e:
            logger.debug(f"Failed to update session with Solana address: {type(e).__name__}")
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
