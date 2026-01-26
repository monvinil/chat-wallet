"""
Chat02 Onboarding Flow
V12 "Liquid Silver" - The Gateway
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
        st.markdown(f"""
        <div style="color: #888; font-size: 13px; padding: 10px 0;">
            Ready to chat — {remaining} free messages
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="color: #888; font-size: 13px; padding: 10px 0;">
            Connected and ready
        </div>
        """, unsafe_allow_html=True)


def show_step_1_welcome():
    """Step 1: V12 wallet confirmation - centered void"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center;">
            <h2 style="font-weight: 300; margin-bottom: 16px;">Wallet Secured</h2>
            <div style="color: #555; font-size: 13px; line-height: 1.6;">
                One more step — connect an AI to start chatting.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show wallet address
        address = st.session_state.get("wallet_address", "")
        if address:
            st.markdown(f"""
            <div style="text-align: center; margin: 30px 0; font-family: 'JetBrains Mono'; font-size: 11px; color: #444;">
                {address[:8]}...{address[-6:]}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

        if st.button("Continue", type="primary", use_container_width=True):
            st.session_state.onboarding_step = 2


def show_step_2_connect_ai(user_id: str):
    """Step 2: V12 Connect AI - centered void"""
    from api_key_setup import show_api_key_setup_modal, check_api_key_status

    # Check if already configured
    has_key, provider = check_api_key_status()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

        if has_key:
            provider_labels = {
                "google": "Gemini",
                "anthropic": "Claude",
                "openai": "GPT"
            }
            model_name = provider_labels.get(provider, "AI")

            st.markdown(f"""
            <div style="text-align: center;">
                <h2 style="font-weight: 300; margin-bottom: 16px;">Connected</h2>
                <div style="color: #888; font-size: 13px;">{model_name}</div>
            </div>
            """, unsafe_allow_html=True)

            # Celebration
            if not st.session_state.get("_api_setup_celebration_shown"):
                st.balloons()
                st.session_state._api_setup_celebration_shown = True

            st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

            col_a, col_b = st.columns([1, 1])
            with col_a:
                if st.button("Change", use_container_width=True):
                    st.session_state._api_setup_celebration_shown = False
                    show_api_key_setup_modal()
            with col_b:
                if st.button("Start", type="primary", use_container_width=True):
                    st.session_state.onboarding_complete = True

            return True

        st.markdown("""
        <div style="text-align: center;">
            <h2 style="font-weight: 300; margin-bottom: 16px;">Intelligence</h2>
            <div style="color: #555; font-size: 13px; line-height: 1.8;">
                Connect an AI to activate chat commands.<br>
                <a href="https://aistudio.google.com/apikey" target="_blank" style="color: #888;">Get a free key from Google →</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

        if st.button("Connect Provider", type="primary", use_container_width=True, key="connect_ai_main"):
            show_api_key_setup_modal()

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        with st.expander("Other options"):
            st.markdown("""
            <div style="font-size: 12px; color: #555; line-height: 1.8;">
                <strong style="color: #888;">Claude</strong> — Best quality (paid)<br>
                <strong style="color: #888;">GPT</strong> — Popular choice (paid)
            </div>
            """, unsafe_allow_html=True)

    return False
