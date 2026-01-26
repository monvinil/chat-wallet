"""
Gmail OAuth integration for reading emails and verification codes
"""

import streamlit as st
from typing import Optional, Dict, Any
import os
from datetime import datetime, timedelta

# Gmail OAuth will require google-auth and google-api-python-client
try:
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

from settings_manager import SettingsManager


class GmailOAuth:
    """Handle Gmail OAuth flow and API calls"""

    # OAuth scopes we need
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
        'https://www.googleapis.com/auth/userinfo.email',  # Get user email
    ]

    @staticmethod
    def get_oauth_url(user_id: str, redirect_uri: str) -> Optional[str]:
        """Generate OAuth authorization URL"""
        if not GOOGLE_AUTH_AVAILABLE:
            st.error("Google OAuth libraries not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client")
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
                scopes=GmailOAuth.SCOPES,
                redirect_uri=redirect_uri
            )

            # Generate authorization URL
            auth_url, state = flow.authorization_url(
                access_type='offline',  # Get refresh token
                include_granted_scopes='true',
                prompt='consent',  # Force consent screen to get refresh token
                state=user_id  # Pass user_id as state
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
                scopes=GmailOAuth.SCOPES,
                redirect_uri=redirect_uri
            )

            # Exchange code for tokens
            flow.fetch_token(code=code)

            credentials = flow.credentials

            # Get user email from Google
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            provider_email = user_info.get('email')

            # Calculate token expiry
            expires_at = None
            if credentials.expiry:
                expires_at = credentials.expiry.isoformat()

            # Save tokens to database
            success = SettingsManager.save_oauth_connection(
                user_id=user_id,
                provider="gmail",
                provider_user_id=provider_email,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                scopes=GmailOAuth.SCOPES,
                expires_at=expires_at
            )

            return success

        except Exception as e:
            st.error(f"OAuth callback failed: {e}")
            return False

    @staticmethod
    def get_gmail_service(user_id: str):
        """Get authenticated Gmail API service"""
        if not GOOGLE_AUTH_AVAILABLE:
            return None

        # Get OAuth connection from database
        connection = SettingsManager.get_oauth_connection(user_id, "gmail")
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
                scopes=connection.get("scopes", GmailOAuth.SCOPES)
            )

            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

                # Update tokens in database
                SettingsManager.save_oauth_connection(
                    user_id=user_id,
                    provider="gmail",
                    provider_user_id=connection.get("provider_user_id"),
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    scopes=connection.get("scopes", GmailOAuth.SCOPES),
                    expires_at=credentials.expiry.isoformat() if credentials.expiry else None
                )

            # Build and return Gmail service
            service = build('gmail', 'v1', credentials=credentials)
            return service

        except Exception as e:
            st.error(f"Failed to get Gmail service: {e}")
            return None

    @staticmethod
    def search_recent_emails(user_id: str, query: str = "is:unread", max_results: int = 10) -> list:
        """Search recent emails"""
        service = GmailOAuth.get_gmail_service(user_id)
        if not service:
            return []

        try:
            # Search for messages
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            # Get full message details
            emails = []
            for msg in messages:
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                # Extract headers
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

                # Extract body (simplified - just get snippet)
                snippet = message.get('snippet', '')

                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'from': from_email,
                    'date': date,
                    'snippet': snippet,
                    'full_message': message
                })

            return emails

        except Exception as e:
            st.error(f"Failed to search emails: {e}")
            return []

    @staticmethod
    def extract_verification_code(email_body: str) -> Optional[str]:
        """Extract verification code from email body using common patterns"""
        import re

        # Common patterns for verification codes
        patterns = [
            r'\b(\d{6})\b',  # 6-digit code
            r'\b(\d{4,8})\b',  # 4-8 digit code
            r'code:\s*([A-Z0-9]{4,8})',  # "code: XXXX"
            r'verification code:\s*([A-Z0-9]{4,8})',
            r'your code is:\s*([A-Z0-9]{4,8})',
        ]

        for pattern in patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                return match.group(1)

        return None


def show_gmail_connection_ui(user_id: str):
    """Show Gmail connection UI in settings"""

    # Check if already connected
    connection = SettingsManager.get_oauth_connection(user_id, "gmail")

    if connection and connection.get("is_active"):
        st.success(f"✅ Connected: {connection.get('provider_user_id')}")
        st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 11px; color: #555;'>Connected on {connection.get('created_at', '')[:10]}</div>", unsafe_allow_html=True)

        if st.button("🔌 Disconnect Gmail"):
            if SettingsManager.disconnect_account(user_id, "gmail"):
                st.success("Gmail disconnected!")
                st.rerun()
    else:
        st.info("Connect your Gmail to enable automated email reading (verification codes, receipts, etc.)")

        # Show OAuth button
        if st.button("📧 Connect Gmail", type="primary"):
            # Get redirect URI (Railway URL or localhost)
            app_url = os.getenv("APP_URL", "http://localhost:8501")
            redirect_uri = f"{app_url}/oauth/callback"

            # Generate OAuth URL
            auth_url = GmailOAuth.get_oauth_url(user_id, redirect_uri)

            if auth_url:
                st.markdown(f"[Click here to authorize Gmail →]({auth_url})")
                st.markdown("<div style='font-family: JetBrains Mono; font-size: 11px; color: #555;'>You'll be redirected back after authorization</div>", unsafe_allow_html=True)
