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
    """Step 1: Bold wallet creation confirmation"""
    st.markdown("### Your wallet is live")
    st.progress(0.5, text="1 of 2")

    # Show wallet address prominently
    address = st.session_state.get("wallet_address", "")
    if address:
        st.code(address)

    st.markdown("""
**Multi-chain.** Works on Base, Arbitrum, Polygon, and Solana from a single seed phrase.

**Self-custodial.** You hold the keys. No one else can access your funds.

One step left: connect an AI to unlock the chat.
""")

    if st.button("Continue", type="primary", use_container_width=True):
        st.session_state.onboarding_step = 2


def show_step_2_connect_ai(user_id: str):
    """Step 2: Connect AI - unlock the superpowers"""
    from api_key_setup import show_api_key_setup_modal, check_api_key_status

    st.markdown("### Power the chat")
    st.progress(1.0, text="2 of 2")

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

        if not st.session_state.get("_api_setup_celebration_shown"):
            st.balloons()
            st.session_state._api_setup_celebration_shown = True

        st.markdown("**Ready.** Start typing—your wallet listens.")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Change provider", use_container_width=True):
                st.session_state._api_setup_celebration_shown = False
                show_api_key_setup_modal()
        with col2:
            if st.button("Start", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True

        return True

    st.markdown("""
The chat needs an AI brain. **Google Gemini is free** and works great.

1. [Get a key here](https://aistudio.google.com/apikey) (takes 30 seconds)
2. Click **Get API Key** → **Create in new project**
3. Paste below
""")

    if st.button("Connect AI", type="primary", use_container_width=True, key="connect_ai_main"):
        show_api_key_setup_modal()

    with st.expander("Use a different provider"):
        st.caption("**Claude** — Best quality (paid)")
        st.caption("**GPT** — Most popular (paid)")

    return False
