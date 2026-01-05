"""
Email tools for AI agent - LangChain compatible
"""

from langchain_core.tools import tool
from typing import Optional
from email_manager import EmailManager
import streamlit as st


@tool
def get_verification_code(from_domain: Optional[str] = None) -> str:
    """
    Get verification code from recent emails (last 10 minutes).

    Useful when signing up for services that send email verification codes.
    The AI should wait 30-60 seconds after submitting a form before calling this.

    Args:
        from_domain: Optional - sender domain to filter by (e.g., "porkbun.com", "amazon.com")

    Returns:
        The verification code string, or error message if not found
    """
    try:
        user_id = st.session_state.get("wallet_address")
        if not user_id:
            return "Error: User not logged in"

        code = EmailManager.get_verification_code_from_recent_emails(
            user_id=user_id,
            from_domain=from_domain,
            time_range_minutes=10
        )

        if code:
            return f"Verification code: {code}"
        else:
            return "No verification code found in recent emails. The email might not have arrived yet. Try waiting 30 seconds and call this tool again."

    except Exception as e:
        return f"Error fetching verification code: {e}"


@tool
def search_recent_emails(query: str = "ALL", max_results: int = 5) -> str:
    """
    Search recent emails from the last 24 hours.

    Use this to find receipts, order confirmations, or specific information from emails.

    Args:
        query: Search query - can be:
            - "ALL" (all recent emails)
            - "UNSEEN" (only unread emails)
            - 'FROM "sender@example.com"' (emails from specific sender)
            - 'SUBJECT "Order Confirmation"' (emails with subject)
        max_results: Maximum number of emails to return (default 5, max 10)

    Returns:
        Formatted list of recent emails with subject, from, date, and snippet
    """
    try:
        user_id = st.session_state.get("wallet_address")
        if not user_id:
            return "Error: User not logged in"

        # Limit max results
        max_results = min(max_results, 10)

        emails = EmailManager.search_recent_emails(
            user_id=user_id,
            query=query,
            max_results=max_results,
            time_range_minutes=1440  # 24 hours
        )

        if not emails:
            return "No emails found matching your query in the last 24 hours."

        # Format results
        result = f"Found {len(emails)} email(s):\n\n"

        for i, email_data in enumerate(emails, 1):
            result += f"Email {i}:\n"
            result += f"From: {email_data.get('from', 'Unknown')}\n"
            result += f"Subject: {email_data.get('subject', 'No subject')}\n"
            result += f"Date: {email_data.get('date', 'Unknown')}\n"
            result += f"Preview: {email_data.get('snippet', '')[:200]}...\n"
            result += "\n---\n\n"

        return result

    except Exception as e:
        return f"Error searching emails: {e}"


@tool
def check_email_connected() -> str:
    """
    Check if user has connected an email for AI automation.

    Returns:
        Status message about email connection
    """
    try:
        user_id = st.session_state.get("wallet_address")
        if not user_id:
            return "Error: User not logged in"

        from settings_manager import SettingsManager
        connection = SettingsManager.get_oauth_connection(user_id, "email")

        if connection and connection.get("is_active"):
            email = connection.get("provider_user_id", "Unknown")
            return f"Email connected: {email}. You can use email tools for automation."
        else:
            return "No email connected. Ask the user to connect an email in Settings → Connected Accounts to enable email automation features."

    except Exception as e:
        return f"Error checking email connection: {e}"


def get_email_tools():
    """Get list of email tools for AI agent"""
    return [
        get_verification_code,
        search_recent_emails,
        check_email_connected
    ]
