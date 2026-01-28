"""
Universal Email Manager - IMAP-based email access for any provider
Supports Gmail, Yahoo, Outlook, and custom domains
"""

import imaplib
import email
from email.header import decode_header
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import streamlit as st
from settings_manager import SettingsManager


class EmailManager:
    """Manage email access via IMAP for AI automation"""

    # Common IMAP servers
    IMAP_SERVERS = {
        "gmail.com": ("imap.gmail.com", 993),
        "yahoo.com": ("imap.mail.yahoo.com", 993),
        "outlook.com": ("outlook.office365.com", 993),
        "hotmail.com": ("outlook.office365.com", 993),
        "icloud.com": ("imap.mail.me.com", 993),
        "aol.com": ("imap.aol.com", 993),
    }

    @staticmethod
    def get_imap_server(email_address: str) -> tuple:
        """Get IMAP server and port for email provider"""
        domain = email_address.split("@")[-1].lower()
        return EmailManager.IMAP_SERVERS.get(domain, (f"imap.{domain}", 993))

    @staticmethod
    def save_email_credentials(user_id: str, email_address: str, password: str) -> bool:
        """Save encrypted email credentials to database"""
        try:
            # Test connection first
            imap_server, imap_port = EmailManager.get_imap_server(email_address)

            try:
                mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                mail.login(email_address, password)
                mail.logout()
            except imaplib.IMAP4.error as e:
                if "Application-specific password required" in str(e):
                    st.error("🔐 Gmail/Yahoo users: You need an **App Password**, not your regular password. See instructions below.")
                    return False
                else:
                    st.error(f"❌ Login failed: {e}")
                    return False
            except Exception as e:
                st.error(f"❌ Connection failed: {e}")
                return False

            # Save credentials encrypted
            success = SettingsManager.save_oauth_connection(
                user_id=user_id,
                provider="email",
                access_token=email_address,  # Store email as "access token"
                refresh_token=password,       # Store password as "refresh token"
                provider_user_id=email_address,
                scopes=["imap", "read"],
                expires_at=None
            )

            return success

        except Exception as e:
            st.error(f"Failed to save credentials: {e}")
            return False

    @staticmethod
    def get_email_connection(user_id: str) -> Optional[imaplib.IMAP4_SSL]:
        """Get authenticated IMAP connection"""
        try:
            # Get stored credentials
            connection = SettingsManager.get_oauth_connection(user_id, "email")
            if not connection or not connection.get("is_active"):
                return None

            email_address = connection["access_token"]
            password = connection["refresh_token"]

            # Connect to IMAP server
            imap_server, imap_port = EmailManager.get_imap_server(email_address)
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(email_address, password)

            return mail

        except Exception as e:
            st.error(f"Failed to connect to email: {e}")
            return None

    @staticmethod
    def search_recent_emails(
        user_id: str,
        query: str = "ALL",
        max_results: int = 10,
        time_range_minutes: int = 1440  # 24 hours default
    ) -> List[Dict[str, Any]]:
        """
        Search recent emails with time-based filtering

        Args:
            user_id: User ID
            query: IMAP search query (e.g., "UNSEEN", "FROM email@example.com")
            max_results: Maximum number of emails to return
            time_range_minutes: Only fetch emails from last N minutes

        Returns:
            List of email dicts with subject, from, date, snippet
        """
        mail = EmailManager.get_email_connection(user_id)
        if not mail:
            return []

        try:
            # Select inbox
            mail.select("inbox")

            # Calculate date filter (only recent emails)
            since_date = (datetime.now() - timedelta(minutes=time_range_minutes)).strftime("%d-%b-%Y")

            # Search with date filter
            search_query = f'(SINCE {since_date})'
            if query != "ALL":
                search_query = f'({query} SINCE {since_date})'

            status, messages = mail.search(None, search_query)

            if status != "OK":
                return []

            email_ids = messages[0].split()
            email_ids = email_ids[-max_results:]  # Get last N emails

            emails = []
            for email_id in reversed(email_ids):  # Newest first
                try:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")

                    if status != "OK":
                        continue

                    # Parse email
                    msg = email.message_from_bytes(msg_data[0][1])

                    # Get subject
                    subject = EmailManager._decode_header(msg.get("Subject", ""))

                    # Get from
                    from_header = EmailManager._decode_header(msg.get("From", ""))

                    # Get date
                    date_str = msg.get("Date", "")

                    # Get body snippet (first 300 chars)
                    body = EmailManager._get_email_body(msg)
                    snippet = body[:300] if body else ""

                    emails.append({
                        "subject": subject,
                        "from": from_header,
                        "date": date_str,
                        "snippet": snippet,
                        "body": body  # Full body if needed
                    })

                except Exception as e:
                    st.warning(f"Failed to parse email: {e}")
                    continue

            mail.logout()
            return emails

        except Exception as e:
            st.error(f"Failed to search emails: {e}")
            try:
                mail.logout()
            except:
                pass
            return []

    @staticmethod
    def extract_verification_code(text: str) -> Optional[str]:
        """Extract verification code from email text"""
        # Common patterns for verification codes
        patterns = [
            r'\b(\d{6})\b',  # 6-digit code
            r'\b(\d{4,8})\b',  # 4-8 digit code
            r'code[:\s]+([A-Z0-9]{4,8})',  # "code: XXXX"
            r'verification code[:\s]+([A-Z0-9]{4,8})',
            r'your code is[:\s]+([A-Z0-9]{4,8})',
            r'OTP[:\s]+([A-Z0-9]{4,8})',
            r'One-Time Password[:\s]+([A-Z0-9]{4,8})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def get_verification_code_from_recent_emails(
        user_id: str,
        from_domain: Optional[str] = None,
        time_range_minutes: int = 10
    ) -> Optional[str]:
        """
        Get verification code from recent emails

        Args:
            user_id: User ID
            from_domain: Optional - filter by sender domain (e.g., "porkbun.com")
            time_range_minutes: How far back to search (default 10 minutes)

        Returns:
            Verification code string or None
        """
        # Build search query
        query = "UNSEEN"  # Only unread emails
        if from_domain:
            query = f'FROM "{from_domain}"'

        # Search recent emails
        emails = EmailManager.search_recent_emails(
            user_id=user_id,
            query=query,
            max_results=5,
            time_range_minutes=time_range_minutes
        )

        # Extract code from each email
        for email_data in emails:
            # Check subject
            code = EmailManager.extract_verification_code(email_data.get("subject", ""))
            if code:
                return code

            # Check body
            code = EmailManager.extract_verification_code(email_data.get("snippet", ""))
            if code:
                return code

            # Check full body if needed
            code = EmailManager.extract_verification_code(email_data.get("body", ""))
            if code:
                return code

        return None

    @staticmethod
    def _decode_header(header: str) -> str:
        """Decode email header"""
        if not header:
            return ""

        decoded_parts = decode_header(header)
        decoded_str = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or "utf-8", errors="ignore")
            else:
                decoded_str += part

        return decoded_str

    @staticmethod
    def _get_email_body(msg) -> str:
        """Extract email body text"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except:
                body = ""

        return body


def show_email_connection_ui(user_id: str):
    """Show email connection UI in settings"""

    # Check if already connected
    connection = SettingsManager.get_oauth_connection(user_id, "email")

    if connection and connection.get("is_active"):
        st.success(f"✅ Connected: {connection.get('provider_user_id')}")
        st.markdown("<div style='font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #555;'>AI can use this email for automated signups and verification codes</div>", unsafe_allow_html=True)

        if st.button("🔌 Disconnect Email"):
            if SettingsManager.disconnect_account(user_id, "email"):
                st.success("Email disconnected!")
                st.rerun()
    else:
        st.info("🤖 **Enable AI Automation**: Connect your email so the AI can sign up for services and read verification codes automatically.")

        with st.expander("📧 Connect Email", expanded=True):
            email_address = st.text_input(
                "Email Address",
                placeholder="you@gmail.com",
                help="Your email address (Gmail, Yahoo, Outlook, etc.)"
            )

            password = st.text_input(
                "Password / App Password",
                type="password",
                placeholder="Your email password or app-specific password",
                help="For Gmail/Yahoo, use an App Password (see below)"
            )

            if st.button("💾 Save Email", type="primary"):
                if not email_address or not password:
                    st.error("Please enter both email and password")
                else:
                    with st.spinner("Testing connection..."):
                        success = EmailManager.save_email_credentials(user_id, email_address, password)

                    if success:
                        st.success("Email connected successfully")
                        st.toast("Email ready for AI automation")
                        st.rerun()

            # Instructions for app passwords
            st.divider()
            st.markdown("### 🔐 App Password Setup")

            with st.expander("Gmail Users - Get App Password"):
                st.markdown("""
                1. Go to [Google Account Security](https://myaccount.google.com/security)
                2. Enable **2-Step Verification** (if not already enabled)
                3. Go to **App passwords** section
                4. Select **Mail** and **Other (Custom name)**
                5. Copy the 16-character password
                6. Paste it above (no spaces)
                """)

            with st.expander("Yahoo Users - Get App Password"):
                st.markdown("""
                1. Go to [Yahoo Account Security](https://login.yahoo.com/account/security)
                2. Click **Generate app password**
                3. Select **Other App** → Name it "Chat Wallet"
                4. Copy the password
                5. Paste it above
                """)

            with st.expander("Outlook/Hotmail Users"):
                st.markdown("""
                Most Outlook accounts work with regular passwords.

                If you have 2FA enabled:
                1. Go to [Microsoft Account Security](https://account.microsoft.com/security)
                2. Create an **App password**
                3. Use that instead of your regular password
                """)
