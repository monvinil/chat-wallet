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
    def _set_cookie_js(name: str, value: str, days: int = 30):
        """Set cookie using direct JavaScript injection (more reliable)"""
        js_code = f"""
        <script>
        (function() {{
            var date = new Date();
            date.setTime(date.getTime() + ({days} * 24 * 60 * 60 * 1000));
            var expires = "expires=" + date.toUTCString();
            document.cookie = "{name}={value};" + expires + ";path=/;SameSite=Lax";
            console.log("[Session] Cookie set via JS: {name}=" + "{value}".substring(0, 8) + "...");
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
        js_code = f"""
        <script>
        document.cookie = "{name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;";
        console.log("[Session] Cookie deleted: {name}");
        </script>
        """
        components.html(js_code, height=0)

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
        """Save session token to browser cookie using multiple methods for reliability"""
        print(f"[Session] Saving cookie with token={session_token[:8]}...")

        # Method 1: Direct JavaScript injection (most reliable in production)
        try:
            SessionManager._set_cookie_js(
                SessionManager.COOKIE_NAME,
                session_token,
                SessionManager.SESSION_EXPIRY_DAYS
            )
            print(f"[Session] Cookie set via JS successfully")
        except Exception as e:
            print(f"[Session] JS cookie set failed: {e}")

        # Method 2: stx cookie manager (backup)
        try:
            cookie_manager = SessionManager.get_cookie_manager()
            if cookie_manager:
                cookie_manager.set(
                    SessionManager.COOKIE_NAME,
                    session_token,
                    expires_at=datetime.now() + timedelta(days=SessionManager.SESSION_EXPIRY_DAYS)
                )
                print(f"[Session] Cookie set via stx successfully")
        except Exception as e:
            print(f"[Session] stx cookie set failed: {e}")

        # Also store in session state as ultimate fallback
        st.session_state._session_token_backup = session_token

    @staticmethod
    def get_session_cookie() -> Optional[str]:
        """Get session token from browser cookie"""
        # Try stx cookie manager first (can read JS-set cookies)
        cookie_manager = SessionManager.get_cookie_manager()
        if cookie_manager:
            # IMPORTANT: Must call get_all() to refresh cookies from browser!
            # The CookieManager caches cookies on init, and get() uses the cache.
            # On first render after refresh, the cache is empty (default={}).
            # Calling get_all() fetches fresh cookies from the browser.
            # Use unique key to avoid Streamlit duplicate key error
            all_cookies = cookie_manager.get_all(key="session_get_all")
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
        """Save wallet decryption key to session cookie (for auto-unlock on refresh)"""
        # Use session cookie (no expiry) - cleared when browser closes
        # This keeps wallet unlocked across page refreshes but not browser restarts
        try:
            import base64
            # Encode key for cookie storage
            encoded_key = base64.b64encode(wallet_key.encode()).decode()
            print(f"[Session] Saving wallet key cookie, encoded length: {len(encoded_key)}")

            # Method 1: Direct JavaScript (session cookie - no expiry)
            js_code = f"""
            <script>
            document.cookie = "chat_wallet_key={encoded_key};path=/;SameSite=Lax";
            console.log("[Session] Wallet key cookie set via JS");
            </script>
            """
            components.html(js_code, height=0)

            # Method 2: stx cookie manager (backup, with 1 day expiry for persistence)
            cookie_manager = SessionManager.get_cookie_manager()
            if cookie_manager:
                cookie_manager.set(
                    "chat_wallet_key",
                    encoded_key,
                    expires_at=datetime.now() + timedelta(days=1),
                    key="set_wallet_key"
                )
                print(f"[Session] Wallet key cookie set via stx")

        except Exception as e:
            print(f"[Session] Failed to save wallet key: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def get_wallet_key() -> Optional[str]:
        """Get wallet decryption key from cookie (for auto-unlock)"""
        try:
            cookie_manager = SessionManager.get_cookie_manager()
            if cookie_manager:
                import base64
                all_cookies = cookie_manager.get_all(key="wallet_key_get_all")
                encoded_key = all_cookies.get("chat_wallet_key")
                if encoded_key:
                    return base64.b64decode(encoded_key.encode()).decode()
        except Exception as e:
            print(f"[Session] Failed to get wallet key: {e}")
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

                # Try to auto-unlock with saved wallet key (from session cookie)
                saved_key = SessionManager.get_wallet_key()
                if saved_key:
                    # Key was saved - auto-unlock wallet
                    st.session_state.wallet_key = saved_key
                    st.session_state.wallet_locked = False
                    if debug:
                        print(f"[Session] Auto-unlocked wallet with saved key")
                else:
                    # No saved key - wallet stays locked
                    st.session_state.wallet_locked = True
                    if debug:
                        print(f"[Session] No saved key - wallet locked")
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
