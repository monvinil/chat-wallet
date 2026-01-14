"""
Streamlined onboarding flow for Chat Wallet
Clean, professional UX with minimal friction
"""

import streamlit as st
from settings_manager import SettingsManager


def show_onboarding():
    """
    Check if onboarding is complete.
    Returns True if ready to chat, False if needs setup.
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return False

    # Check if API key is configured
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))

    # If API key configured, onboarding complete
    if has_api_key:
        return True

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


def show_step_1_welcome():
    """Step 1: Welcome the user and explain what's next"""
    st.markdown("### Almost there")
    st.progress(0.5, text="Step 1 of 2: Wallet created")
    st.divider()

    st.markdown("""
#### Your wallet is ready

Your self-custodial wallet has been created and encrypted. You control the private keys—no one else can access your funds.

**Supported networks:** Base, Arbitrum, Polygon

**One more step:** Connect an AI provider to enable the chat assistant. We recommend Google Gemini—it's free and takes about 30 seconds to set up.
""")

    if st.button("Continue", type="primary", use_container_width=True):
        st.session_state.onboarding_step = 2


def show_step_2_connect_ai(user_id: str):
    """Step 2: Connect AI provider"""
    from api_key_setup import show_api_key_setup_modal, check_api_key_status

    st.markdown("### Connect AI provider")
    st.progress(1.0, text="Step 2 of 2: AI setup")
    st.divider()

    # Check if already configured
    has_key, provider = check_api_key_status()

    if has_key:
        # Show success state
        provider_labels = {
            "google": ("Google Gemini", "◆"),
            "anthropic": ("Anthropic Claude", "◆"),
            "openai": ("OpenAI GPT", "◆")
        }
        provider_name, icon = provider_labels.get(provider, ("AI Provider", "◆"))

        st.success(f"{icon} Connected to {provider_name}")

        # Show celebration once
        if not st.session_state.get("_api_setup_celebration_shown"):
            st.balloons()
            st.session_state._api_setup_celebration_shown = True

        st.markdown("**Setup complete.** You can now manage your wallet through conversation.")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Change provider", use_container_width=True):
                st.session_state._api_setup_celebration_shown = False
                show_api_key_setup_modal()
        with col2:
            if st.button("Start chatting", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True

        return True

    # Show API key setup prompt
    st.markdown("""
#### Get a free Google Gemini API key

The chat assistant requires an AI provider. Google Gemini is free and works great:

1. Visit [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **Get API Key** → **Create in new project**
4. Copy the key and paste it below

No credit card required. Includes 1,500 requests per day.
""")

    if st.button("Connect AI provider", type="primary", use_container_width=True, key="connect_ai_main"):
        show_api_key_setup_modal()

    return False
