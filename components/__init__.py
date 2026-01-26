"""
UI Components for Chat Wallet
Modular UI components extracted from app.py
"""

from components.sidebar import (
    sidebar,
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
    render_action_strip,
    render_action_deck,  # Alias for backwards compatibility
    render_modules,
    render_modules_preview,
    render_header,
    render_luxe_card,
    render_fashion_card,  # Alias for backwards compatibility
)

__all__ = [
    # Sidebar
    "sidebar",
    "render_transaction_history",
    # Modals
    "deposit_modal",
    "send_modal",
    "seed_phrase_modal",
    "generate_qr",
    "show_success_animation",
    # Chat - V9
    "chat_interface",
    "render_action_strip",
    "render_modules",
    "render_modules_preview",
    "render_header",
    "render_luxe_card",
    # Chat - Backwards compatibility aliases
    "render_action_deck",
    "render_fashion_card",
]
