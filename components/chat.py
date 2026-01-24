"""
Chat interface component for Chat Wallet
2026 Cyber-Physical Design - Bento Grid Layout
"""

import streamlit as st
from chain_utils import ChainUtils


def render_quick_actions():
    """Render quick action capsules - Dynamic Island style"""
    st.markdown("""
    <div style="
        display: flex;
        justify-content: center;
        gap: 8px;
        margin-bottom: 16px;
    ">
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Send", key="quick_send", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I want to send money"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col2:
        if st.button("Gift Card", key="quick_giftcard", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Show me gift cards"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col3:
        if st.button("Pay Bill", key="quick_bill", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Help me pay a bill"})
            st.session_state._quick_action_triggered = True
            st.rerun()


def render_bento_card(title: str, items: list, tab_idx: int, is_preview: bool = False):
    """Render a Bento-style capability card"""
    # Create a 2x2 or 2x3 grid based on item count
    cols_per_row = 2
    rows = (len(items) + cols_per_row - 1) // cols_per_row

    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            item_idx = row * cols_per_row + col_idx
            if item_idx < len(items):
                with cols[col_idx]:
                    if is_preview:
                        label = items[item_idx]
                        st.button(
                            label,
                            key=f"preview_{tab_idx}_{item_idx}",
                            disabled=True,
                            use_container_width=True,
                            help="Sign up to use"
                        )
                    else:
                        label, prompt, is_live = items[item_idx]
                        if is_live:
                            if st.button(label, key=f"cap_{tab_idx}_{item_idx}", use_container_width=True):
                                st.session_state.messages.append({"role": "user", "content": prompt})
                                st.session_state._quick_action_triggered = True
                                st.rerun()
                        else:
                            st.button(
                                label,
                                key=f"cap_{tab_idx}_{item_idx}",
                                disabled=True,
                                use_container_width=True,
                                help=prompt
                            )


def render_suggested_actions():
    """
    Render capability library with thematic tabs - Bento Grid style.
    Organized by use case for easy discovery.
    """
    # Categories: (label, prompt, is_live)
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
        ],
        "Food": [
            ("DoorDash", "I want a DoorDash gift card", True),
            ("Uber Eats", "I want Uber Eats gift card credits", True),
            ("Starbucks", "Get me a Starbucks gift card", True),
            ("Chipotle", "I want a Chipotle gift card", True),
        ],
        "Streaming": [
            ("Netflix", "I want a Netflix gift card", True),
            ("Spotify", "Get me a Spotify gift card", True),
            ("Disney+", "I want a Disney+ gift card", False),
            ("Hulu", "Show me Hulu gift cards", False),
        ],
        "Gaming": [
            ("PlayStation", "Show me PlayStation gift cards", True),
            ("Xbox", "I want an Xbox gift card", True),
            ("Steam", "Get me a Steam gift card", True),
            ("Nintendo", "I want a Nintendo eShop card", True),
        ],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            render_bento_card(category_name, items, tab_idx, is_preview=False)


def render_suggested_actions_preview():
    """
    Render capability preview for pre-login users.
    All buttons disabled - just for exploration.
    """
    categories = {
        "Send & Pay": ["Send USDC", "Pay Bills", "Phone Top-up", "Schedule"],
        "Earn": ["Earn Yield", "Swap to ETH", "Stack Sats"],
        "Tools": ["Get Domain", "VPN", "eSIM", "Alerts"],
        "Shopping": ["Amazon", "Target", "Walmart", "Best Buy"],
        "Food": ["DoorDash", "Uber Eats", "Starbucks", "Chipotle"],
        "Streaming": ["Netflix", "Spotify", "Disney+", "Hulu"],
        "Gaming": ["PlayStation", "Xbox", "Steam", "Nintendo"],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            render_bento_card(category_name, items, tab_idx, is_preview=True)


def render_ai_status_capsule(llm_config: dict, user_id: str = None):
    """Render AI connection status as a HUD capsule"""
    from gemini_oauth import GeminiOAuth

    if llm_config.get("using_oauth"):
        email = GeminiOAuth.get_connection_email(user_id)
        status_text = f"Google ({email})" if email else "Google"
        status_color = "#00FF9D"
    elif llm_config.get("using_free_tier"):
        status_text = "Gemini Free"
        status_color = "#00D4FF"
    elif llm_config.get("api_key"):
        provider = llm_config.get("provider", "").title()
        status_text = provider or "Connected"
        status_color = "#00FF9D"
    else:
        status_text = "Not Connected"
        status_color = "#FF3D71"

    st.markdown(f"""
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: rgba({int(status_color[1:3], 16)}, {int(status_color[3:5], 16)}, {int(status_color[5:7], 16)}, 0.08);
        border: 1px solid rgba({int(status_color[1:3], 16)}, {int(status_color[3:5], 16)}, {int(status_color[5:7], 16)}, 0.2);
        border-radius: 100px;
        margin-bottom: 12px;
    ">
        <div style="
            width: 5px;
            height: 5px;
            background: {status_color};
            border-radius: 50%;
            box-shadow: 0 0 6px {status_color};
        "></div>
        <span style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.625rem;
            color: {status_color};
            letter-spacing: 0.05em;
        ">{status_text}</span>
    </div>
    """, unsafe_allow_html=True)


def render_welcome_hero():
    """Render welcome hero section for non-logged-in users"""
    st.markdown("""
    <div style="
        text-align: center;
        padding: 40px 0;
    ">
        <div style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2rem;
            font-weight: 600;
            color: #F0F4F8;
            letter-spacing: -0.03em;
            margin-bottom: 12px;
        ">Chat Wallet</div>
        <div style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.9375rem;
            color: #64748B;
            max-width: 400px;
            margin: 0 auto;
            line-height: 1.6;
        ">Your crypto wallet that speaks your language. Buy gift cards, pay bills, and send money—all through simple conversation.</div>
    </div>
    """, unsafe_allow_html=True)


def render_terminal_header():
    """Render terminal-style header with connection info"""
    wallet_addr = ChainUtils.format_address(st.session_state.wallet_address)

    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        background: linear-gradient(135deg, rgba(20, 25, 32, 0.9) 0%, rgba(15, 19, 24, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        margin-bottom: 16px;
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                width: 8px;
                height: 8px;
                background: #00FF9D;
                border-radius: 50%;
                box-shadow: 0 0 8px #00FF9D;
            "></div>
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.75rem;
                color: #94A3B8;
            ">CONNECTED</span>
        </div>
        <span style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: #64748B;
            font-variant-numeric: tabular-nums;
        ">{wallet_addr}</span>
    </div>
    """, unsafe_allow_html=True)


