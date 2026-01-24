"""
Chat interface component for Chat Wallet
V3 "Opinionated Luxury" - Cyber-Physical Design System
"""

import streamlit as st
from chain_utils import ChainUtils


def render_hud_header():
    """Render HUD-style header with system status"""
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
        <div>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
                         letter-spacing: 0.1em; color: #71717a; text-transform: uppercase;">
                CHAT WALLET
            </span>
            <h1 style="font-size: 1.75rem; font-weight: 600; margin: 0.25rem 0 0 0; color: #e4e4e7;">
                Terminal
            </h1>
        </div>
        <div style="background: rgba(163, 230, 53, 0.1); border: 1px solid rgba(163, 230, 53, 0.3);
                    border-radius: 100px; padding: 0.35rem 0.75rem; display: inline-flex; align-items: center; gap: 0.5rem;">
            <span style="width: 6px; height: 6px; background: #a3e635; border-radius: 50%;
                         box-shadow: 0 0 8px #a3e635;"></span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
                         letter-spacing: 0.05em; color: #a3e635; text-transform: uppercase;">
                SYSTEM ACTIVE
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_quick_actions():
    """Render 4-column Bento grid quick actions"""
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
                letter-spacing: 0.15em; color: #52525b; margin-bottom: 0.75rem; text-transform: uppercase;">
        QUICK ACTIONS
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("DEPOSIT", key="quick_deposit", use_container_width=True):
            st.session_state.show_deposit_modal = True
            st.rerun()

    with col2:
        if st.button("SEND", key="quick_send", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I want to send money"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col3:
        if st.button("PERKS", key="quick_perks", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Show me gift cards"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col4:
        if st.button("BILLS", key="quick_bills", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Help me pay a bill"})
            st.session_state._quick_action_triggered = True
            st.rerun()


def render_suggested_actions():
    """
    Render capability library with V3 thematic tabs.
    Simplified categories: FINANCE, LIFESTYLE, TOOLS
    """
    categories = {
        "FINANCE": [
            ("Send USDC", "Help me send USDC to someone", True),
            ("Pay Bills", "Help me pay a bill with crypto", True),
            ("Top-up", "I need to add minutes to my phone", True),
            ("Schedule", "I want to set up a recurring payment", True),
        ],
        "LIFESTYLE": [
            ("Amazon", "I want to buy an Amazon gift card", True),
            ("DoorDash", "I want a DoorDash gift card", True),
            ("Netflix", "I want a Netflix gift card", True),
            ("Spotify", "Get me a Spotify gift card", True),
            ("Steam", "Get me a Steam gift card", True),
            ("PlayStation", "Show me PlayStation gift cards", True),
            ("Starbucks", "Get me a Starbucks gift card", True),
            ("Target", "Show me Target gift cards", True),
        ],
        "TOOLS": [
            ("Domain", "I want to register a domain", True),
            ("VPN", "I want a Mullvad VPN subscription", True),
            ("eSIM", "I need an international eSIM", False),
            ("Alerts", "Set up balance alerts", False),
        ],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            cols = st.columns(4)
            for i, (label, prompt, is_live) in enumerate(items):
                col_idx = i % 4
                with cols[col_idx]:
                    if is_live:
                        if st.button(label, key=f"cap_{tab_idx}_{i}", use_container_width=True):
                            st.session_state.messages.append({"role": "user", "content": prompt})
                            st.session_state._quick_action_triggered = True
                            st.rerun()
                    else:
                        st.button(label, key=f"cap_{tab_idx}_{i}", disabled=True,
                                  use_container_width=True, help=prompt)


def render_suggested_actions_preview():
    """
    Render capability preview for pre-login users.
    All buttons disabled - just for exploration.
    """
    categories = {
        "FINANCE": ["Send USDC", "Pay Bills", "Top-up", "Schedule"],
        "LIFESTYLE": ["Amazon", "DoorDash", "Netflix", "Spotify", "Steam", "PlayStation", "Starbucks", "Target"],
        "TOOLS": ["Domain", "VPN", "eSIM", "Alerts"],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            cols = st.columns(4)
            for i, label in enumerate(items):
                col_idx = i % 4
                with cols[col_idx]:
                    st.button(label, key=f"preview_{tab_idx}_{i}", disabled=True,
                              use_container_width=True, help="Sign up to use")


def chat_interface(create_agent_func):
    """
    Main chat interface - V3 Terminal Design

    Args:
        create_agent_func: Function to create the AI agent (passed from app.py)
    """
    # No wallet - show welcome and prompt to sign in/up
    if not st.session_state.wallet_address:
        render_hud_header()

        # Terminal-style welcome
        st.markdown("""
        <div style="background: rgba(10, 10, 11, 0.8); border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
                        letter-spacing: 0.1em; color: #52525b; margin-bottom: 1rem;">
                WELCOME
            </div>
            <p style="color: #e4e4e7; margin-bottom: 1rem; line-height: 1.6;">
                Your crypto wallet that speaks your language. Buy gift cards, pay bills,
                and send money—all through simple conversation.
            </p>
            <p style="color: #71717a; font-size: 0.875rem;">
                Sign up or log in to initialize your session.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Show preview of capabilities (all disabled for exploration)
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        render_suggested_actions_preview()

        # Disabled chat input
        st.chat_input("Message...", disabled=True, key="preview_input")
        return

    # If wallet is locked, show a message to unlock
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        render_hud_header()
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 12px; padding: 1.25rem; margin: 1rem 0;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
                        letter-spacing: 0.1em; color: #ef4444; margin-bottom: 0.5rem;">
                SESSION LOCKED
            </div>
            <p style="color: #e4e4e7; margin: 0;">
                Enter your password in the sidebar to unlock your wallet and resume.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.chat_input("Message...", disabled=True, key="locked_input")
        return

    # Show onboarding flow if user hasn't completed setup
    from onboarding import show_onboarding
    if not show_onboarding():
        return

    # Check if API key is configured (own key or free tier)
    from api_key_setup import show_api_key_banner, check_api_key_status
    from free_tier import FreeTier
    from settings_manager import SettingsManager

    user_id = st.session_state.get("user_id")
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))

    if not has_api_key:
        if FreeTier.is_available() and not FreeTier.has_quota(user_id):
            FreeTier.show_upgrade_prompt()
        else:
            show_api_key_banner()
        return

    # If API key was just configured, force agent re-initialization
    if has_api_key and st.session_state.get("_api_key_just_saved"):
        st.session_state.agent = None
        st.session_state._agent_initializing = False
        st.session_state._api_key_just_saved = False
        cache_key = f"_llm_config_{user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]

    # HUD Header
    render_hud_header()

    # Show free tier status if using it
    if llm_config.get("using_free_tier"):
        remaining = llm_config.get("remaining_messages", 0)
        if remaining <= 10:
            st.markdown(f"""
            <div style="background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.3);
                        border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem;
                        font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #eab308;">
                {remaining} FREE MESSAGES REMAINING
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
                        letter-spacing: 0.1em; color: #52525b; margin-bottom: 1rem;">
                {remaining} FREE MESSAGES REMAINING
            </div>
            """, unsafe_allow_html=True)

    # Quick action bento grid
    render_quick_actions()

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Show messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Determine if we need to process a message (from chat input OR quick action)
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # Suggested actions
    render_suggested_actions()

    # Chat input (only if not processing quick action)
    if not prompt:
        prompt = st.chat_input("Message...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

    # Process the message (from either source)
    if prompt:
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                message_success = False
                try:
                    if not st.session_state.get("agent"):
                        try:
                            agent = create_agent_func()
                            if agent:
                                st.session_state.agent = agent
                        except Exception:
                            pass

                    if not st.session_state.get("agent"):
                        from api_key_setup import check_api_key_status
                        has_key, provider = check_api_key_status()

                        if not has_key:
                            response = """**AI provider not connected**

To use the chat assistant, you need to connect an AI provider first.

Click **Settings** in the sidebar, then go to **AI Provider** to add your API key."""
                        else:
                            response = """**AI assistant loading...**

The assistant is still initializing. This usually takes a moment after logging in.

**Try:** Refresh the page or wait a few seconds and try again."""
                    else:
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

                        response = result.get("output", "Sorry, I couldn't process that.")
                        message_success = True

                except Exception as e:
                    error_msg = str(e)

                    if "API key" in error_msg or "credit" in error_msg.lower() or "authentication" in error_msg.lower():
                        response = """Hmm, looks like there's an issue with your AI connection.

Head to **Settings** → **AI Provider** to check your API key."""
                    elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
                        response = """Rate limit reached. Wait a minute and try again."""
                    else:
                        response = f"Error: {error_msg}"

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

                if message_success and llm_config.get("using_free_tier"):
                    FreeTier.increment_usage(user_id)

    # Terminal-style welcome message for logged in users
    if not st.session_state.messages:
        wallet_short = ChainUtils.format_address(st.session_state.wallet_address)
        welcome = f"""<span style="color: #a3e635; font-family: 'JetBrains Mono', monospace;">SESSION INITIALIZED</span>

Wallet: `{wallet_short}`

**Available commands:**
- "What's my balance?"
- "Send $20 to 0x..."
- "Buy a $25 Amazon gift card"
- "Register mydomain.com"
- "Get Mullvad VPN"

What would you like to do?"""
        st.session_state.messages.append({"role": "assistant", "content": welcome})
