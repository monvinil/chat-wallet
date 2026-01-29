"""
Chat Interface Component
V12 Design: "Liquid Silver" - Floating Void Aesthetic
"""

import html
import streamlit as st
from chain_utils import ChainUtils
from langchain_core.callbacks import BaseCallbackHandler
from decision_logger import log_ai_decision, DecisionLogger
from utils.logger import logger


def _format_tool_action(tool_name: str) -> str:
    """Convert tool name to human-readable action label."""
    tool_labels = {
        # Transactions
        "preview_transaction": "Prepared transfer",
        "execute_transaction": "Sent USDC",
        "get_balance": "Checked balance",
        # Yield
        "get_yield_status": "Checked yield",
        "preview_yield_deposit": "Prepared deposit",
        "execute_yield_deposit": "Deposited to earn",
        "preview_yield_withdrawal": "Prepared withdrawal",
        "execute_yield_withdrawal": "Withdrew funds",
        "get_current_apy": "Checked rates",
        # Gift cards
        "search_gift_cards": "Searched gift cards",
        "get_gift_card_details": "Found gift card",
        "purchase_gift_card": "Purchased gift card",
        "pay_bill_with_giftcard": "Paid bill",
        # Merchants
        "search_crypto_merchants": "Found merchants",
        "buy_domain_with_crypto": "Domain purchase",
        "subscribe_vpn_with_crypto": "VPN subscription",
        # Scheduler
        "create_scheduled_transfer": "Created automation",
        "list_scheduled_tasks": "Listed automations",
        "cancel_scheduled_task": "Cancelled automation",
        # Email
        "check_email_connected": "Checked email",
        "get_verification_code": "Got email code",
        "search_recent_emails": "Searched emails",
    }
    return tool_labels.get(tool_name, tool_name.replace("_", " ").title())


def _render_action_indicator(tool_calls: list) -> str:
    """Render a subtle action indicator showing what the AI did."""
    if not tool_calls:
        return ""

    # Get unique tool names (first occurrence only)
    seen = set()
    unique_tools = []
    for tc in tool_calls:
        tool_name = tc.get("tool", "")
        if tool_name and tool_name not in seen:
            seen.add(tool_name)
            unique_tools.append(tool_name)

    if not unique_tools:
        return ""

    # Format as human-readable actions
    actions = [_format_tool_action(t) for t in unique_tools[:3]]  # Max 3
    action_text = " → ".join(actions)

    return f"""
    <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.04);">
        <span style="font-family: 'Inter', sans-serif; font-size: 11px; color: #555;">
            {action_text}
        </span>
    </div>
    """


def _ensure_string(content) -> str:
    """Convert message content to string, handling list format from LangChain."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Extract text from content blocks (multi-modal/tool responses)
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
        return ''.join(text_parts)
    return str(content) if content else ''


# === STREAMING CALLBACK HANDLER ===
class StreamlitTokenHandler(BaseCallbackHandler):
    """Callback handler that streams tokens to a Streamlit container in real-time."""

    def __init__(self, container):
        self.container = container
        self.text = ""
        self.tool_status = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when LLM produces a new token."""
        self.text += token
        # Update container with current text + cursor
        self._render()

    def on_tool_start(self, serialized, input_str, **kwargs) -> None:
        """Called when a tool starts executing."""
        tool_name = html.escape(serialized.get("name", "tool"))
        self.tool_status = f"⚡ {tool_name}..."
        self._render()

    def on_tool_end(self, output, **kwargs) -> None:
        """Called when a tool finishes."""
        self.tool_status = ""
        self._render()

    def _render(self):
        """Render current state to the container."""
        # Show tool status if active - more prominent styling
        status_html = ""
        if self.tool_status:
            status_html = f'''
            <div style="
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                color: #22c55e;
                background: rgba(34,197,94,0.1);
                padding: 4px 10px;
                border-radius: 4px;
                margin-bottom: 12px;
                letter-spacing: 0.02em;
            ">
                <span style="animation: pulse 1s ease-in-out infinite;">●</span>
                {self.tool_status}
            </div>
            <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.4; }}
            }}
            </style>
            '''

        # Show text with blinking cursor
        cursor = "▌" if not self.tool_status else ""
        text_html = f'<div style="color: #ccc; font-family: \'Inter\', -apple-system, sans-serif; font-weight: 300; font-size: 15px; line-height: 1.7;">{html.escape(self.text)}{cursor}</div>'

        self.container.markdown(status_html + text_html, unsafe_allow_html=True)

    def get_final_text(self) -> str:
        """Get the complete text without cursor."""
        return self.text


