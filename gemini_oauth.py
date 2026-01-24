"""
Gemini OAuth integration for AI chat using user's Google account

Users sign in with Google and use their own Gemini free tier quota.
No API keys needed for the app operator - completely free to run.
"""

import streamlit as st
from typing import Optional, Dict, Any
import os

# Google Auth libraries
try:
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

# Google Generative AI library
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from settings_manager import SettingsManager


class GeminiOAuth:
    """Handle Google OAuth for Gemini API access"""

    # OAuth scopes for Gemini API
    SCOPES = [
        'https://www.googleapis.com/auth/generative-language.retriever',  # Gemini API access
        'https://www.googleapis.com/auth/userinfo.email',  # Get user email
    ]

    @staticmethod
    def is_available() -> bool:
        """Check if Gemini OAuth dependencies are installed"""
        return GOOGLE_AUTH_AVAILABLE and GENAI_AVAILABLE

    @staticmethod
    def get_oauth_url(user_id: str, redirect_uri: str) -> Optional[str]:
        """Generate OAuth authorization URL for Gemini"""
        if not GOOGLE_AUTH_AVAILABLE:
            st.error("Google OAuth libraries not installed. Run: pip install google-auth google-auth-oauthlib google-generativeai")
            return None

        # Get OAuth credentials from environment
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

        if not client_id or not client_secret:
            st.error("Google OAuth credentials not configured. Add GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET to environment variables.")
            return None

        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=GeminiOAuth.SCOPES,
                redirect_uri=redirect_uri
            )

            # Generate authorization URL
            auth_url, state = flow.authorization_url(
                access_type='offline',  # Get refresh token
                include_granted_scopes='true',
                prompt='consent',  # Force consent to get refresh token
                state=f"gemini:{user_id}"  # Prefix to identify Gemini OAuth
            )

            return auth_url

        except Exception as e:
            st.error(f"Failed to generate OAuth URL: {e}")
            return None

    @staticmethod
    def handle_oauth_callback(code: str, redirect_uri: str, user_id: str) -> bool:
        """Handle OAuth callback and save tokens"""
        if not GOOGLE_AUTH_AVAILABLE:
            return False

        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

        if not client_id or not client_secret:
            return False

        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=GeminiOAuth.SCOPES,
                redirect_uri=redirect_uri
            )

            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Get user email from Google
            try:
                from googleapiclient.discovery import build
                service = build('oauth2', 'v2', credentials=credentials)
                user_info = service.userinfo().get().execute()
                provider_email = user_info.get('email')
            except Exception:
                provider_email = "google_user"

            # Calculate token expiry
            expires_at = None
            if credentials.expiry:
                expires_at = credentials.expiry.isoformat()

            # Save tokens to database
            success = SettingsManager.save_oauth_connection(
                user_id=user_id,
                provider="gemini",
                provider_user_id=provider_email,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                scopes=GeminiOAuth.SCOPES,
                expires_at=expires_at
            )

            return success

        except Exception as e:
            st.error(f"OAuth callback failed: {e}")
            return False

    @staticmethod
    def get_credentials(user_id: str) -> Optional[Credentials]:
        """Get valid OAuth credentials for a user"""
        if not GOOGLE_AUTH_AVAILABLE:
            return None

        # Get OAuth connection from database
        connection = SettingsManager.get_oauth_connection(user_id, "gemini")
        if not connection or not connection.get("is_active"):
            return None

        try:
            # Create credentials object
            credentials = Credentials(
                token=connection["access_token"],
                refresh_token=connection.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
                scopes=connection.get("scopes", GeminiOAuth.SCOPES)
            )

            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

                # Update tokens in database
                SettingsManager.save_oauth_connection(
                    user_id=user_id,
                    provider="gemini",
                    provider_user_id=connection.get("provider_user_id"),
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    scopes=connection.get("scopes", GeminiOAuth.SCOPES),
                    expires_at=credentials.expiry.isoformat() if credentials.expiry else None
                )

            return credentials

        except Exception as e:
            st.error(f"Failed to get Gemini credentials: {e}")
            return None

    @staticmethod
    def is_connected(user_id: str) -> bool:
        """Check if user has connected their Google account for Gemini"""
        connection = SettingsManager.get_oauth_connection(user_id, "gemini")
        return bool(connection and connection.get("is_active"))

    @staticmethod
    def get_connection_email(user_id: str) -> Optional[str]:
        """Get the email address of the connected Google account"""
        connection = SettingsManager.get_oauth_connection(user_id, "gemini")
        if connection and connection.get("is_active"):
            return connection.get("provider_user_id")
        return None

    @staticmethod
    def disconnect(user_id: str) -> bool:
        """Disconnect Google account from Gemini"""
        return SettingsManager.disconnect_account(user_id, "gemini")

    @staticmethod
    def get_llm_config(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get LLM config for a user using their OAuth credentials.
        Returns config dict if user has valid Gemini OAuth, None otherwise.
        """
        if not GeminiOAuth.is_connected(user_id):
            return None

        credentials = GeminiOAuth.get_credentials(user_id)
        if not credentials:
            return None

        return {
            "provider": "google_oauth",
            "model": "gemini-2.0-flash",  # Fast, capable, free tier
            "credentials": credentials,
            "using_free_tier": True,
            "using_oauth": True
        }


def show_gemini_connection_ui(user_id: str):
    """Show Gemini/Google connection UI"""

    if not GeminiOAuth.is_available():
        st.warning("Google AI libraries not installed")
        st.code("pip install google-auth google-auth-oauthlib google-generativeai")
        return

    # Check if already connected
    if GeminiOAuth.is_connected(user_id):
        email = GeminiOAuth.get_connection_email(user_id)
        st.success(f"Connected: {email}")
        st.caption("Using your Google account's free Gemini quota")

        if st.button("Disconnect Google"):
            if GeminiOAuth.disconnect(user_id):
                st.success("Disconnected!")
                st.rerun()
    else:
        st.info("Sign in with Google to start chatting (free)")

        if st.button("Sign in with Google", type="primary"):
            # Get redirect URI
            app_url = os.getenv("APP_URL", "http://localhost:8501")
            redirect_uri = f"{app_url}/oauth/callback"

            # Generate OAuth URL
            auth_url = GeminiOAuth.get_oauth_url(user_id, redirect_uri)

            if auth_url:
                st.markdown(f"[Click here to sign in with Google]({auth_url})")
                st.caption("You'll use your own Google account's free Gemini quota")
