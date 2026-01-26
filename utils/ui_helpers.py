"""
UI Helper utilities for consistent user experience
"""

import streamlit as st
from typing import Optional
from utils.logger import logger


def show_error(title: str, message: str, next_step: Optional[str] = None, log_details: Optional[str] = None):
    """
    Display a user-friendly error message with optional guidance.

    Args:
        title: Short error title (e.g., "Could not send")
        message: User-friendly explanation
        next_step: Optional actionable suggestion
        log_details: Optional technical details for server-side logging only
    """
    if log_details:
        logger.error(f"{title}: {log_details}")

    st.error(f"**{title}**  \n{message}")
    if next_step:
        st.info(f"**Try this:** {next_step}")


def show_success(title: str, message: str, details: Optional[str] = None):
    """
    Display a success message with optional details.

    Args:
        title: Short success title (e.g., "Transaction sent")
        message: User-friendly explanation
        details: Optional additional info (shown as caption)
    """
    st.success(f"**{title}**  \n{message}")
    if details:
        st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 11px; color: #555;'>{details}</div>", unsafe_allow_html=True)


def show_warning(message: str, suggestion: Optional[str] = None):
    """
    Display a warning with optional suggestion.

    Args:
        message: Warning message
        suggestion: Optional actionable suggestion
    """
    if suggestion:
        st.warning(f"{message}  \n**Suggestion:** {suggestion}")
    else:
        st.warning(message)


def show_empty_state(title: str, description: str, action_label: Optional[str] = None):
    """
    Display an empty state with guidance.

    Args:
        title: What's empty (e.g., "No transactions yet")
        description: How to populate it
        action_label: Optional action button text (returns True if clicked)
    """
    st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 11px; color: #555;'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 11px; color: #444;'>{description}</div>", unsafe_allow_html=True)
    if action_label:
        return st.button(action_label, type="primary")
    return False
