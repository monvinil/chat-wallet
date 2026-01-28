"""
Chat Interface Component
V12 Design: "Liquid Silver" - Floating Void Aesthetic
"""

import html
import streamlit as st
from chain_utils import ChainUtils
from langchain_core.callbacks import BaseCallbackHandler


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
        # Show tool status if active
        status_html = ""
        if self.tool_status:
            status_html = f'<div style="font-size: 12px; color: #666; margin-bottom: 8px;">{self.tool_status}</div>'

        # Show text with blinking cursor
        cursor = "▌" if not self.tool_status else ""
        text_html = f'<div style="color: #ccc; font-family: Inter; font-weight: 300; font-size: 15px; line-height: 1.7;">{html.escape(self.text)}{cursor}</div>'

        self.container.markdown(status_html + text_html, unsafe_allow_html=True)

    def get_final_text(self) -> str:
        """Get the complete text without cursor."""
        return self.text


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
        <div style="font-family: 'Inter'; font-size: 18px; font-weight: 400; color: white; letter-spacing: -0.02em;">
            {value} {f'<span style="font-size: 12px; color: {color}; margin-left: 4px;">{tag}</span>' if tag else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- HEADER: MAGAZINE ---
def render_header():
    """Magazine-style minimal header."""
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        <div style="margin-top: 30px;">
            <h1 style="font-size: 28px; margin: 0; font-weight: 500; letter-spacing: -0.04em; text-transform: none !important;">USDChat</h1>
            <p style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #555; margin: 8px 0 0 0; letter-spacing: 0.1em;">
                Make your AI chat ideas real with digital USD. Powered by USDC.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="text-align: right; margin-top: 40px;">
            <span style="font-family: 'JetBrains Mono'; font-size: 11px; color: #fff; background: rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 10px;">ONLINE</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


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
            "bg": "rgba(255,255,255,0.03)",
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
            "bg": "rgba(255,255,255,0.03)",
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
            "bg": "rgba(255,255,255,0.03)",
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
    }

    # === DATA SOURCES (mock - replace with real queries) ===
    active_tasks = []  # TODO: Pull from pending_approvals table

    perks = [
        {"brand": "spotify", "progress": 75, "target": 100, "reward": "1 Mo Free", "spent": 75},
        {"brand": "netflix", "progress": 32, "target": 100, "reward": "1 Mo Free", "spent": 32},
    ]

    # === SLOT BUILDER ===
    slots = []

    # Slot 1: AI Data card (first)
    # TODO: Pull real data from llm_config / free tier usage
    ai_brand = BRANDS["ai"]
    ai_provider = "Claude"  # TODO: Get from user's LLM config
    ai_tier = "Free"  # TODO: Get from subscription status
    ai_remaining = "8/10"  # TODO: Get from FreeTier.get_remaining_messages()

    slots.append({
        "mode": "ai",
        "title": "YOUR AI",
        "main": ai_provider,
        "sub": f"{ai_tier} · {ai_remaining} msgs",
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

    # Slot 2: Priority Action or Stats fallback (SPOTLIGHT - White)
    if active_tasks:
        t = active_tasks[0]
        slots.append({
            "mode": "task",
            "title": t["label"],
            "main": t["value"],
            "sub": t["action"],
            "spotlight": True,
            "icon": "https://api.iconify.design/mdi/alert-circle.svg",
            "brand_key": "system",
        })
    else:
        # TODO: Replace with real data from transactions table
        month_spending = 0.00
        month_tx_count = 0
        scheduled_count = 0  # TODO: Pull from scheduled_payments table

        slots.append({
            "mode": "stat",
            "title": "YOUR STATS",
            "main": f"${month_spending:.2f}",
            "stats": f"{month_tx_count} txs · {scheduled_count} scheduled",
            "spotlight": True,
            "icon": BRANDS["system"]["icon"],
            "brand_key": "system",
        })

    # Slots 3-4: Perks (Matte dark glass with glowing progress bars)
    for p in perks[:2]:
        brand = BRANDS.get(p["brand"].lower(), BRANDS["system"])
        pct = int((p["progress"] / p["target"]) * 100) if p["target"] > 0 else 0
        spent = p.get("spent", 0)
        slots.append({
            "mode": "perk",
            "title": p["brand"].upper(),
            "main": f"{p['progress']}/{p['target']}",
            "sub": p["reward"],
            "pct": pct,
            "spent": spent,
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
        margin: 0 -16px;
        padding-left: 16px;
        padding-right: 16px;
    }
    .pulse-deck::-webkit-scrollbar { display: none; }
    .pulse-card {
        flex: 0 0 auto;
        scroll-snap-align: start;
        min-width: 140px;
        width: calc(25% - 9px);
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
    .pulse-card[data-brand="ai"] .pulse-card-inner { --glow-color: rgba(255, 255, 255, 0.25); }
    .pulse-card[data-brand="system"] .pulse-card-inner { --glow-color: rgba(255, 255, 255, 0.3); }

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
        # Show reward text (no arrow)
        reward = slot.get("sub", "")
        bottom = f'<div class="pulse-card-sub" style="font-family:JetBrains Mono;font-size:11px;color:{sub_color};text-shadow:{text_shadow};">{reward}</div>'
    elif mode == "ai":
        bottom = f'<div class="pulse-card-sub" style="font-family:JetBrains Mono;font-size:11px;color:{sub_color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><span style="color:{accent};">●</span> {slot["sub"]}</div>'
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
    return f'<div class="pulse-card" data-brand="{brand_key}"><div class="pulse-card-inner" style="{card_style}"><div style="display:flex;justify-content:space-between;align-items:center;"><span class="pulse-card-title" style="{title_style}">{slot["title"]}</span>{icon_html}</div>{main_html}{bottom}{progress_bar}</div></div>'


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

    /* Mobile: scrollable tabs */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
            -webkit-mask-image: linear-gradient(to right, black 85%, transparent 100%);
            mask-image: linear-gradient(to right, black 85%, transparent 100%);
        }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
        .stTabs [data-baseweb="tab"] {
            font-size: 12px !important;
            padding: 8px 12px !important;
            white-space: nowrap;
        }
        [data-baseweb="tab-panel"] button {
            padding: 8px 10px !important;
        }
        [data-baseweb="tab-panel"] button p {
            font-size: 11px !important;
        }
    }
    @media (max-width: 480px) {
        .stTabs [data-baseweb="tab"] {
            font-size: 11px !important;
            padding: 6px 10px !important;
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
    categories = {
        "Send & Pay": [
            ("Send USDC", "Help me send USDC to someone", True),
            ("Pay Bills", "Help me pay a bill with crypto", True),
            ("Phone Top-up", "I need to add minutes to my phone", True),
            ("Schedule", "I want to set up a recurring payment", True),
        ],
        "Earn": [
            ("Earn Yield", "Lend idle USDC on Aave, earn ~4% APY", False),
            ("Swap to ETH", "Swap USDC to ETH at best rates", False),
            ("Stack Sats", "Buy Bitcoin directly, no exchange needed", False),
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
            ("Alerts", "Set up balance alerts and spending notifications", False),
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
            <div style="font-family: 'Inter'; font-weight: 300; color: white; font-size: 20px; letter-spacing: -0.02em;">Authentication Required</div>
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

    # 6. CHAT SECTION - Hairline divider
    st.markdown("<div style='height: 40px; border-bottom: 1px solid rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Welcome state (if no messages yet)
    if not st.session_state.messages:
        wallet_short = ChainUtils.format_address(st.session_state.wallet_address) if st.session_state.wallet_address else "..."
        # Floating data points
        c1, c2, c3 = st.columns(3)
        with c1:
            render_fashion_card("Wallet", wallet_short)
        with c2:
            render_fashion_card("Network", "Arc")
        with c3:
            render_fashion_card("Status", "Active", "●", "#22c55e")

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        # Show modules when no messages
        render_modules()

    # Render chat history - pure text, minimal
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            safe_content = html.escape(msg['content'])
            if msg["role"] == "assistant":
                # AI: Light gray, thin weight
                st.markdown(f"<div style='color: #ccc; font-family: Inter; font-weight: 300; font-size: 15px; line-height: 1.7;'>{safe_content}</div>", unsafe_allow_html=True)
            else:
                # User: White, clean
                st.markdown(f"<div style='color: white; font-family: Inter; font-size: 15px; line-height: 1.6;'>{safe_content}</div>", unsafe_allow_html=True)

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
                st.markdown(f"<div style='color: white; font-family: Inter; font-size: 15px;'>{html.escape(prompt)}</div>", unsafe_allow_html=True)

    # 9. PROCESS MESSAGE (Streaming)
    if prompt:
        with st.chat_message("assistant"):
            # Create empty container for streaming output
            response_container = st.empty()
            message_success = False
            response = ""

            try:
                # Agent initialization logic
                if not st.session_state.get("agent"):
                    try:
                        agent = create_agent_func()
                        if agent:
                            st.session_state.agent = agent
                    except Exception:
                        pass

                if not st.session_state.get("agent"):
                    # Handle missing agent
                    from api_key_setup import check_api_key_status
                    has_key, provider = check_api_key_status()
                    if not has_key:
                        response = "**System Offline:** API Key required in Settings."
                    else:
                        response = "**Initializing:** Please wait..."
                    response_container.markdown(f"<div style='color: #ccc; font-family: Inter; font-weight: 300; font-size: 15px; line-height: 1.7;'>{html.escape(response)}</div>", unsafe_allow_html=True)
                else:
                    # Process with LangChain + Streaming
                    from langchain_core.messages import HumanMessage, AIMessage
                    history = []
                    for m in st.session_state.messages[:-1]:
                        if m["role"] == "user":
                            history.append(HumanMessage(content=m["content"]))
                        else:
                            history.append(AIMessage(content=m["content"]))

                    # Create streaming callback handler
                    stream_handler = StreamlitTokenHandler(response_container)

                    # Invoke with streaming callback
                    result = st.session_state.agent.invoke(
                        {"input": prompt, "chat_history": history},
                        config={"callbacks": [stream_handler]}
                    )

                    # Get final response (prefer streamed text, fallback to result)
                    response = stream_handler.get_final_text() or result.get("output", "Error processing request.")
                    message_success = True

                    # Final render without cursor
                    response_container.markdown(f"<div style='color: #ccc; font-family: Inter; font-weight: 300; font-size: 15px; line-height: 1.7;'>{html.escape(response)}</div>", unsafe_allow_html=True)

            except Exception as e:
                response = f"**System Error:** {str(e)}"
                response_container.markdown(f"<div style='color: #ccc; font-family: Inter; font-weight: 300; font-size: 15px; line-height: 1.7;'>{html.escape(response)}</div>", unsafe_allow_html=True)

            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": response})

            if message_success and llm_config.get("using_free_tier"):
                FreeTier.increment_usage(user_id)