# === PENDING TRANSACTION CARD ===
def _render_pending_transaction_card():
    """Render a transaction preview card if one is pending approval"""
    preview = st.session_state.get("_pending_tx_preview")
    if not preview or preview.get("status") != "pending_approval":
        return

    from design_system import DS

    st.markdown(f"""
    <style>
    .tx-card {{
        background: {DS.colors.BG_GLASS};
        border: 1px solid {DS.colors.BORDER_GLASS};
        border-radius: {DS.radius.LG};
        padding: {DS.spacing.LG};
        margin: {DS.spacing.MD} 0;
    }}
    .tx-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: {DS.spacing.MD};
        padding-bottom: {DS.spacing.SM};
        border-bottom: 1px solid {DS.colors.BORDER_HAIRLINE};
    }}
    .tx-action {{
        font-family: {DS.typography.FONT_MONO};
        font-size: {DS.typography.SIZE_XS};
        color: {DS.colors.TEXT_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}
    .tx-network {{
        font-family: {DS.typography.FONT_MONO};
        font-size: {DS.typography.SIZE_XS};
        color: {DS.colors.ACCENT_SUCCESS};
        background: rgba(34,197,94,0.1);
        padding: 4px 8px;
        border-radius: {DS.radius.SM};
    }}
    .tx-amount {{
        font-family: {DS.typography.FONT_SANS};
        font-size: 28px;
        font-weight: 300;
        color: {DS.colors.TEXT_PRIMARY};
        letter-spacing: -0.02em;
        margin-bottom: {DS.spacing.MD};
    }}
    .tx-row {{
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
    }}
    .tx-label {{
        font-family: {DS.typography.FONT_MONO};
        font-size: {DS.typography.SIZE_SM};
        color: {DS.colors.TEXT_MUTED};
    }}
    .tx-value {{
        font-family: {DS.typography.FONT_MONO};
        font-size: {DS.typography.SIZE_SM};
        color: {DS.colors.TEXT_SECONDARY};
    }}
    .tx-value.address {{
        font-size: 11px;
        max-width: 180px;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .tx-divider {{
        height: 1px;
        background: {DS.colors.BORDER_HAIRLINE};
        margin: {DS.spacing.SM} 0;
    }}
    .tx-total {{
        font-family: {DS.typography.FONT_SANS};
        font-size: {DS.typography.SIZE_LG};
        font-weight: 600;
        color: {DS.colors.TEXT_PRIMARY};
    }}
    </style>
    <div class="tx-card">
        <div class="tx-header">
            <span class="tx-action">{preview.get('action', 'Send USDC')}</span>
            <span class="tx-network">{preview.get('network', 'Base')}</span>
        </div>
        <div class="tx-amount">{preview.get('amount', '$0.00')}</div>
        <div class="tx-row">
            <span class="tx-label">To</span>
            <span class="tx-value address">{preview.get('to_full_address', preview.get('to', ''))}</span>
        </div>
        <div class="tx-row">
            <span class="tx-label">Fee</span>
            <span class="tx-value">{preview.get('fee', '$0.00')}</span>
        </div>
        <div class="tx-row">
            <span class="tx-label">Time</span>
            <span class="tx-value">{preview.get('estimated_time', '~3-5 sec')}</span>
        </div>
        <div class="tx-divider"></div>
        <div class="tx-row">
            <span class="tx-label">Total</span>
            <span class="tx-value tx-total">{preview.get('total_cost', '$0.00')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Approval buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("CANCEL", key="tx_cancel", use_container_width=True):
            st.session_state._pending_tx_preview = None
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Transaction cancelled."
            })
            st.rerun()
    with col2:
        if st.button("APPROVE", key="tx_approve", type="primary", use_container_width=True):
            # Store approval and let user confirm via chat
            st.session_state._tx_approved = preview
            st.session_state._pending_tx_preview = None
            st.session_state.messages.append({
                "role": "user",
                "content": "Yes, send it."
            })
            st.rerun()


# === SKELETON LOADING STATES ===
def _inject_chat_skeleton_css():
    """Inject CSS for skeleton loading animations"""
    st.markdown("""
    <style>
    @keyframes skeleton-shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    .skeleton {
        background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%);
        background-size: 200% 100%;
        animation: skeleton-shimmer 1.5s ease-in-out infinite;
        border-radius: 4px;
    }
    .skeleton-card {
        height: 96px;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    </style>
    """, unsafe_allow_html=True)


def render_pulse_deck_skeleton(count: int = 3):
    """Render skeleton placeholder for pulse deck cards"""
    _inject_chat_skeleton_css()
    cols = st.columns(count)
    for i in range(count):
        with cols[i]:
            st.markdown("""
            <div class="skeleton skeleton-card"></div>
            """, unsafe_allow_html=True)


def render_message_skeleton():
    """Render skeleton placeholder for chat message"""
    st.markdown("""
    <div style="padding: 16px 0;">
        <div class="skeleton" style="height: 14px; width: 80%; margin-bottom: 8px;"></div>
        <div class="skeleton" style="height: 14px; width: 60%; margin-bottom: 8px;"></div>
        <div class="skeleton" style="height: 14px; width: 70%;"></div>
    </div>
    """, unsafe_allow_html=True)


# --- VISUAL: FLOATING DATA ---
def render_fashion_card(label, value, tag=None, tag_color=None):
    """Minimalist data point floating in space."""
    color = tag_color or "#444"
    st.markdown(f"""
    <div style="padding: 12px 0;">
        <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #444; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.1em;">{label}</div>
        <div style="font-family: 'Inter', -apple-system, sans-serif; font-size: 18px; font-weight: 400; color: white; letter-spacing: -0.02em;">
            {value} {f'<span style="font-size: 12px; color: {color}; margin-left: 4px;">{tag}</span>' if tag else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- HEADER: MAGAZINE ---
def render_header():
    """Magazine-style minimal header with optional balance display."""
    from design_system import enhanced_ui

    # Inject micro-interactions CSS globally
    enhanced_ui.inject_micro_interactions()

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        <div style="margin-top: 24px;">
            <h1 style="font-size: 28px; margin: 0; font-weight: 500; letter-spacing: -0.04em; text-transform: none !important;">USDChat</h1>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        # Show balance if wallet connected, otherwise show status
        if st.session_state.get("wallet_address") and not st.session_state.get("wallet_locked", False):
            try:
                from direct_tx import get_direct_executor
                executor = get_direct_executor("arc-testnet")
                balance = float(executor.get_usdc_balance(st.session_state.wallet_address))
                st.markdown(f"""
                <div style="text-align: right; margin-top: 24px;">
                    <div style="font-family: 'Inter', -apple-system, sans-serif; font-size: 24px; font-weight: 300; color: #f4f4f5; letter-spacing: -0.02em;">${balance:,.2f}</div>
                    <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #52525b; text-transform: uppercase; letter-spacing: 0.05em;">USDC</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.markdown("""
                <div style="text-align: right; margin-top: 28px;">
                    <span style="font-family: 'JetBrains Mono'; font-size: 11px; color: #22c55e; background: rgba(34,197,94,0.1); padding: 6px 12px; border-radius: 10px;">● ONLINE</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: right; margin-top: 28px;">
                <span style="font-family: 'JetBrains Mono'; font-size: 11px; color: #fff; background: rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 10px;">ONLINE</span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


# --- THE PULSE DECK (V22: Cupertino White / True Apple Style) ---
def render_pulse_deck():
    """
    V22: Cupertino White - white text on vibrant mesh gradients.
    - Spotlight (first card): Pure white titanium with dark text
    - Perks (cards 2-3): Saturated mesh gradients with WHITE text + shadow lift
    - Text shadows make white text readable on bright backgrounds
    """

    # === BRAND DEFINITIONS: V22 Cupertino White with Mesh Gradients ===
    BRANDS = {
        "spotify": {
            "icon": "https://api.iconify.design/simple-icons/spotify.svg",
            # Matte dark glass - matches AI card
            "bg": "rgba(255,255,255,0.05)",
            "border": "none",
            "shadow": "none",
            "accent": "#1ed760",  # Spotify green for progress bar
            "text_color": "#FFFFFF",
            "sub_color": "rgba(255,255,255,0.6)",
            "icon_filter": "brightness(0) invert(1) opacity(0.8)",
            "text_shadow": "none",
        },
        "netflix": {
            "icon": "https://api.iconify.design/simple-icons/netflix.svg",
            # Matte dark glass - matches AI card
            "bg": "rgba(255,255,255,0.05)",
            "border": "none",
            "shadow": "none",
            "accent": "#e50914",  # Netflix red for progress bar
            "text_color": "#FFFFFF",
            "sub_color": "rgba(255,255,255,0.6)",
            "icon_filter": "brightness(0) invert(1) opacity(0.8)",
            "text_shadow": "none",
        },
        "ai": {
            "icon": "https://api.iconify.design/mdi/robot-outline.svg",
            # Matte dark glass - no border
            "bg": "rgba(255,255,255,0.05)",
            "border": "none",
            "shadow": "none",
            "accent": "#1ed760",  # Green accent for AI status
            "text_color": "#FFFFFF",
            "sub_color": "rgba(255,255,255,0.6)",
            "icon_filter": "brightness(0) invert(1) opacity(0.8)",
            "text_shadow": "none",
        },
        "system": {
            "icon": "https://api.iconify.design/mdi/chart-line.svg",
            "bg": "#FFFFFF",
            "shadow": "0 4px 12px rgba(0,0,0,0.15)",
            "accent": "#000000",
            "text_color": "#000000",
            "sub_color": "#8e8e93",
            "icon_filter": "brightness(0)",
            "text_shadow": "none",
        },
        "yield": {
            "icon": "https://api.iconify.design/mdi/trending-up.svg",
            "bg": "rgba(255,255,255,0.05)",
            "border": "none",
            "shadow": "none",
            "accent": "#22c55e",  # Green for yield/growth
            "text_color": "#FFFFFF",
            "sub_color": "rgba(255,255,255,0.6)",
            "icon_filter": "brightness(0) invert(1) opacity(0.8)",
            "text_shadow": "none",
        },
        "automation": {
            "icon": "https://api.iconify.design/mdi/robot-outline.svg",
            "bg": "rgba(255,255,255,0.05)",
            "border": "none",
            "shadow": "none",
            "accent": "#8b5cf6",  # Purple for automation
            "text_color": "#FFFFFF",
            "sub_color": "rgba(255,255,255,0.6)",
            "icon_filter": "brightness(0) invert(1) opacity(0.8)",
            "text_shadow": "none",
        },
    }

    # === DATA SOURCES (mock - replace with real queries) ===
    active_tasks = []  # TODO: Pull from pending_approvals table

    perks = [
        {"brand": "spotify", "progress": 75, "target": 100, "reward": "1 Mo Free", "spent": 75},
        {"brand": "netflix", "progress": 32, "target": 100, "reward": "1 Mo Free", "spent": 32},
    ]

    # === SLOT BUILDER ===
    slots = []

    # Slot 1: AI Data card - connected to real user settings
    from settings_manager import SettingsManager
    from free_tier import FreeTier

    user_id = st.session_state.get("user_id")
    llm_config = SettingsManager.get_llm_config(user_id) if user_id else {}

    ai_brand = BRANDS["ai"]

    # Get provider display name - only show if user has configured a key
    provider_names = {"anthropic": "Claude", "google": "Gemini", "openai": "GPT-4o"}

    # Get last AI action from session (lightweight - no DB query)
    last_action = None
    messages = st.session_state.get("messages", [])
    if messages:
        # Find last assistant message with tool calls (reverse search)
        for msg in reversed(messages[-10:]):  # Check last 10 messages
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                # Simple heuristic: check for action keywords
                if any(word in content.lower() for word in ["sent", "bought", "deposited", "checked", "scheduled"]):
                    # Extract first sentence as action summary
                    first_sentence = content.split('.')[0][:40]
                    if len(first_sentence) > 35:
                        first_sentence = first_sentence[:35] + "..."
                    last_action = first_sentence
                    break

    # Get tier and usage info
    if not llm_config.get("api_key"):
        # No key at all - show setup needed
        ai_provider = "Not Set"
        ai_tier = "Setup"
        ai_sub = "Add API key"
    elif llm_config.get("using_free_tier"):
        # Using app's free tier (Google Gemini - free)
        remaining = FreeTier.get_remaining(user_id) if user_id else 0
        total = 50  # FREE_TIER_MESSAGES
        ai_provider = "Gemini"  # Free tier uses Gemini
        ai_tier = "Free"
        ai_sub = f"{remaining}/{total} msgs" if not last_action else last_action
    else:
        # User has their own key - show their provider
        ai_provider = provider_names.get(llm_config.get("provider", ""), "AI")
        ai_tier = "Pro"
        ai_sub = "Your key" if not last_action else last_action

    slots.append({
        "mode": "ai",
        "title": "YOUR AI",
        "main": ai_provider,
        "sub": f"{ai_tier} · {ai_sub}" if not last_action else ai_sub,
        "bg": ai_brand["bg"],
        "border": ai_brand.get("border", "none"),
        "shadow": ai_brand["shadow"],
        "accent": ai_brand["accent"],
        "text_color": ai_brand["text_color"],
        "sub_color": ai_brand["sub_color"],
        "icon_filter": ai_brand["icon_filter"],
        "text_shadow": ai_brand["text_shadow"],
        "spotlight": False,
        "icon": ai_brand["icon"],
        "brand_key": "ai",
    })

    # Slot 2: Treasury card (SPOTLIGHT - shows balance + treasury health)
    usdc_balance = 0.00
    yield_earnings = 0.00
    yield_apy = 0.0
    active_automations = 0

    if st.session_state.get("wallet_address"):
        try:
            from direct_tx import get_direct_executor
            executor = get_direct_executor("arc-testnet")
            usdc_balance = float(executor.get_usdc_balance(st.session_state.wallet_address))
        except Exception:
            pass

        # Check yield deposits
        try:
            from aave_client import get_yield_summary
            yield_info = get_yield_summary(st.session_state.wallet_address)
            if yield_info:
                yield_earnings = yield_info.get("estimated_earnings_30d", 0)
                yield_apy = yield_info.get("current_apy", 0)
        except Exception:
            pass

        # Count active automations (scheduled tasks)
        try:
            from scheduler_manager import SchedulerManager
            if user_id:
                tasks = SchedulerManager.get_user_tasks(user_id)
                active_automations = len([t for t in tasks if t.get("status") == "active"])
        except Exception:
            pass

    # Build treasury status line
    treasury_parts = []
    if yield_apy > 0:
        treasury_parts.append(f"{yield_apy:.1f}% APY")
    if active_automations > 0:
        treasury_parts.append(f"{active_automations} auto")
    treasury_status = " · ".join(treasury_parts) if treasury_parts else "Tap to earn"

    # Add action hint if not earning yet
    balance_action = "earn" if yield_apy == 0 else None
    slots.append({
        "mode": "stat",
        "title": "BALANCE",
        "main": f"${usdc_balance:.2f}",
        "stats": treasury_status,
        "spotlight": True,
        "icon": BRANDS["system"]["icon"],
        "brand_key": "system",
        "action": balance_action,
    })

    # Slot 3: Yield card (if earning) OR first perk
    if yield_apy > 0:
        yield_brand = BRANDS["yield"]
        slots.append({
            "mode": "yield",
            "title": "EARNING",
            "main": f"{yield_apy:.1f}%",
            "sub": f"+${yield_earnings:.2f}/mo",
            "bg": yield_brand["bg"],
            "border": yield_brand.get("border", "none"),
            "shadow": yield_brand["shadow"],
            "accent": yield_brand["accent"],
            "text_color": yield_brand["text_color"],
            "sub_color": yield_brand["sub_color"],
            "icon_filter": yield_brand["icon_filter"],
            "text_shadow": yield_brand["text_shadow"],
            "spotlight": False,
            "icon": yield_brand["icon"],
            "brand_key": "yield",
        })
        # Only show 1 perk if yield card is shown
        perks_to_show = perks[:1]
    else:
        # No yield, show both perks
        perks_to_show = perks[:2]

    # Slots 3-4 (or just 4): Perks
    for p in perks_to_show:
        brand = BRANDS.get(p["brand"].lower(), BRANDS["system"])
        pct = int((p["progress"] / p["target"]) * 100) if p["target"] > 0 else 0
        spent = p.get("spent", 0)
        remaining = max(0, p["target"] - p["progress"])
        slots.append({
            "mode": "perk",
            "title": p["brand"].upper(),
            "main": f"{p['progress']}/{p['target']}",
            "sub": p["reward"],
            "pct": pct,
            "spent": spent,
            "remaining": remaining,
            "brand_key": p["brand"].lower(),
            "bg": brand["bg"],
            "border": brand.get("border", "none"),
            "shadow": brand["shadow"],
            "accent": brand["accent"],
            "text_color": brand.get("text_color", "#FFFFFF"),
            "sub_color": brand.get("sub_color", "rgba(255,255,255,0.6)"),
            "icon_filter": brand.get("icon_filter", "brightness(0) invert(1) opacity(0.8)"),
            "text_shadow": brand.get("text_shadow", "none"),
            "spotlight": False,
            "icon": brand["icon"],
        })

    # === RENDER: Mobile-First Responsive ===
    # Inject mobile CSS once (V24 Ambient Glow upgrade)
    st.markdown("""
    <style>
    .pulse-deck-wrapper {
        position: relative;
        overflow: hidden;
    }
    .pulse-deck {
        display: flex;
        gap: 12px;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        -ms-overflow-style: none;
        padding: 4px 0 8px 0;
    }
    .pulse-deck::-webkit-scrollbar { display: none; }
    .pulse-card {
        flex: 0 0 auto;
        scroll-snap-align: start;
        min-width: 140px;
        width: calc(25% - 9px);
    }

    /* Mobile: remove edge bleed, use natural padding */
    @media (max-width: 768px) {
        .pulse-deck {
            margin: 0;
            padding-left: 0;
            padding-right: 0;
        }
    }

    /* === V24 AMBIENT GLOW SYSTEM === */
    .pulse-card-inner {
        position: relative;
        overflow: hidden;
        transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        /* Default glow color - overridden per card */
        --glow-color: rgba(255, 255, 255, 0.15);
    }

    /* Brand-specific glow colors */
    .pulse-card[data-brand="spotify"] .pulse-card-inner { --glow-color: rgba(30, 215, 96, 0.25); }
    .pulse-card[data-brand="netflix"] .pulse-card-inner { --glow-color: rgba(229, 9, 20, 0.25); }
    .pulse-card[data-brand="ai"] .pulse-card-inner { --glow-color: transparent; }
    .pulse-card[data-brand="system"] .pulse-card-inner { --glow-color: rgba(255, 255, 255, 0.3); }
    .pulse-card[data-brand="yield"] .pulse-card-inner { --glow-color: rgba(34, 197, 94, 0.3); }
    .pulse-card[data-brand="automation"] .pulse-card-inner { --glow-color: rgba(139, 92, 246, 0.3); }

    /* Spotify/Netflix: glow positioned at right-bottom corner */
    .pulse-card[data-brand="spotify"] .pulse-card-inner::after,
    .pulse-card[data-brand="netflix"] .pulse-card-inner::after {
        background: radial-gradient(80% 80% at 85% 120%, var(--glow-color) 0%, transparent 60%);
    }

    /* Noise texture overlay (inline SVG - no external deps) */
    .pulse-card-inner::before {
        content: "";
        position: absolute;
        inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        opacity: 0.03;
        mix-blend-mode: overlay;
        pointer-events: none;
        border-radius: inherit;
    }

    /* Ambient glow: radial gradient at bottom for "light pooling" effect */
    .pulse-card-inner::after {
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(80% 80% at 50% 120%, var(--glow-color) 0%, transparent 60%);
        opacity: 0.6;
        pointer-events: none;
        border-radius: inherit;
        transition: opacity 0.3s ease;
    }

    /* Dark glass cards: specular highlight + base shadow */
    .pulse-card-inner:not([style*="background:#FFFFFF"]):not([style*="background: #FFFFFF"]) {
        box-shadow:
            inset 0 1px 0 0 rgba(255,255,255,0.08),
            0 4px 12px rgba(0,0,0,0.2);
    }

    /* Spotlight cards: keep clean white look, subtle glow */
    .pulse-card-inner[style*="background:#FFFFFF"],
    .pulse-card-inner[style*="background: #FFFFFF"] {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .pulse-card-inner[style*="background:#FFFFFF"]::before,
    .pulse-card-inner[style*="background: #FFFFFF"]::before {
        opacity: 0.02;
    }
    .pulse-card-inner[style*="background:#FFFFFF"]::after,
    .pulse-card-inner[style*="background: #FFFFFF"]::after {
        opacity: 0; /* No ambient glow on white cards */
    }

    /* Hover: lift with brand-colored glow */
    .pulse-card:hover .pulse-card-inner {
        transform: translateY(-3px);
    }
    .pulse-card:hover .pulse-card-inner::after {
        opacity: 1;
    }
    .pulse-card:hover .pulse-card-inner:not([style*="background:#FFFFFF"]):not([style*="background: #FFFFFF"]) {
        box-shadow:
            inset 0 1px 0 0 rgba(255,255,255,0.15),
            inset 0 0 0 1px rgba(255,255,255,0.08),
            0 8px 24px rgba(0,0,0,0.3),
            0 0 24px var(--glow-color);
    }
    .pulse-card:hover .pulse-card-inner[style*="background:#FFFFFF"],
    .pulse-card:hover .pulse-card-inner[style*="background: #FFFFFF"] {
        box-shadow: 0 12px 28px rgba(0,0,0,0.2);
    }

    /* No hover on touch devices */
    @media (hover: none) {
        .pulse-card:hover .pulse-card-inner {
            transform: none;
        }
        .pulse-card:hover .pulse-card-inner::after {
            opacity: 0.6;
        }
    }

    /* Mobile: 2 cards visible, scroll for more */
    @media (max-width: 768px) {
        .pulse-card {
            min-width: 160px;
            width: calc(50% - 6px);
        }
        .pulse-deck { gap: 8px; }
        /* Scroll hint: fade on right edge */
        .pulse-deck-wrapper::after {
            content: '';
            position: absolute;
            right: 0;
            top: 0;
            height: 100%;
            width: 32px;
            background: linear-gradient(to right, transparent, #09090b);
            pointer-events: none;
            opacity: 0.8;
        }
    }
    /* Small mobile: compact cards */
    @media (max-width: 480px) {
        .pulse-card { min-width: 145px; }
        .pulse-card-inner { padding: 14px !important; height: 88px !important; }
        .pulse-card-title { font-size: 9px !important; }
        .pulse-card-main { font-size: 14px !important; }
        .pulse-card-sub { font-size: 10px !important; }
        .pulse-card-main .usdc-label { display: none; }
    }
    /* Extra small: iPhone SE, Mini */
    @media (max-width: 375px) {
        .pulse-card { min-width: 130px; }
        .pulse-card-inner { padding: 12px !important; height: 82px !important; }
        .pulse-card-title { font-size: 8px !important; }
        .pulse-card-main { font-size: 13px !important; }
        .pulse-card-sub { display: none; }
    }
    </style>
    <script>
    // V25: Pulse Deck card actions
    document.addEventListener('click', function(e) {
        const card = e.target.closest('.pulse-card[data-action]');
        if (!card) return;

        const action = card.getAttribute('data-action');
        if (action === 'earn') {
            // Find and click the Earn tab
            const tabs = document.querySelectorAll('[data-baseweb="tab"]');
            for (const tab of tabs) {
                if (tab.textContent.trim() === 'Earn') {
                    tab.click();
                    // Scroll to modules section
                    setTimeout(() => {
                        const tabPanel = document.querySelector('[data-baseweb="tab-panel"]');
                        if (tabPanel) {
                            tabPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }, 100);
                    break;
                }
            }
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # Build all cards as HTML for horizontal scroll container
    cards_html = ""
    for slot in slots:
        cards_html += _render_pulse_card_html(slot)

    st.markdown(f'<div class="pulse-deck-wrapper"><div class="pulse-deck">{cards_html}</div></div>', unsafe_allow_html=True)


def _render_pulse_card_html(slot: dict) -> str:
    """Return HTML string for a pulse card (for horizontal scroll container)."""

    mode = slot["mode"]
    icon = slot["icon"]
    is_spotlight = slot.get("spotlight", False)
    pct = slot.get("pct", 0)
    spent = slot.get("spent", 0)
    # Brand key for ambient glow targeting
    brand_key = slot.get("brand_key", mode)  # Default to mode (ai, stat, etc.)

    # === THEME: Spotlight vs Vibrant Mesh ===
    if is_spotlight:
        bg = "#FFFFFF"
        text_color = "#000000"
        sub_color = "#8e8e93"
        shadow = "0 4px 12px rgba(0,0,0,0.15)"
        icon_filter = "brightness(0)"
        track_color = "rgba(0,0,0,0.06)"
        accent = "#000000"
        text_shadow = "none"
        fill_shadow = "none"
    else:
        bg = slot.get("bg", "rgba(255,255,255,0.03)")
        text_color = slot.get("text_color", "#FFFFFF")
        sub_color = slot.get("sub_color", "rgba(255,255,255,0.6)")
        shadow = slot.get("shadow", "none")
        icon_filter = slot.get("icon_filter", "brightness(0) invert(1) opacity(0.8)")
        track_color = "rgba(255,255,255,0.25)"
        accent = slot.get("accent", "#FFFFFF")
        text_shadow = slot.get("text_shadow", "none")
        # White glow on mesh gradient cards
        fill_shadow = "0 0 8px rgba(255,255,255,0.6)"

    # === ICON ===
    icon_html = f'<img src="{icon}" style="height:14px;width:auto;max-width:18px;object-fit:contain;filter:{icon_filter};opacity:1.0;">'

    # === MAIN VALUE (compact for mobile) ===
    if mode == "perk":
        # Same line: 75/100 USDC Spent - matches stats card styling
        main_html = f'<div class="pulse-card-main" style="display:flex;align-items:baseline;gap:6px;margin-top:4px;"><span style="font-family:Inter;font-size:17px;font-weight:800;color:{text_color};letter-spacing:-0.03em;text-shadow:{text_shadow};">{slot["main"]}</span><span class="usdc-label" style="font-family:JetBrains Mono;font-size:10px;color:{sub_color};text-shadow:{text_shadow};">USDC Spent</span></div>'
    else:
        main_html = f'<div class="pulse-card-main" style="font-family:Inter;font-size:17px;font-weight:800;color:{text_color};margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-0.03em;text-shadow:{text_shadow};">{slot["main"]}</div>'

    # === BOTTOM SECTION ===
    if mode == "perk":
        # Show progress toward reward: "25 more → 1 Mo Free"
        reward = slot.get("sub", "")
        remaining = slot.get("remaining", 0)
        if remaining > 0:
            bottom = f'<div class="pulse-card-sub" style="font-family:JetBrains Mono;font-size:11px;color:{sub_color};text-shadow:{text_shadow};"><span style="color:{accent};">{remaining} more</span> → {reward}</div>'
        else:
            bottom = f'<div class="pulse-card-sub" style="font-family:JetBrains Mono;font-size:11px;color:{accent};text-shadow:{text_shadow};">Unlocked! {reward}</div>'
    elif mode == "ai":
        bottom = f'<div class="pulse-card-sub" style="font-family:JetBrains Mono;font-size:11px;color:{sub_color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><span style="color:{accent};">●</span> {slot["sub"]}</div>'
    elif mode == "yield":
        # Yield card - show estimated earnings with green indicator
        bottom = f'<div class="pulse-card-sub" style="font-family:JetBrains Mono;font-size:11px;color:{sub_color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><span style="color:{accent};">↑</span> {slot["sub"]}</div>'
    elif mode == "stat" and slot.get("stats"):
        bottom = f'<div class="pulse-card-sub" style="font-family:JetBrains Mono;font-size:11px;color:{sub_color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{slot["stats"]}</div>'
    elif is_spotlight:
        bottom = '<div style="text-align:right;"><span style="font-family:Inter;font-weight:700;font-size:14px;color:#000;">→</span></div>'
    else:
        bottom = f'<div class="pulse-card-sub" style="font-family:JetBrains Mono;font-size:11px;color:{sub_color};text-align:right;text-shadow:{text_shadow};">{slot.get("sub", "")} →</div>'

    # === THE CARD ===
    border = slot.get("border", "none")
    mode = slot["mode"]
    pct = slot.get("pct", 0)
    accent = slot.get("accent", "#1ed760")

    # Card style (no progress bar for perk cards)
    card_style = f"background:{bg};border:{border};border-radius:14px;padding:16px;height:96px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:{shadow};"
    progress_bar = ""

    title_style = f"font-family:Inter;font-size:10px;color:{sub_color};letter-spacing:0.02em;font-weight:700;text-transform:uppercase;text-shadow:{text_shadow};"

    # V24: Add data-brand attribute for ambient glow targeting
    # V25: Add data-action for clickable cards
    action = slot.get("action", "")
    action_attr = f'data-action="{action}"' if action else ""
    cursor_style = "cursor:pointer;" if action else ""

    return f'<div class="pulse-card" data-brand="{brand_key}" {action_attr}><div class="pulse-card-inner" style="{card_style}{cursor_style}"><div style="display:flex;justify-content:space-between;align-items:center;"><span class="pulse-card-title" style="{title_style}">{slot["title"]}</span>{icon_html}</div>{main_html}{bottom}{progress_bar}</div></div>'


def _render_pulse_card(slot: dict):
    """Legacy wrapper - renders single card via st.markdown."""
    st.markdown(_render_pulse_card_html(slot), unsafe_allow_html=True)


# Legacy alias
def render_action_deck():
    render_pulse_deck()


# --- MODULES: DEEP GLASS TILES ---
def render_modules():
    """
    Render full capability library with all categories.
    V7 Address Box styling (matches sidebar deposit address) with 9 category tabs.
    """
    # V7 Address Box Style - matches sidebar deposit address styling
    st.markdown("""
    <style>
    /* Container padding */
    [data-baseweb="tab-panel"] {
        padding-top: 16px !important;
    }

    /* The Tile (Button) - Address Box Style */
    [data-baseweb="tab-panel"] button {
        padding: 10px 12px !important;
        border-radius: 4px !important;
        background: rgba(255,255,255,0.05) !important;
        border: none !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }

    /* Hover State - subtle brighten */
    [data-baseweb="tab-panel"] button:hover:not(:disabled) {
        background: rgba(255,255,255,0.1) !important;
    }

    /* Active/Press State */
    [data-baseweb="tab-panel"] button:active:not(:disabled) {
        background: rgba(255,255,255,0.08) !important;
    }

    /* Text Styling - JetBrains Mono like address */
    [data-baseweb="tab-panel"] button p {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
        font-weight: 400 !important;
        color: #888 !important;
        letter-spacing: 0 !important;
    }

    /* Hover text brighten */
    [data-baseweb="tab-panel"] button:hover:not(:disabled) p {
        color: #fff !important;
    }

    /* Disabled state - same look, just not interactive */
    [data-baseweb="tab-panel"] button:disabled {
        opacity: 1 !important;
        cursor: default !important;
    }
    [data-baseweb="tab-panel"] button:disabled p {
        color: #888 !important;
    }

    /* Mobile: compact tabs, show first 5 only */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
        .stTabs [data-baseweb="tab"] {
            font-size: 11px !important;
            padding: 8px 10px !important;
            white-space: nowrap;
        }
        /* Hide tabs beyond first 5 on mobile */
        .stTabs [data-baseweb="tab-list"] > button:nth-child(n+6) {
            display: none !important;
        }
        [data-baseweb="tab-panel"] button {
            padding: 8px 10px !important;
        }
        [data-baseweb="tab-panel"] button p {
            font-size: 11px !important;
        }
        /* Limit to 2 columns on mobile */
        [data-baseweb="tab-panel"] .stHorizontalBlock {
            flex-wrap: wrap !important;
        }
        [data-baseweb="tab-panel"] .stHorizontalBlock > div {
            flex: 0 0 48% !important;
            max-width: 48% !important;
        }
    }
    @media (max-width: 480px) {
        .stTabs [data-baseweb="tab"] {
            font-size: 10px !important;
            padding: 6px 8px !important;
        }
        [data-baseweb="tab-panel"] button {
            padding: 6px 8px !important;
        }
        [data-baseweb="tab-panel"] button p {
            font-size: 10px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Full categories with (label, prompt, is_live)
    # Import showcase agents for demo-ready flows
    from showcase_agents import get_showcase_agents

    # Build Showcase category from demo-ready agents
    demo_agents = get_showcase_agents(demo_ready_only=True)
    showcase_items = [(f"{a.icon} {a.name}", a.initial_prompt, True) for a in demo_agents]

    categories = {
        "Showcase": showcase_items,  # Demo-ready AI agents first
        "Automate": [
            ("Recurring Send", "Set up a recurring USDC payment to someone", True),
            ("Auto-Savings", "Move a % of deposits to earn yield automatically", False),
            ("Bill Autopay", "Automatically pay a bill when it's due", True),
            ("Price Alert", "Alert me when ETH drops below $3000", False),
            ("Low Balance", "Warn me if my balance drops below $50", False),
        ],
        "Send & Pay": [
            ("Send USDC", "Help me send USDC to someone", True),
            ("Pay Bills", "Help me pay a bill with crypto", True),
            ("Phone Top-up", "I need to add minutes to my phone", True),
            ("Split Bill", "Split a payment between multiple people", False),
        ],
        "Earn": [
            ("Start Earning", "Put my idle USDC to work earning ~4% APY", True),
            ("Check Yield", "How much am I earning on my deposits?", True),
            ("Withdraw", "I want to withdraw from yield", True),
            ("Best Rates", "Where can I get the best yield rates right now?", False),
        ],
        "Bot Trade": [
            ("Hyperliquid", "Trade perpetuals on Hyperliquid DEX", False),
            ("Polymarket", "Bet on prediction markets via Polymarket", False),
            ("Pump.fun", "Launch or trade meme coins on Pump.fun", False),
            ("Kalshi", "Trade event contracts on Kalshi", False),
        ],
        "Content": [
            ("New AI Character", "Create a custom AI character or persona", False),
        ],
        "Tools": [
            ("Get Domain", "I want to register a domain", True),
            ("VPN", "I want a Mullvad VPN subscription", True),
            ("eSIM", "I need an international eSIM", False),
            ("My Rules", "Show me my active automations and rules", True),
        ],
        "Shopping": [
            ("Amazon", "I want to buy an Amazon gift card", True),
            ("Target", "Show me Target gift cards", True),
            ("Walmart", "I want a Walmart gift card", True),
            ("Best Buy", "Show me Best Buy gift cards", True),
            ("Sephora", "Get a Sephora gift card", True),
        ],
        "Food": [
            ("DoorDash", "I want a DoorDash gift card", True),
            ("Uber Eats", "I want Uber Eats gift card credits", True),
            ("Starbucks", "Get me a Starbucks gift card", True),
            ("Chipotle", "I want a Chipotle gift card", True),
            ("Grubhub", "Show me Grubhub gift cards", True),
        ],
        "Streaming": [
            ("Netflix", "I want a Netflix gift card", True),
            ("Spotify", "Get me a Spotify gift card", True),
            ("Disney+", "I want a Disney+ gift card", False),
            ("Hulu", "Show me Hulu gift cards", False),
            ("Apple TV+", "I want an Apple TV+ subscription", False),
        ],
        "Gaming": [
            ("PlayStation", "Show me PlayStation gift cards", True),
            ("Xbox", "I want an Xbox gift card", True),
            ("Steam", "Get me a Steam gift card", True),
            ("Nintendo", "I want a Nintendo eShop card", True),
            ("Roblox", "Show me Roblox gift cards", True),
        ],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            cols = st.columns(min(len(items), 4))
            for i, (label, prompt, is_live) in enumerate(items):
                col_idx = i % 4
                with cols[col_idx]:
                    if is_live:
                        if st.button(label, key=f"mod_{tab_idx}_{i}", use_container_width=True):
                            st.session_state.messages.append({"role": "user", "content": prompt})
                            st.session_state._quick_action_triggered = True
                            st.rerun()
                    else:
                        st.button(label, key=f"mod_{tab_idx}_{i}", disabled=True,
                                  use_container_width=True, help=prompt)


def render_modules_preview():
    """
    Render capability preview for pre-login users (all disabled).
    Uses same V7 Address Box styling as render_modules.
    """
    # V7 Address Box CSS (compact version)
    st.markdown("""
    <style>
    [data-baseweb="tab-panel"] { padding-top: 16px !important; }
    [data-baseweb="tab-panel"] button {
        padding: 10px 12px !important;
        border-radius: 4px !important;
        background: rgba(255,255,255,0.05) !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-baseweb="tab-panel"] button p {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
        font-weight: 400 !important;
        color: #888 !important;
    }
    [data-baseweb="tab-panel"] button:disabled { opacity: 1 !important; cursor: default !important; }
    </style>
    """, unsafe_allow_html=True)

    categories = {
        "Send & Pay": ["Send USDC", "Pay Bills", "Phone Top-up", "Schedule"],
        "Earn": ["Earn Yield", "Swap to ETH", "Stack Sats"],
        "Bot Trade": ["Hyperliquid", "Polymarket", "Pump.fun", "Kalshi"],
        "Content": ["New AI Character"],
        "Tools": ["Get Domain", "VPN", "eSIM", "Alerts"],
        "Shopping": ["Amazon", "Target", "Walmart", "Best Buy", "Sephora"],
        "Food": ["DoorDash", "Uber Eats", "Starbucks", "Chipotle", "Grubhub"],
        "Streaming": ["Netflix", "Spotify", "Disney+", "Hulu", "Apple TV+"],
        "Gaming": ["PlayStation", "Xbox", "Steam", "Nintendo", "Roblox"],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            cols = st.columns(min(len(items), 4))
            for i, label in enumerate(items):
                col_idx = i % 4
                with cols[col_idx]:
                    st.button(label, key=f"prev_{tab_idx}_{i}", disabled=True,
                              use_container_width=True, help="Sign up to use")


# --- MAIN INTERFACE ---
def chat_interface(create_agent_func):
    """Main chat interface with V12 liquid silver styling."""
    # 1. HEADER
    render_header()

    # 2. HANDLE PRE-LOGIN STATE
    if not st.session_state.wallet_address:
        st.markdown("""
        <div style="
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding: 60px 0;
            margin: 20px 0;
            text-align: center;
        ">
            <div style="font-family: 'Inter', -apple-system, sans-serif; font-weight: 300; color: white; font-size: 20px; letter-spacing: -0.02em;">Authentication Required</div>
            <div style="color: #444; font-size: 12px; margin-top: 12px; font-family: 'JetBrains Mono'; letter-spacing: 0.05em;">INITIALIZE SESSION TO PROCEED</div>
        </div>
        """, unsafe_allow_html=True)
        render_modules_preview()
        st.chat_input("Waiting...", disabled=True, key="preview_input")
        return

    # 3. HANDLE LOCKED STATE
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.markdown("""
        <div style="color: #666; font-size: 14px; padding: 20px 0;">Session locked. Unlock in sidebar to continue.</div>
        """, unsafe_allow_html=True)
        st.chat_input("Locked", disabled=True, key="locked_input")
        return

    # 4. ONBOARDING & API CHECKS
    from onboarding import show_onboarding
    if not show_onboarding():
        return

    from api_key_setup import show_api_key_banner
    from settings_manager import SettingsManager
    from free_tier import FreeTier

    user_id = st.session_state.get("user_id")
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))

    if not has_api_key:
        if FreeTier.is_available() and not FreeTier.has_quota(user_id):
            FreeTier.show_upgrade_prompt()
        else:
            show_api_key_banner()
        return

    # Force agent re-initialization if API key was just configured
    if has_api_key and st.session_state.get("_api_key_just_saved"):
        st.session_state.agent = None
        st.session_state._agent_initializing = False
        st.session_state._api_key_just_saved = False
        cache_key = f"_llm_config_{user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]

    # 5. PULSE DECK
    render_pulse_deck()

    # 6. MODULES - Show categories/actions first (before chat)
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    render_modules()

    # 7. CHAT SECTION - Hairline divider
    st.markdown("<div style='height: 32px; border-bottom: 1px solid rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Welcome state (if no messages yet) - simple text prompt
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align: center; padding: 24px 0 16px 0;">
            <div style="font-family: 'Inter', sans-serif; font-size: 15px; color: #71717a; font-weight: 300;">
                Select an action above, or type your own request below
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Render chat history - pure text, minimal
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            safe_content = html.escape(_ensure_string(msg['content']))
            if msg["role"] == "assistant":
                # AI: Light gray, thin weight
                st.markdown(f"<div style='color: #ccc; font-family: 'Inter', -apple-system, sans-serif; font-weight: 300; font-size: 15px; line-height: 1.7;'>{safe_content}</div>", unsafe_allow_html=True)
            else:
                # User: White, clean
                st.markdown(f"<div style='color: white; font-family: 'Inter', -apple-system, sans-serif; font-size: 15px; line-height: 1.6;'>{safe_content}</div>", unsafe_allow_html=True)

    # Render pending transaction card if exists
    _render_pending_transaction_card()

    # 7. HANDLE INPUT LOGIC
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # 8. INPUT FIELD
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if not prompt:
        prompt = st.chat_input("Start typing...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(f"<div style='color: white; font-family: 'Inter', -apple-system, sans-serif; font-size: 15px;'>{html.escape(prompt)}</div>", unsafe_allow_html=True)

    # 9. PROCESS MESSAGE (Streaming)
    if prompt:
        with st.chat_message("assistant"):
            # Create empty container for streaming output
            response_container = st.empty()
            message_success = False
            response = ""

            # Show thinking indicator while initializing
            from design_system import ui
            response_container.markdown("""
            <style>
            @keyframes thinking-pulse {
                0%, 100% { opacity: 0.3; }
                50% { opacity: 1; }
            }
            .thinking-container {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 0;
            }
            .thinking-text {
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                color: #52525b;
                letter-spacing: 0.05em;
            }
            .thinking-dots {
                display: flex;
                gap: 4px;
            }
            .thinking-dot {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #52525b;
                animation: thinking-pulse 1.4s ease-in-out infinite;
            }
            .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
            .thinking-dot:nth-child(3) { animation-delay: 0.4s; }
            </style>
            <div class="thinking-container">
                <span class="thinking-text">Thinking</span>
                <div class="thinking-dots">
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            try:
                # Agent initialization logic
                if not st.session_state.get("agent"):
                    try:
                        agent = create_agent_func()
                        if agent:
                            st.session_state.agent = agent
                    except Exception as agent_err:
                        from utils.logger import logger
                        logger.error(f"Agent creation failed: {type(agent_err).__name__}: {str(agent_err)}")
                        import traceback
                        logger.error(traceback.format_exc())

                if not st.session_state.get("agent"):
                    # Handle missing agent - show helpful error
                    from api_key_setup import check_api_key_status
                    has_key, provider = check_api_key_status()
                    if not has_key:
                        response = "**Setup Required:** Please configure your API key in Settings to enable AI."
                        response_container.markdown(f"<div style='color: #ccc; font-family: 'Inter', -apple-system, sans-serif; font-weight: 300; font-size: 15px; line-height: 1.7;'>{response}</div>", unsafe_allow_html=True)
                    else:
                        # Has key but agent still failed - show error and retry once
                        retry_count = st.session_state.get("_agent_retry_count", 0)
                        if retry_count < 2:
                            st.session_state._agent_retry_count = retry_count + 1
                            response_container.markdown("<div style='color: #888; font-family: 'Inter', -apple-system, sans-serif; font-size: 14px;'>Connecting to AI... please wait.</div>", unsafe_allow_html=True)
                            import time
                            time.sleep(0.5)
                            # Keep the message, just retry
                            st.rerun()
                        else:
                            # Failed after retries - show error
                            st.session_state._agent_retry_count = 0
                            response = f"**Connection Error:** Unable to connect to {provider or 'AI provider'}. Check your API key in Settings."
                            response_container.markdown(f"<div style='color: #ccc; font-family: 'Inter', -apple-system, sans-serif; font-weight: 300; font-size: 15px; line-height: 1.7;'>{response}</div>", unsafe_allow_html=True)
                            # Remove the user message that couldn't be processed
                            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                                st.session_state.messages.pop()
                else:
                    # Process with LangChain 1.2+ API (graph-based agent)
                    from langchain_core.messages import HumanMessage, AIMessage

                    # Build message history for new agent format
                    messages = []
                    for m in st.session_state.messages[:-1]:
                        if m["role"] == "user":
                            messages.append(HumanMessage(content=m["content"]))
                        else:
                            messages.append(AIMessage(content=m["content"]))
                    # Add current user message
                    messages.append(HumanMessage(content=prompt))

                    # Create streaming callback handler
                    stream_handler = StreamlitTokenHandler(response_container)

                    # Invoke with new langchain 1.2+ format
                    result = st.session_state.agent.invoke(
                        {"messages": messages},
                        config={"callbacks": [stream_handler]}
                    )

                    # Extract response from new format (messages list)
                    result_messages = result.get("messages", [])
                    if result_messages:
                        # Get last AI message content (may be string or list)
                        last_msg = result_messages[-1]
                        content = getattr(last_msg, 'content', '')
                        response = _ensure_string(content) or stream_handler.get_final_text() or "Error processing request."
                    else:
                        response = stream_handler.get_final_text() or "Error processing request."
                    message_success = True

                    # Extract tool calls from messages for logging
                    tool_calls = []
                    for msg in result_messages:
                        msg_type = type(msg).__name__
                        if msg_type == "AIMessage" and hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                tool_calls.append({
                                    "tool": tc.get("name", "unknown"),
                                    "input": tc.get("args", {}),
                                })
                        elif msg_type == "ToolMessage":
                            # Match tool result with corresponding call
                            tool_calls.append({
                                "tool": getattr(msg, 'name', 'tool'),
                                "output_preview": str(getattr(msg, 'content', ''))[:500]
                            })

                    # Log decision for AI training data
                    try:
                        log_ai_decision(
                            user_message=prompt,
                            ai_response=response,
                            tool_calls=tool_calls if tool_calls else None,
                            outcome="success"
                        )
                    except Exception as log_err:
                        logger.debug(f"Decision logging failed: {log_err}")

                    # Build action indicator if tools were used
                    action_indicator = _render_action_indicator(tool_calls)

                    # Final render with action indicator
                    response_container.markdown(f"""
                    <div style='color: #ccc; font-family: \"Inter\", -apple-system, sans-serif; font-weight: 300; font-size: 15px; line-height: 1.7;'>
                        {html.escape(response)}
                    </div>
                    {action_indicator}
                    """, unsafe_allow_html=True)

            except Exception as e:
                response = f"**System Error:** {str(e)}"
                response_container.markdown(f"<div style='color: #ccc; font-family: 'Inter', -apple-system, sans-serif; font-weight: 300; font-size: 15px; line-height: 1.7;'>{html.escape(response)}</div>", unsafe_allow_html=True)

                # Log failed decision
                try:
                    log_ai_decision(
                        user_message=prompt,
                        ai_response=response,
                        outcome="failure"
                    )
                except Exception:
                    pass  # Don't let logging failure affect user experience

            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": response})

            if message_success and llm_config.get("using_free_tier"):
                FreeTier.increment_usage(user_id)

            # Rerun to show chat input after processing
            st.rerun()

    # Mobile bottom navigation (only shows on mobile via CSS)
    _render_mobile_nav()


def _render_mobile_nav():
    """Render mobile bottom navigation bar (CSS hides on desktop)."""
    st.markdown("""
    <style>
    .mobile-nav {
        display: none;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(9, 9, 11, 0.98);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255,255,255,0.06);
        padding: 8px 0 calc(8px + env(safe-area-inset-bottom, 0px)) 0;
        z-index: 9999;
    }
    .mobile-nav-inner {
        display: flex;
        justify-content: space-around;
        align-items: center;
        max-width: 400px;
        margin: 0 auto;
    }
    .mobile-nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 8px 16px;
        cursor: pointer;
        transition: transform 0.1s ease;
        text-decoration: none;
    }
    .mobile-nav-item:active {
        transform: scale(0.92);
    }
    .mobile-nav-icon {
        font-size: 20px;
        line-height: 1;
    }
    .mobile-nav-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .mobile-nav-item.active .mobile-nav-icon,
    .mobile-nav-item.active .mobile-nav-label {
        color: #f4f4f5;
    }
    .mobile-nav-item:not(.active) .mobile-nav-icon,
    .mobile-nav-item:not(.active) .mobile-nav-label {
        color: #52525b;
    }
    .mobile-nav-indicator {
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: #22c55e;
        margin-top: 2px;
    }
    @media (max-width: 768px) {
        .mobile-nav {
            display: block;
        }
        /* Add padding to main content to prevent overlap */
        .main .block-container,
        section.main .block-container {
            padding-bottom: 90px !important;
        }
    }
    </style>
    <div class="mobile-nav">
        <div class="mobile-nav-inner">
            <div class="mobile-nav-item active">
                <span class="mobile-nav-icon">💬</span>
                <span class="mobile-nav-label">Chat</span>
                <div class="mobile-nav-indicator"></div>
            </div>
            <div class="mobile-nav-item">
                <span class="mobile-nav-icon">💰</span>
                <span class="mobile-nav-label">Wallet</span>
            </div>
            <div class="mobile-nav-item">
                <span class="mobile-nav-icon">📋</span>
                <span class="mobile-nav-label">History</span>
            </div>
            <div class="mobile-nav-item">
                <span class="mobile-nav-icon">⚙️</span>
                <span class="mobile-nav-label">Settings</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
