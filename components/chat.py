"""
Chat interface component for Chat Wallet
Main chat UI, quick actions, and suggested actions
"""

import streamlit as st
from chain_utils import ChainUtils


def render_quick_actions():
    """Render quick action chips above chat"""
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


def render_suggested_actions():
    """
    Render capability library with thematic tabs.
    Organized by use case for easy discovery.
    """
    # Categories: (emoji, label, prompt, is_live)
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
    # Same categories as render_suggested_actions
    categories = {
        "Send & Pay": [
            "Send USDC",
            "Pay Bills",
            "Phone Top-up",
            "Schedule",
        ],
        "Earn": [
            "Earn Yield",
            "Swap to ETH",
            "Stack Sats",
        ],
        "Tools": [
            "Get Domain",
            "VPN",
            "eSIM",
            "Alerts",
        ],
        "Shopping": [
            "Amazon",
            "Target",
            "Walmart",
            "Best Buy",
            "Sephora",
        ],
        "Food": [
            "DoorDash",
            "Uber Eats",
            "Starbucks",
            "Chipotle",
            "Grubhub",
        ],
        "Streaming": [
            "Netflix",
            "Spotify",
            "Disney+",
            "Hulu",
            "Apple TV+",
        ],
        "Gaming": [
            "PlayStation",
            "Xbox",
            "Steam",
            "Nintendo",
            "Roblox",
        ],
    }

    tabs = st.tabs(list(categories.keys()))

    for tab_idx, (category_name, items) in enumerate(categories.items()):
        with tabs[tab_idx]:
            cols = st.columns(min(len(items), 4))
            for i, label in enumerate(items):
                col_idx = i % 4
                with cols[col_idx]:
                    st.button(label, key=f"preview_{tab_idx}_{i}", disabled=True,
                              use_container_width=True, help="Sign up to use")


def chat_interface(create_agent_func):
    """
    Main chat interface

    Args:
        create_agent_func: Function to create the AI agent (passed from app.py)
    """
    st.title("Chat Wallet")
    st.caption("Manage your wallet through conversation")

    # No wallet - show welcome and prompt to sign in/up
    if not st.session_state.wallet_address:
        with st.chat_message("assistant"):
            st.markdown("""**Welcome to Chat Wallet**

Your crypto wallet that speaks your language. Buy gift cards, pay bills, and send money—all through simple conversation.

Sign up or log in to get started.
""")

        # Show preview of capabilities (all disabled for exploration)
        st.divider()
        render_suggested_actions_preview()

        # Disabled chat input
        st.chat_input("Message...", disabled=True, key="preview_input")
        return

    # If wallet is locked, show a message to unlock
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.info("**Wallet locked** — Enter your password in the sidebar to unlock your wallet and start chatting.")
        st.chat_input("Message...", disabled=True, key="locked_input")
        return

    # Show onboarding flow if user hasn't completed setup
    from onboarding import show_onboarding
    if not show_onboarding():
        # User is still in onboarding, don't show chat
        return

    # Check if API key is configured (own key or free tier)
    from api_key_setup import show_api_key_banner, check_api_key_status
    from free_tier import FreeTier
    from settings_manager import SettingsManager

    user_id = st.session_state.get("user_id")
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))

    if not has_api_key:
        # No API access - check if free tier exhausted
        if FreeTier.is_available() and not FreeTier.has_quota(user_id):
            FreeTier.show_upgrade_prompt()
        else:
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

    # Show free tier status if using it
    if llm_config.get("using_free_tier"):
        remaining = llm_config.get("remaining_messages", 0)
        if remaining <= 10:
            st.warning(f"{remaining} free messages left. Add your API key in Settings.")
        else:
            st.caption(f"{remaining} free messages remaining")

    # Quick action chips for logged-in users (only after onboarding complete)
    render_quick_actions()

    st.divider()

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

    # Suggested actions - scrollable pills above chat input
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
            with st.spinner("Thinking..."):
                message_success = False
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
                        message_success = True  # Only count successful agent responses

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

                # Increment free tier usage only on successful messages
                if message_success and llm_config.get("using_free_tier"):
                    FreeTier.increment_usage(user_id)

    # Welcome message for logged in users (only shown after onboarding complete)
    if not st.session_state.messages:
        welcome = f"""Wallet connected: `{ChainUtils.format_address(st.session_state.wallet_address)}`

**Try these commands:**
- "What's my balance?"
- "Send $20 to 0x..."
- "Show my deposit address"
- "Buy a $25 Amazon gift card"
- "Register mydomain.com"
- "Get Mullvad VPN"

What would you like to do?
"""
        st.session_state.messages.append({"role": "assistant", "content": welcome})
