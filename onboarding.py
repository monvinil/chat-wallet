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

    Priority:
    1. Gemini OAuth (user signed in with Google - free)
    2. User's own API key
    3. Free tier API key (if app has GOOGLE_API_KEY)
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return False

    # Check if user has API access (own key, OAuth, or free tier)
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))
    has_oauth = llm_config.get("using_oauth", False)

    # If API access available, ready to chat
    if has_api_key or has_oauth:
        # Show first-time welcome for new users (just signed up)
        if st.session_state.get("just_signed_up") and not st.session_state.get("_welcome_shown"):
            show_welcome_message(llm_config)
            st.session_state._welcome_shown = True
        return True

    # No API access - show setup flow
    # Quick start mode - skip welcome, go straight to AI setup
    if st.session_state.get("quick_start_active"):
        st.session_state.onboarding_step = 2

    # Initialize step if not set
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1

    # Step 1: Welcome (only for regular signups, not quick start)
    if st.session_state.onboarding_step == 1:
        show_step_1_welcome()
        return False

    # Step 2: AI Setup (Google Sign-in or API key)
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
    """Step 2: Connect AI - Google sign-in or API key"""
    import os
    from api_key_setup import show_api_key_setup_modal, check_api_key_status
    from gemini_oauth import GeminiOAuth

    st.markdown("### Almost there!")
    st.progress(1.0, text="Step 2 of 2")

    # Check if already configured (API key or OAuth)
    has_key, provider = check_api_key_status()
    has_oauth = GeminiOAuth.is_connected(user_id)

    if has_key or has_oauth:
        if has_oauth:
            email = GeminiOAuth.get_connection_email(user_id)
            st.success(f"Connected with Google ({email})")
        else:
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

    # Check if Google OAuth is configured (env vars exist)
    oauth_available = bool(os.getenv("GOOGLE_OAUTH_CLIENT_ID"))

    st.markdown("""
To chat with your wallet, sign in with Google (free and instant):
""")

    if oauth_available:
        # Primary: Sign in with Google
        if st.button("Sign in with Google", type="primary", use_container_width=True, key="google_signin_main"):
            app_url = os.getenv("APP_URL", "http://localhost:8501")
            redirect_uri = f"{app_url}/oauth/callback"

            auth_url = GeminiOAuth.get_oauth_url(user_id, redirect_uri)
            if auth_url:
                st.markdown(f"[Click here to sign in with Google]({auth_url})")
                st.caption("Uses your Google account's free Gemini quota")

        st.caption("One click, no API keys needed")
    else:
        # Fallback if OAuth not configured: API key flow
        st.markdown("""
1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Get API Key** → **Create in new project**
3. Come back and paste it here
""")

        if st.button("Add my API key", type="primary", use_container_width=True, key="connect_ai_main"):
            show_api_key_setup_modal()

    with st.expander("Other options"):
        if oauth_available:
            st.caption("**API Key** — Paste your own Google API key")
            if st.button("Use API key instead", key="use_api_key"):
                show_api_key_setup_modal()
        st.caption("**Claude** — Best quality (paid)")
        st.caption("**GPT** — Popular choice (paid)")
        st.caption("You can change this anytime in Settings.")

    return False
