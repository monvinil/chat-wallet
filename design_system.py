"""
USDChat Design System
Unified design tokens and component helpers for consistent UI.

Usage:
    from design_system import DS, ui

    # Access tokens
    color = DS.colors.TEXT_MUTED

    # Render components
    ui.thinking_indicator()
    ui.transaction_card(amount="$50.00", to="0x1234...", network="Base")
"""

from dataclasses import dataclass
from typing import Optional
import streamlit as st


# =============================================================================
# DESIGN TOKENS
# =============================================================================

@dataclass(frozen=True)
class Colors:
    """Color palette - V22 Cinematic Atmosphere"""
    # Backgrounds
    BG_VOID: str = "#09090b"
    BG_SURFACE: str = "#18181b"
    BG_ELEVATED: str = "#27272a"
    BG_GLASS: str = "rgba(255,255,255,0.03)"
    BG_GLASS_HOVER: str = "rgba(255,255,255,0.05)"

    # Text
    TEXT_PRIMARY: str = "#f4f4f5"
    TEXT_SECONDARY: str = "#a1a1aa"
    TEXT_MUTED: str = "#71717a"  # Improved contrast (was #52525b)
    TEXT_GHOST: str = "#52525b"  # Improved contrast for WCAG AA (was #3f3f46)

    # Borders
    BORDER_GLASS: str = "rgba(255,255,255,0.08)"
    BORDER_HAIRLINE: str = "rgba(255,255,255,0.06)"
    BORDER_SUBTLE: str = "rgba(255,255,255,0.12)"
    BORDER_FOCUS: str = "rgba(255,255,255,0.3)"

    # Accents
    ACCENT_PRIMARY: str = "#ffffff"
    ACCENT_SUCCESS: str = "#22c55e"
    ACCENT_WARNING: str = "#eab308"
    ACCENT_ERROR: str = "#ef4444"
    ACCENT_INFO: str = "#3b82f6"

    # Brand colors for cards
    SPOTIFY_GREEN: str = "#1ed760"
    NETFLIX_RED: str = "#e50914"


@dataclass(frozen=True)
class Spacing:
    """Spacing scale - consistent rhythm"""
    NONE: str = "0"
    XS: str = "4px"
    SM: str = "8px"
    MD: str = "16px"
    LG: str = "24px"
    XL: str = "40px"
    XXL: str = "64px"

    # Semantic spacing
    CARD_PADDING: str = "16px"
    SECTION_GAP: str = "24px"
    INLINE_GAP: str = "8px"


@dataclass(frozen=True)
class Typography:
    """Typography tokens"""
    # Font families
    FONT_SANS: str = "'Inter', -apple-system, sans-serif"
    FONT_MONO: str = "'JetBrains Mono', monospace"

    # Font sizes
    SIZE_XS: str = "10px"
    SIZE_SM: str = "12px"
    SIZE_MD: str = "14px"
    SIZE_LG: str = "16px"
    SIZE_XL: str = "20px"
    SIZE_XXL: str = "28px"

    # Font weights
    WEIGHT_LIGHT: int = 300
    WEIGHT_REGULAR: int = 400
    WEIGHT_MEDIUM: int = 500
    WEIGHT_SEMIBOLD: int = 600
    WEIGHT_BOLD: int = 700

    # Line heights
    LINE_TIGHT: float = 1.2
    LINE_NORMAL: float = 1.5
    LINE_RELAXED: float = 1.7


@dataclass(frozen=True)
class Radius:
    """Border radius scale"""
    NONE: str = "0"
    SM: str = "4px"
    MD: str = "8px"
    LG: str = "12px"
    XL: str = "16px"
    PILL: str = "9999px"


@dataclass(frozen=True)
class Shadows:
    """Shadow definitions"""
    NONE: str = "none"
    SM: str = "0 1px 2px rgba(0,0,0,0.1)"
    MD: str = "0 4px 12px rgba(0,0,0,0.15)"
    LG: str = "0 8px 24px rgba(0,0,0,0.2)"
    GLOW_WHITE: str = "0 0 20px rgba(255,255,255,0.1)"
    GLOW_SUCCESS: str = "0 0 20px rgba(34,197,94,0.2)"
    INSET: str = "inset 0 1px 3px rgba(0,0,0,0.2)"


