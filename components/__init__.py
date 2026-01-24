"""
UI Components for Chat Wallet
Modular UI components extracted from app.py
"""

from components.sidebar import (
    sidebar,
    render_sidebar_footer,
    render_transaction_history
)
from components.modals import (
    deposit_modal,
    send_modal,
    seed_phrase_modal,
    generate_qr,
    show_success_animation
)
from components.chat import (
    chat_interface,
    render_action_deck,
    render_modules,
    render_modules_preview,
    render_header,
    render_industrial_card
)

__all__ = [
    # Sidebar
    "sidebar",
    "render_sidebar_footer",
    "render_transaction_history",
    # Modals
    "deposit_modal",
    "send_modal",
    "seed_phrase_modal",
    "generate_qr",
    "show_success_animation",
    # Chat
    "chat_interface",
    "render_action_deck",
    "render_modules",
    "render_modules_preview",
    "render_header",
    "render_industrial_card",
]
