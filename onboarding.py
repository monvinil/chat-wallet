"""
Simplified onboarding flow - single step API key setup
No st.rerun() calls for better performance
"""

import streamlit as st
from settings_manager import SettingsManager


def show_onboarding():
    """
    Simple onboarding - just check if API key is configured.
    Returns True if ready to chat, False if needs API key.
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
    """Step 1: Welcome and explain what just happened"""
    st.markdown("### Setup Your Wallet")
    st.progress(0.5, text="Step 1 of 2")
    st.divider()

    st.markdown("""
## ✅ Wallet Created

**Your wallet is ready:**
- Secure address generated (only you control the private keys)
- Multi-chain support enabled (Base, Arbitrum, Polygon)
- Encrypted and backed up to cloud

**Next: Get your FREE AI key (30 seconds)**

Chat Wallet needs a Google Gemini API key to power the chat assistant:
- Completely **FREE** (no credit card needed)
- Just sign in with Google
- 1500 requests/day included free
""")

    if st.button("Continue →", type="primary", use_container_width=True):
        st.session_state.onboarding_step = 2


def show_step_2_connect_ai(user_id: str):
    """Step 2: Connect AI provider"""
    from api_key_setup import show_api_key_setup_modal, check_api_key_status

    st.markdown("### Setup Your Wallet")
    st.progress(1.0, text="Step 2 of 2")
    st.divider()

    # Check if already configured
    has_key, provider = check_api_key_status()

    if has_key:
        # Show success state
        if provider == "google":
            provider_name = "Google Gemini"
            emoji = "🆓"
        elif provider == "anthropic":
            provider_name = "Anthropic"
            emoji = "🟣"
        else:
            provider_name = "OpenAI"
            emoji = "🟢"

        st.success(f"{emoji} **Connected:** {provider_name}")

        # Show balloons once
        if not st.session_state.get("_api_setup_celebration_shown"):
            st.balloons()
            st.session_state._api_setup_celebration_shown = True

        st.info("✅ **Setup Complete!** You can now use the chat to manage your wallet.")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Change Provider", use_container_width=True):
                st.session_state._api_setup_celebration_shown = False
                show_api_key_setup_modal()
        with col2:
            if st.button("Start Chatting →", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True

        return True  # Onboarding complete

    # Show API key setup prompt
    st.markdown("""
## Connect AI Provider

Get your **FREE** Google Gemini API key:

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with Google
3. Click "Get API Key" → Create in new project
4. Copy key and paste below

**No credit card required** - 1500 requests/day free!
""")

    # Show modal button
    if st.button("🔗 Connect AI Provider", type="primary", use_container_width=True, key="connect_ai_main"):
        show_api_key_setup_modal()

    # Skip option
    st.markdown("---")
    if st.button("Skip for now (testing only)", use_container_width=True):
        st.session_state.onboarding_complete = True

    return False  # Still in onboarding
