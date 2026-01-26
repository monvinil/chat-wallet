"""
Chat Interface Component
V11 Design: "The Monolith" - Depth & Materiality
Frosted glass, cobalt accent, rounded corners with depth.
"""

import html
import streamlit as st
from chain_utils import ChainUtils


def _escape_content(content: str) -> str:
    """Escape HTML in content to prevent XSS while preserving markdown formatting"""
    # Escape HTML special chars to prevent script injection
    return html.escape(content)


# --- HELPER: GLASS CARD (V11 Depth) ---
def render_raw_card(label, value, icon=None):
    """
    Renders a card with V11 frosted glass styling.
    Features rounded corners and subtle depth.
    """
    icon_html = f'<span style="margin-right: 8px; opacity: 0.5;">{icon}</span>' if icon else ''
    st.markdown(f"""
    <div style="
        background: rgba(10, 10, 10, 0.8);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    ">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; margin-bottom: 8px; letter-spacing: 0.08em; text-transform: uppercase;">{label}</div>
        <div style="font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 400; color: white;">{icon_html}{value}</div>
    </div>
    """, unsafe_allow_html=True)


# Keep alias for backwards compatibility
render_luxe_card = render_raw_card
render_fashion_card = render_raw_card


# --- HEADER: V10 SPLIT BRAND ---
def render_header():
    """
    V10 brand header with split weight typography.
    CHAT (light) / 02 (bold) layout.
    """
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        <div style="margin-top: 10px;">
            <h1 style="font-size: 48px; line-height: 1; margin: 0; letter-spacing: 0.2em;">
                <span style="font-weight: 300;">CHAT</span><span style="font-weight: 800;">02</span>
            </h1>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; margin-top: 10px; letter-spacing: 0.08em;">
            <div style="margin-bottom: 6px;">V11.0</div>
            <div style="
                display: inline-block;
                background: rgba(37, 99, 235, 0.1);
                color: #2563eb;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 9px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            ">ONLINE</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)


# --- CALLBACKS FOR ACTION BUTTONS ---
def _on_deposit_click():
    st.session_state.show_deposit_modal = True


def _on_send_click():
    st.session_state.show_send_modal = True


def _on_quick_action(prompt: str):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state._quick_action_triggered = True