def chat_interface(create_agent_func):
    """
    Main chat interface - 2026 Cyber-Physical Design

    Args:
        create_agent_func: Function to create the AI agent (passed from app.py)
    """
    # No wallet - show welcome hero
    if not st.session_state.wallet_address:
        render_welcome_hero()

        with st.chat_message("assistant"):
            st.markdown("""Sign up or log in to get started with your personal crypto assistant.""")

        # Show preview of capabilities (all disabled for exploration)
        st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
        render_suggested_actions_preview()

        # Disabled chat input
        st.chat_input("Message...", disabled=True, key="preview_input")
        return

    # If wallet is locked, show a message to unlock
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.markdown("""
        <div style="
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 16px 20px;
            background: rgba(255, 184, 0, 0.08);
            border: 1px solid rgba(255, 184, 0, 0.15);
            border-radius: 8px;
            margin-bottom: 16px;
        ">
            <div style="
                width: 8px;
                height: 8px;
                background: #FFB800;
                border-radius: 50%;
            "></div>
            <span style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.875rem;
                color: #FFB800;
            ">Wallet locked — Enter your password in the sidebar to continue</span>
        </div>
        """, unsafe_allow_html=True)
        st.chat_input("Message...", disabled=True, key="locked_input")
        return

    # Show onboarding flow if user hasn't completed setup
    from onboarding import show_onboarding
    if not show_onboarding():
        # User is still in onboarding, don't show chat
        return

    # Check if API key is configured (own key, OAuth, or free tier)
    from api_key_setup import show_api_key_banner, check_api_key_status
    from free_tier import FreeTier
    from settings_manager import SettingsManager
    from gemini_oauth import GeminiOAuth

    user_id = st.session_state.get("user_id")
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))
    has_oauth = llm_config.get("using_oauth", False)

    if not has_api_key and not has_oauth:
        # No API access - show setup prompt
        show_api_key_banner()
        return

    # If API key was just configured, force agent re-initialization
    if has_api_key and st.session_state.get("_api_key_just_saved"):
        st.session_state.agent = None  # Force recreation
        st.session_state._agent_initializing = False
        st.session_state._api_key_just_saved = False  # Clear flag
        # Clear LLM config cache to pick up new key
        cache_key = f"_llm_config_{user_id}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]

    # Terminal header with connection info
    render_terminal_header()

    # AI status capsule
    render_ai_status_capsule(llm_config, user_id)

    # Quick action capsules
    render_quick_actions()

    # Normal logged-in chat interface
    # Show messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Determine if we need to process a message (from chat input OR quick action)
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        # Quick action button was clicked - get the last user message
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # Suggested actions - Bento grid tabs
    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
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
            with st.spinner(""):
                try:
                    # Safety check: ensure agent is initialized
                    if not st.session_state.get("agent"):
                        # Try to initialize agent now
                        try:
                            agent = create_agent_func()
                            if agent:
                                st.session_state.agent = agent
                        except Exception:
                            pass

                    if not st.session_state.get("agent"):
                        # Still no agent - provide helpful guidance
                        from api_key_setup import check_api_key_status
                        has_key, provider = check_api_key_status()

                        if not has_key:
                            response = """**AI provider not connected**

To use the chat assistant, you need to connect an AI provider first.

Click **Settings** in the sidebar, then go to **AI Provider** to add your API key. We recommend Google Gemini—it's free."""
                        else:
                            response = """**AI assistant loading...**

The assistant is still initializing. This usually takes a moment after logging in.

**Try:** Refresh the page (F5) or wait a few seconds and try again."""
                    else:
                        # Lazy import LangChain message types
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

                except Exception as e:
                    error_msg = str(e)

                    # Casual/human error messages
                    if "API key" in error_msg or "credit" in error_msg.lower() or "authentication" in error_msg.lower():
                        response = """Hmm, looks like there's an issue with your AI connection.

Head to **Settings** → **AI Provider** to check your API key. If you're using Google Gemini, you can grab a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)."""
                    elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
                        response = """Whoa, we're going too fast! The AI needs a breather.

Wait a minute and try again, or switch providers in Settings if this keeps happening."""
                    else:
                        response = f"Oops, something went wrong: {error_msg}"

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # Welcome message for logged in users (only shown after onboarding complete)
    if not st.session_state.messages:
        welcome = f"""Connected: `{ChainUtils.format_address(st.session_state.wallet_address)}`

**Try these:**
- "What's my balance?"
- "Send $20 to 0x..."
- "Buy a $25 Amazon gift card"
- "Register mydomain.com"

What would you like to do?
"""
        st.session_state.messages.append({"role": "assistant", "content": welcome})
