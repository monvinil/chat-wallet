"""
Chat02 Onboarding Flow
Streamlined for instant chat access with free tier
"""

import streamlit as st
from settings_manager import SettingsManager


def show_onboarding():
    """
    Check if onboarding is complete.
    Returns True if ready to chat, False if needs setup.

    With free tier, users can chat immediately after signup.
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return False

    # Check if user has API access (own key OR free tier)
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))

    # If API key available (own or free tier), ready to chat
    if has_api_key:
        # Show first-time welcome for new users (just signed up)
        if st.session_state.get("just_signed_up") and not st.session_state.get("_welcome_shown"):
            show_welcome_message(llm_config)
            st.session_state._welcome_shown = True
        return True

    # No API access - show setup flow
    # Quick start mode - skip welcome, go straight to API setup
    if st.session_state.get("quick_start_active"):
        st.session_state.onboarding_step = 2

    # Initialize step if not set
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1

    # Step 1: Welcome (only for regular signups, not quick start)
    if st.session_state.onboarding_step == 1:
        show_step_1_welcome()
        return False

    # Step 2: API Key Setup
    return show_step_2_connect_ai(user_id)


def show_welcome_message(llm_config: dict):
    """Show brief welcome for users with free tier access"""
    if llm_config.get("using_free_tier"):
        remaining = llm_config.get("remaining_messages", 50)
        st.success(f"You're ready to chat! ({remaining} free messages)")
    else:
        st.success("You're connected and ready to chat!")


def show_step_1_welcome():
    """Step 1: Warm wallet confirmation - educational, flowing"""
    st.markdown("### Your wallet is ready")
    st.progress(0.5, text="Step 1 of 2")

    # Show wallet address as accessible detail
    address = st.session_state.get("wallet_address", "")
    if address:
        with st.expander("Your wallet address", expanded=False):
            st.code(address)
            st.caption("This is your payment address")

    st.markdown("""
Great! Your wallet is secured and only you can access it.

One more step: connect an AI assistant to start chatting.
""")

    if st.button("Continue", type="primary", use_container_width=True):
        st.session_state.onboarding_step = 2


def show_step_2_connect_ai(user_id: str):
    """Step 2: Connect AI - flowing, educational"""
    from api_key_setup import show_api_key_setup_modal, check_api_key_status

    st.markdown("### Almost there!")
    st.progress(1.0, text="Step 2 of 2")

    # Check if already configured
    has_key, provider = check_api_key_status()

    if has_key:
        provider_labels = {
            "google": "Gemini",
            "anthropic": "Claude",
            "openai": "GPT"
        }
        model_name = provider_labels.get(provider, "AI")

        st.success(f"Connected to {model_name}")

        # Clear celebration - satisfying moment
        if not st.session_state.get("_api_setup_celebration_shown"):
            st.balloons()
            st.session_state._api_setup_celebration_shown = True

        st.markdown("You're all set! Start typing to buy gift cards, pay bills, send money, and more.")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Change provider", use_container_width=True):
                st.session_state._api_setup_celebration_shown = False
                show_api_key_setup_modal()
        with col2:
            if st.button("Start chatting", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True

        return True

    st.markdown("""
To chat with your wallet, you need a free AI key from Google:

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Get API Key** → **Create in new project**
3. Come back and paste it here
""")

    if st.button("Add my API key", type="primary", use_container_width=True, key="connect_ai_main"):
        show_api_key_setup_modal()

    with st.expander("Other options"):
        st.caption("**Claude** — Best quality (paid)")
        st.caption("**GPT** — Popular choice (paid)")
        st.caption("You can change this anytime in Settings.")

    return False
