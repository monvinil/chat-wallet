"""
USDChat Onboarding Flow
V12 "Liquid Silver" - The Gateway
"""

import streamlit as st
from settings_manager import SettingsManager


def show_onboarding():
    """
    Check if onboarding is complete.
    Returns True if ready to chat, False if needs setup.

    SIMPLIFIED FLOW (v2):
    - If user has API key (own or free tier) -> ready to chat
    - If no API key -> show API setup directly (no intermediate steps)
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

    # No API access - go directly to API setup (skip intermediate welcome)
    # This reduces onboarding from 2 steps to 1
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


def show_step_2_connect_ai(user_id: str):
    """Connect AI - streamlined single-step setup"""
    from api_key_setup import show_api_key_setup_modal, check_api_key_status

    # Check if already configured
    has_key, provider = check_api_key_status()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)

        if has_key:
            provider_labels = {
                "google": "Gemini",
                "anthropic": "Claude",
                "openai": "GPT"
            }
            model_name = provider_labels.get(provider, "AI")

            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 40px; margin-bottom: 16px;">✓</div>
                <h2 style="font-weight: 300; margin-bottom: 8px;">Ready</h2>
                <div style="color: #666; font-size: 12px;">{model_name} connected</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

            if st.button("START CHATTING", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True
                st.session_state.just_signed_up = False
                st.rerun()

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            if st.button("Change provider", use_container_width=True):
                show_api_key_setup_modal()

            return True

        # Not configured yet - show simple setup
        st.markdown("""
        <div style="text-align: center;">
            <h2 style="font-weight: 300; margin-bottom: 12px;">Last step</h2>
            <div style="color: #555; font-size: 13px; line-height: 1.6; max-width: 280px; margin: 0 auto;">
                Connect an AI to power your wallet assistant
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

        # Primary CTA - Google (free)
        if st.button("CONNECT FREE AI", type="primary", use_container_width=True, key="connect_ai_main"):
            show_api_key_setup_modal()

        st.markdown("""
        <div style="text-align: center; margin-top: 12px;">
            <a href="https://aistudio.google.com/apikey" target="_blank"
               style="color: #666; font-size: 11px; text-decoration: none;">
                Get a free Google API key →
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # Secondary options collapsed
        with st.expander("Use Claude or GPT instead"):
            st.markdown("""
            <div style="font-size: 12px; color: #555; line-height: 1.8; padding: 8px 0;">
                <strong style="color: #888;">Claude</strong> — Best reasoning (paid)<br>
                <strong style="color: #888;">GPT-4</strong> — Popular choice (paid)
            </div>
            """, unsafe_allow_html=True)
            if st.button("Configure paid provider", use_container_width=True):
                show_api_key_setup_modal()

    return False
