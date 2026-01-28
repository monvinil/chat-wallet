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
    TEXT_MUTED: str = "#52525b"
    TEXT_GHOST: str = "#3f3f46"

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