@dataclass(frozen=True)
class Transitions:
    """Animation/transition tokens"""
    FAST: str = "0.1s ease"
    NORMAL: str = "0.2s ease"
    SLOW: str = "0.3s ease"
    SPRING: str = "0.3s cubic-bezier(0.25, 0.8, 0.25, 1)"


class DesignSystem:
    """Unified access to all design tokens"""
    colors = Colors()
    spacing = Spacing()
    typography = Typography()
    radius = Radius()
    shadows = Shadows()
    transitions = Transitions()


# Shorthand
DS = DesignSystem()


# =============================================================================
# UI COMPONENTS
# =============================================================================

class UIComponents:
    """Reusable UI component renderers"""

    @staticmethod
    def thinking_indicator(message: str = "Thinking") -> None:
        """
        Render an AI thinking indicator with animated dots.
        Call this when waiting for AI response.
        """
        st.markdown(f"""
        <style>
        @keyframes thinking-pulse {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
        }}
        .thinking-container {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 0;
        }}
        .thinking-text {{
            font-family: {DS.typography.FONT_MONO};
            font-size: {DS.typography.SIZE_SM};
            color: {DS.colors.TEXT_MUTED};
            letter-spacing: 0.05em;
        }}
        .thinking-dots {{
            display: flex;
            gap: 4px;
        }}
        .thinking-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: {DS.colors.TEXT_MUTED};
            animation: thinking-pulse 1.4s ease-in-out infinite;
        }}
        .thinking-dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .thinking-dot:nth-child(3) {{ animation-delay: 0.4s; }}
        </style>
        <div class="thinking-container">
            <span class="thinking-text">{message}</span>
            <div class="thinking-dots">
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def transaction_card(
        action: str,
        amount: str,
        to_address: str,
        network: str,
        fee: str,
        total: str,
        estimated_time: str = "~3-5 seconds"
    ) -> None:
        """
        Render a transaction preview card.
        Much better UX than raw JSON dump.
        """
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
            font-size: {DS.typography.SIZE_XXL};
            font-weight: {DS.typography.WEIGHT_LIGHT};
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
            font-size: {DS.typography.SIZE_XS};
            max-width: 200px;
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
            font-weight: {DS.typography.WEIGHT_SEMIBOLD};
            color: {DS.colors.TEXT_PRIMARY};
        }}
        </style>
        <div class="tx-card">
            <div class="tx-header">
                <span class="tx-action">{action}</span>
                <span class="tx-network">{network}</span>
            </div>
            <div class="tx-amount">{amount}</div>
            <div class="tx-row">
                <span class="tx-label">To</span>
                <span class="tx-value address">{to_address}</span>
            </div>
            <div class="tx-row">
                <span class="tx-label">Fee</span>
                <span class="tx-value">{fee}</span>
            </div>
            <div class="tx-row">
                <span class="tx-label">Time</span>
                <span class="tx-value">{estimated_time}</span>
            </div>
            <div class="tx-divider"></div>
            <div class="tx-row">
                <span class="tx-label">Total</span>
                <span class="tx-value tx-total">{total}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def status_badge(
        text: str,
        variant: str = "default"  # default, success, warning, error, info
    ) -> str:
        """Return HTML for a status badge. Use with st.markdown(..., unsafe_allow_html=True)"""
        colors = {
            "default": (DS.colors.TEXT_MUTED, "rgba(255,255,255,0.1)"),
            "success": (DS.colors.ACCENT_SUCCESS, "rgba(34,197,94,0.1)"),
            "warning": (DS.colors.ACCENT_WARNING, "rgba(234,179,8,0.1)"),
            "error": (DS.colors.ACCENT_ERROR, "rgba(239,68,68,0.1)"),
            "info": (DS.colors.ACCENT_INFO, "rgba(59,130,246,0.1)"),
        }
        text_color, bg_color = colors.get(variant, colors["default"])

        return f"""<span style="
            font-family: {DS.typography.FONT_MONO};
            font-size: {DS.typography.SIZE_XS};
            color: {text_color};
            background: {bg_color};
            padding: 4px 10px;
            border-radius: {DS.radius.SM};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        ">{text}</span>"""

    @staticmethod
    def section_header(title: str, subtitle: Optional[str] = None) -> None:
        """Render a consistent section header"""
        html = f"""
        <div style="margin-bottom: {DS.spacing.MD};">
            <div style="
                font-family: {DS.typography.FONT_MONO};
                font-size: {DS.typography.SIZE_XS};
                color: {DS.colors.TEXT_MUTED};
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: 4px;
            ">{title}</div>
        """
        if subtitle:
            html += f"""
            <div style="
                font-family: {DS.typography.FONT_SANS};
                font-size: {DS.typography.SIZE_SM};
                color: {DS.colors.TEXT_GHOST};
            ">{subtitle}</div>
            """
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def empty_state(
        title: str,
        description: str,
        icon: str = "—"
    ) -> None:
        """Render an empty state placeholder"""
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: {DS.spacing.XL} {DS.spacing.MD};
            color: {DS.colors.TEXT_MUTED};
        ">
            <div style="
                font-size: 32px;
                margin-bottom: {DS.spacing.SM};
                opacity: 0.5;
            ">{icon}</div>
            <div style="
                font-family: {DS.typography.FONT_SANS};
                font-size: {DS.typography.SIZE_MD};
                color: {DS.colors.TEXT_SECONDARY};
                margin-bottom: 4px;
            ">{title}</div>
            <div style="
                font-family: {DS.typography.FONT_MONO};
                font-size: {DS.typography.SIZE_XS};
                color: {DS.colors.TEXT_GHOST};
            ">{description}</div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def skeleton(variant: str = "text", width: str = "100%", height: Optional[str] = None) -> str:
        """
        Return HTML for a skeleton loader.
        Variants: text, title, card, avatar
        """
        heights = {
            "text": "14px",
            "title": "28px",
            "card": "96px",
            "avatar": "40px",
        }
        h = height or heights.get(variant, "14px")
        radius = DS.radius.PILL if variant == "avatar" else DS.radius.SM

        return f"""
        <div style="
            width: {width};
            height: {h};
            background: linear-gradient(90deg,
                rgba(255,255,255,0.03) 25%,
                rgba(255,255,255,0.08) 50%,
                rgba(255,255,255,0.03) 75%
            );
            background-size: 200% 100%;
            animation: skeleton-shimmer 1.5s ease-in-out infinite;
            border-radius: {radius};
        "></div>
        <style>
        @keyframes skeleton-shimmer {{
            0% {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}
        </style>
        """

    @staticmethod
    def confirmation_buttons(
        approve_label: str = "APPROVE",
        reject_label: str = "CANCEL",
        key_prefix: str = "confirm"
    ) -> Optional[bool]:
        """
        Render approve/reject buttons side by side.
        Returns True if approved, False if rejected, None if no action yet.
        """
        col1, col2 = st.columns(2)
        with col1:
            if st.button(reject_label, key=f"{key_prefix}_reject", use_container_width=True):
                return False
        with col2:
            if st.button(approve_label, key=f"{key_prefix}_approve", type="primary", use_container_width=True):
                return True
        return None

    @staticmethod
    def info_row(label: str, value: str, mono: bool = False) -> None:
        """Render a label-value pair in a row"""
        value_font = DS.typography.FONT_MONO if mono else DS.typography.FONT_SANS
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid {DS.colors.BORDER_HAIRLINE};
        ">
            <span style="
                font-family: {DS.typography.FONT_MONO};
                font-size: {DS.typography.SIZE_SM};
                color: {DS.colors.TEXT_MUTED};
            ">{label}</span>
            <span style="
                font-family: {value_font};
                font-size: {DS.typography.SIZE_SM};
                color: {DS.colors.TEXT_SECONDARY};
            ">{value}</span>
        </div>
        """, unsafe_allow_html=True)


# Shorthand
ui = UIComponents()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def inject_custom_css(css: str) -> None:
    """Inject custom CSS into the page"""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def format_address(address: str, chars: int = 6) -> str:
    """Format a blockchain address with ellipsis"""
    if not address or len(address) < chars * 2:
        return address or ""
    return f"{address[:chars]}...{address[-4:]}"


def format_amount(amount: float, decimals: int = 2, prefix: str = "$") -> str:
    """Format a monetary amount"""
    return f"{prefix}{amount:,.{decimals}f}"


# =============================================================================
# ENHANCED UI COMPONENTS - V2
# =============================================================================

class EnhancedUI:
    """Enhanced UI components with animations and polish"""

    @staticmethod
    def hero_balance(balance: float, change_24h: float = 0.0, network: str = "Arc") -> None:
        """
        Subtle hero balance display - minimal, not clumsy.
        Shows balance with optional 24h change indicator.
        """
        change_color = DS.colors.ACCENT_SUCCESS if change_24h >= 0 else DS.colors.ACCENT_ERROR
        change_sign = "+" if change_24h >= 0 else ""
        change_display = f"{change_sign}{change_24h:.2f}%" if change_24h != 0 else ""

        st.markdown(f"""
        <style>
        .hero-balance {{
            display: flex;
            align-items: baseline;
            gap: 12px;
            padding: 8px 0 16px 0;
        }}
        .hero-amount {{
            font-family: {DS.typography.FONT_SANS};
            font-size: 32px;
            font-weight: 300;
            color: {DS.colors.TEXT_PRIMARY};
            letter-spacing: -0.03em;
        }}
        .hero-currency {{
            font-family: {DS.typography.FONT_MONO};
            font-size: 12px;
            color: {DS.colors.TEXT_MUTED};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .hero-change {{
            font-family: {DS.typography.FONT_MONO};
            font-size: 11px;
            color: {change_color};
            padding: 2px 6px;
            background: {change_color}15;
            border-radius: {DS.radius.SM};
        }}
        @media (max-width: 480px) {{
            .hero-amount {{ font-size: 28px; }}
        }}
        </style>
        <div class="hero-balance">
            <span class="hero-amount">${balance:,.2f}</span>
            <span class="hero-currency">USDC</span>
            {f'<span class="hero-change">{change_display}</span>' if change_display else ''}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def success_animation(message: str = "Success!", show_confetti: bool = False) -> None:
        """
        Animated success state with checkmark and optional confetti.
        """
        confetti_css = ""
        confetti_html = ""
        if show_confetti:
            confetti_css = """
            @keyframes confetti-fall {
                0% { transform: translateY(-100%) rotate(0deg); opacity: 1; }
                100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
            }
            .confetti-piece {
                position: fixed;
                width: 8px;
                height: 8px;
                top: -10px;
                animation: confetti-fall 3s ease-out forwards;
                z-index: 9999;
                pointer-events: none;
            }
            """
            # Generate confetti pieces
            import random
            colors = ["#22c55e", "#3b82f6", "#eab308", "#f472b6", "#8b5cf6"]
            confetti_html = "".join([
                f'<div class="confetti-piece" style="left: {random.randint(5, 95)}%; background: {random.choice(colors)}; animation-delay: {random.random() * 0.5}s; border-radius: {random.choice(["0", "50%"])};"></div>'
                for _ in range(20)
            ])

        st.markdown(f"""
        <style>
        @keyframes success-pop {{
            0% {{ transform: scale(0); opacity: 0; }}
            50% {{ transform: scale(1.2); }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        @keyframes success-check {{
            0% {{ stroke-dashoffset: 50; }}
            100% {{ stroke-dashoffset: 0; }}
        }}
        .success-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            padding: 32px;
            animation: success-pop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
        }}
        .success-circle {{
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: {DS.colors.ACCENT_SUCCESS}20;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .success-check {{
            stroke: {DS.colors.ACCENT_SUCCESS};
            stroke-width: 3;
            stroke-linecap: round;
            stroke-linejoin: round;
            fill: none;
            stroke-dasharray: 50;
            animation: success-check 0.5s ease-out 0.2s forwards;
            stroke-dashoffset: 50;
        }}
        .success-text {{
            font-family: {DS.typography.FONT_SANS};
            font-size: {DS.typography.SIZE_LG};
            color: {DS.colors.TEXT_PRIMARY};
            font-weight: {DS.typography.WEIGHT_MEDIUM};
        }}
        {confetti_css}
        </style>
        {confetti_html}
        <div class="success-container">
            <div class="success-circle">
                <svg width="28" height="28" viewBox="0 0 24 24">
                    <polyline class="success-check" points="4 12 9 17 20 6"></polyline>
                </svg>
            </div>
            <span class="success-text">{message}</span>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def glass_card(content_html: str, glow_color: str = None) -> None:
        """
        Glassmorphism card with optional brand glow.
        """
        glow_style = f"box-shadow: 0 8px 32px {glow_color}20;" if glow_color else ""

        st.markdown(f"""
        <style>
        .glass-card {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: {DS.radius.LG};
            padding: {DS.spacing.LG};
            position: relative;
            overflow: hidden;
            {glow_style}
        }}
        .glass-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
        }}
        </style>
        <div class="glass-card">
            {content_html}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def empty_chat_prompts(prompts: list) -> str:
        """
        Return HTML for empty chat state with suggested prompts.
        prompts: list of (emoji, title, description, prompt_text)
        Returns HTML that can be used with st.markdown.
        """
        prompts_html = ""
        for emoji, title, desc, prompt in prompts:
            prompts_html += f"""
            <div class="prompt-card" data-prompt="{prompt}">
                <span class="prompt-emoji">{emoji}</span>
                <div class="prompt-content">
                    <div class="prompt-title">{title}</div>
                    <div class="prompt-desc">{desc}</div>
                </div>
            </div>
            """

        return f"""
        <style>
        .empty-chat {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
            gap: 24px;
        }}
        .empty-chat-title {{
            font-family: {DS.typography.FONT_SANS};
            font-size: {DS.typography.SIZE_XL};
            color: {DS.colors.TEXT_PRIMARY};
            font-weight: {DS.typography.WEIGHT_LIGHT};
            letter-spacing: -0.02em;
        }}
        .empty-chat-subtitle {{
            font-family: {DS.typography.FONT_MONO};
            font-size: {DS.typography.SIZE_XS};
            color: {DS.colors.TEXT_MUTED};
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}
        .prompts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            width: 100%;
            max-width: 500px;
            margin-top: 16px;
        }}
        @media (max-width: 480px) {{
            .prompts-grid {{ grid-template-columns: 1fr; }}
        }}
        .prompt-card {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 16px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: {DS.radius.MD};
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .prompt-card:hover {{
            background: rgba(255,255,255,0.06);
            border-color: rgba(255,255,255,0.12);
            transform: translateY(-2px);
        }}
        .prompt-emoji {{
            font-size: 20px;
            line-height: 1;
        }}
        .prompt-content {{
            flex: 1;
        }}
        .prompt-title {{
            font-family: {DS.typography.FONT_SANS};
            font-size: {DS.typography.SIZE_SM};
            color: {DS.colors.TEXT_PRIMARY};
            font-weight: {DS.typography.WEIGHT_MEDIUM};
            margin-bottom: 4px;
        }}
        .prompt-desc {{
            font-family: {DS.typography.FONT_MONO};
            font-size: {DS.typography.SIZE_XS};
            color: {DS.colors.TEXT_MUTED};
        }}
        </style>
        <div class="empty-chat">
            <div class="empty-chat-subtitle">What can I help you with?</div>
            <div class="prompts-grid">
                {prompts_html}
            </div>
        </div>
        """

    @staticmethod
    def inject_micro_interactions() -> None:
        """
        Inject global CSS for micro-interactions: button presses, hover states, etc.
        Call once per page.
        """
        st.markdown("""
        <style>
        /* Button press effect */
        .stButton > button {
            transition: transform 0.1s ease, box-shadow 0.1s ease !important;
        }
        .stButton > button:active {
            transform: scale(0.97) !important;
        }
        .stButton > button:hover:not(:disabled) {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }

        /* Primary button glow on hover */
        .stButton > button[kind="primary"]:hover:not(:disabled),
        .stButton > button[data-baseweb="button"][kind="primary"]:hover:not(:disabled) {
            box-shadow: 0 4px 20px rgba(255,255,255,0.15) !important;
        }

        /* Input focus ring */
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: rgba(255,255,255,0.3) !important;
            box-shadow: 0 0 0 2px rgba(255,255,255,0.1) !important;
        }

        /* Card hover lift */
        .hoverable {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .hoverable:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }

        /* Smooth fade-in for new elements */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
            animation: fadeIn 0.3s ease forwards;
        }

        /* Pulse for live indicators */
        @keyframes livePulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .live-indicator {
            animation: livePulse 2s ease-in-out infinite;
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def status_pill(text: str, status: str = "default", pulse: bool = False) -> str:
        """
        Return HTML for an enhanced status pill with optional pulse animation.
        status: default, online, offline, pending, success, error
        """
        status_styles = {
            "default": (DS.colors.TEXT_MUTED, "rgba(255,255,255,0.1)"),
            "online": (DS.colors.ACCENT_SUCCESS, "rgba(34,197,94,0.15)"),
            "offline": (DS.colors.TEXT_GHOST, "rgba(255,255,255,0.05)"),
            "pending": (DS.colors.ACCENT_WARNING, "rgba(234,179,8,0.15)"),
            "success": (DS.colors.ACCENT_SUCCESS, "rgba(34,197,94,0.15)"),
            "error": (DS.colors.ACCENT_ERROR, "rgba(239,68,68,0.15)"),
        }
        color, bg = status_styles.get(status, status_styles["default"])
        pulse_class = "live-indicator" if pulse else ""
        dot_html = f'<span style="width: 6px; height: 6px; border-radius: 50%; background: {color}; margin-right: 6px;" class="{pulse_class}"></span>' if status in ["online", "pending"] else ""

        return f"""<span style="
            display: inline-flex;
            align-items: center;
            font-family: {DS.typography.FONT_MONO};
            font-size: {DS.typography.SIZE_XS};
            color: {color};
            background: {bg};
            padding: 4px 10px;
            border-radius: {DS.radius.PILL};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        ">{dot_html}{text}</span>"""

    @staticmethod
    def mobile_nav(active: str = "chat") -> None:
        """
        Render mobile bottom navigation bar.
        Only shows on mobile (<768px).
        active: chat, wallet, history, settings
        """
        items = [
            ("chat", "💬", "Chat"),
            ("wallet", "💰", "Wallet"),
            ("history", "📋", "History"),
            ("settings", "⚙️", "Settings"),
        ]

        nav_items_html = ""
        for key, icon, label in items:
            is_active = key == active
            active_style = f"color: {DS.colors.TEXT_PRIMARY};" if is_active else f"color: {DS.colors.TEXT_MUTED};"
            indicator = f'<div style="width: 4px; height: 4px; border-radius: 50%; background: {DS.colors.ACCENT_SUCCESS}; margin-top: 4px;"></div>' if is_active else ""
            nav_items_html += f"""
            <div class="mobile-nav-item" data-nav="{key}">
                <span style="font-size: 20px; {active_style}">{icon}</span>
                <span style="font-size: 10px; {active_style}">{label}</span>
                {indicator}
            </div>
            """

        st.markdown(f"""
        <style>
        .mobile-nav {{
            display: none;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(9, 9, 11, 0.95);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255,255,255,0.08);
            padding: 8px 0 env(safe-area-inset-bottom, 8px) 0;
            z-index: 9999;
        }}
        .mobile-nav-inner {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            max-width: 400px;
            margin: 0 auto;
        }}
        .mobile-nav-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 2px;
            padding: 8px 16px;
            cursor: pointer;
            transition: transform 0.1s ease;
        }}
        .mobile-nav-item:active {{
            transform: scale(0.95);
        }}
        @media (max-width: 768px) {{
            .mobile-nav {{
                display: block;
            }}
            /* Add padding to main content to prevent overlap */
            .main .block-container {{
                padding-bottom: 80px !important;
            }}
        }}
        </style>
        <div class="mobile-nav">
            <div class="mobile-nav-inner">
                {nav_items_html}
            </div>
        </div>
        """, unsafe_allow_html=True)


# Shorthand for enhanced UI
enhanced_ui = EnhancedUI()