# --- ACTIONS: V11 ACTION STRIP ---
def render_action_strip():
    """
    V11 action strip with rounded glass buttons.
    Uses on_click callbacks to avoid double-render from explicit st.rerun().
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.button("DEPOSIT ASSETS", key="quick_deposit", type="primary",
                  use_container_width=True, on_click=_on_deposit_click)

    with col2:
        st.button("SEND FUNDS", key="quick_send", use_container_width=True,
                  on_click=_on_send_click)

    with col3:
        st.button("GIFT CARDS", key="quick_giftcard", use_container_width=True,
                  on_click=_on_quick_action, args=("Show me gift cards",))

    with col4:
        st.button("PAY BILLS", key="quick_bill", use_container_width=True,
                  on_click=_on_quick_action, args=("Help me pay a bill",))


# Keep alias for backwards compatibility
render_action_deck = render_action_strip


# --- MODULES: V11 GLASS CATEGORIES ---
def render_modules():
    """
    Render capability library with V11 glass styling.
    """
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)

    # V10 streamlined categories
    categories = {
        "FINANCE": [
            ("SEND_USDC", "Help me send USDC to someone", True),
            ("PAY_BILLS", "Help me pay a bill with crypto", True),
            ("PHONE_TOPUP", "I need to add minutes to my phone", True),
            ("EARN_YIELD", "Lend idle USDC on Aave, earn ~4% APY", False),
        ],
        "LIFESTYLE": [
            ("AMAZON", "I want to buy an Amazon gift card", True),
            ("DOORDASH", "I want a DoorDash gift card", True),
            ("NETFLIX", "I want a Netflix gift card", True),
            ("SPOTIFY", "Get me a Spotify gift card", True),
            ("STARBUCKS", "Get me a Starbucks gift card", True),
            ("PLAYSTATION", "Show me PlayStation gift cards", True),
        ],
        "PRIVACY": [
            ("VPN", "I want a Mullvad VPN subscription", True),
            ("DOMAIN", "I want to register a domain", True),
            ("ESIM", "I need an international eSIM", False),
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
                        st.button(label, key=f"mod_{tab_idx}_{i}", use_container_width=True,
                                  on_click=_on_quick_action, args=(prompt,))
                    else:
                        st.button(label, key=f"mod_{tab_idx}_{i}", disabled=True,
                                  use_container_width=True, help=prompt)


def render_modules_preview():
    """
    Render capability preview for pre-login users (all disabled).
    """
    categories = {
        "FINANCE": ["SEND_USDC", "PAY_BILLS", "PHONE_TOPUP", "EARN_YIELD"],
        "LIFESTYLE": ["AMAZON", "DOORDASH", "NETFLIX", "SPOTIFY", "STARBUCKS", "PLAYSTATION"],
        "PRIVACY": ["VPN", "DOMAIN", "ESIM"],
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
    """
    Main chat interface with V11 glass depth styling.
    """
    # 1. HEADER
    render_header()

    # 2. HANDLE PRE-LOGIN STATE
    if not st.session_state.wallet_address:
        st.markdown("""
        <div style="
            background: rgba(10, 10, 10, 0.8);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 50px 0;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        ">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; letter-spacing: 0.1em; margin-bottom: 12px;">SYSTEM_STATUS</div>
            <div style="font-family: 'Inter', sans-serif; font-weight: 300; color: white; font-size: 20px; letter-spacing: -0.02em;">AUTHENTICATION REQUIRED</div>
        </div>
        """, unsafe_allow_html=True)
        render_modules_preview()
        st.chat_input("AUTHENTICATE TO CONTINUE_", disabled=True, key="preview_input")
        return

    # 3. HANDLE LOCKED STATE
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.markdown("""
        <div style="
            background: rgba(10, 10, 10, 0.8);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 40px 0;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        ">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; letter-spacing: 0.1em; margin-bottom: 8px;">CONSOLE_LOCKED</div>
            <div style="font-family: 'Inter', sans-serif; font-weight: 300; color: #a3a3a3; font-size: 14px;">Enter access key in sidebar</div>
        </div>
        """, unsafe_allow_html=True)
        st.chat_input("LOCKED_", disabled=True, key="locked_input")
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

    # Show free tier status
    if llm_config.get("using_free_tier"):
        remaining = llm_config.get("remaining_messages", 0)
        if remaining <= 10:
            st.warning(f"{remaining} free messages remaining")
        else:
            st.caption(f"{remaining} FREE MESSAGES REMAINING")

    # 5. ACTION STRIP
    render_action_strip()

    # 6. CHAT SECTION
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Welcome state (if no messages yet)
    if not st.session_state.messages:
        wallet_short = ChainUtils.format_address(st.session_state.wallet_address) if st.session_state.wallet_address else "..."
        st.markdown(f"""
        <div style="
            display: flex;
            gap: 40px;
            background: rgba(10, 10, 10, 0.6);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
        ">
            <div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; letter-spacing: 0.1em; margin-bottom: 4px;">WALLET_ID</div>
                <div style="color: white; font-size: 13px; font-family: 'JetBrains Mono', monospace;">{wallet_short}</div>
            </div>
            <div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; letter-spacing: 0.1em; margin-bottom: 4px;">NETWORK</div>
                <div style="color: white; font-size: 13px; font-family: 'JetBrains Mono', monospace;">BASE_MAINNET</div>
            </div>
            <div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; letter-spacing: 0.1em; margin-bottom: 4px;">STATUS</div>
                <div style="color: #2563eb; font-size: 13px; font-family: 'JetBrains Mono', monospace;">ACTIVE</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Show modules when no messages
        render_modules()

    # Render chat history with V10 styling
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # Escape content to prevent XSS
            safe_content = _escape_content(msg["content"])
            if msg["role"] == "assistant":
                # AI = Clean chrome typography
                st.markdown(f"<div style='color: #e5e5e5; font-family: Inter, sans-serif; font-weight: 400; font-size: 15px; line-height: 1.7;'>{safe_content}</div>", unsafe_allow_html=True)
            else:
                # User = Cobalt accent with V11 depth
                st.markdown(f"""
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; letter-spacing: 0.08em; margin-bottom: 4px;">INPUT</div>
                    <div style="color: #2563eb; font-family: Inter, sans-serif; font-size: 14px; font-weight: 500;">{safe_content}</div>
                </div>
                """, unsafe_allow_html=True)

    # 7. HANDLE INPUT LOGIC
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # 8. INPUT FIELD
    if not prompt:
        prompt = st.chat_input("COMMAND_")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                safe_prompt = _escape_content(prompt)
                st.markdown(f"""
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; letter-spacing: 0.08em; margin-bottom: 4px;">INPUT</div>
                    <div style="color: #2563eb; font-family: Inter, sans-serif; font-size: 14px; font-weight: 500;">{safe_prompt}</div>
                </div>
                """, unsafe_allow_html=True)

    # 9. PROCESS MESSAGE
    if prompt:
        with st.chat_message("assistant"):
            with st.spinner("PROCESSING_"):
                message_success = False
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
                            response = "**SYSTEM OFFLINE:** API Key required in Settings."
                        else:
                            response = "**INITIALIZING:** Please wait..."
                    else:
                        # Process with LangChain
                        from langchain_core.messages import HumanMessage, AIMessage
                        history = []
                        for m in st.session_state.messages[:-1]:
                            if m["role"] == "user":
                                history.append(HumanMessage(content=m["content"]))
                            else:
                                history.append(AIMessage(content=m["content"]))

                        result = st.session_state.agent.invoke({
                            "input": prompt,
                            "chat_history": history
                        })
                        response = result.get("output", "Error processing request.")
                        message_success = True

                except Exception as e:
                    response = f"**SYSTEM ERROR:** {str(e)}"

                safe_response = _escape_content(response)
                st.markdown(f"<div style='color: #e5e5e5; font-family: Inter, sans-serif; font-weight: 400; font-size: 15px; line-height: 1.7;'>{safe_response}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response})

                if message_success and llm_config.get("using_free_tier"):
                    FreeTier.increment_usage(user_id)
