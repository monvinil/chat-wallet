"""
Chat02 Onboarding Flow
V10 "Brutalist Fintech" - The Manifest
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
        st.markdown(f"""
        <div style="
            border: 1px solid #1a1a1a;
            padding: 20px;
            margin-bottom: 20px;
        ">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                        letter-spacing: 0.15em; margin-bottom: 8px;">SYSTEM_READY</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 14px; color: white;">
                {remaining} free messages available
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            border: 1px solid #3b82f6;
            padding: 20px;
            margin-bottom: 20px;
        ">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #3b82f6;
                        letter-spacing: 0.15em; margin-bottom: 8px;">SYSTEM_ONLINE</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 14px; color: white;">
                Connected and ready
            </div>
        </div>
        """, unsafe_allow_html=True)


def show_step_1_welcome():
    """Step 1: V10 Brutalist wallet confirmation"""
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 8px;">INITIALIZATION_01</div>
        <div style="font-family: 'Inter', sans-serif; font-size: 28px; font-weight: 300;
                    color: white; letter-spacing: 0.1em;">WALLET SECURED</div>
    </div>
    """, unsafe_allow_html=True)

    # Progress indicator - V10 brutalist style
    st.markdown("""
    <div style="display: flex; gap: 8px; margin-bottom: 2rem;">
        <div style="flex: 1; height: 2px; background: #3b82f6;"></div>
        <div style="flex: 1; height: 2px; background: #262626;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Show wallet address
    address = st.session_state.get("wallet_address", "")
    if address:
        st.markdown(f"""
        <div style="
            border: 1px solid #1a1a1a;
            padding: 20px;
            margin-bottom: 2rem;
            position: relative;
        ">
            <div style="position: absolute; top: 0; left: 0; width: 8px; height: 8px; border-top: 1px solid #404040; border-left: 1px solid #404040;"></div>
            <div style="position: absolute; top: 0; right: 0; width: 8px; height: 8px; border-top: 1px solid #404040; border-right: 1px solid #404040;"></div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                        letter-spacing: 0.15em; margin-bottom: 8px;">WALLET_ADDRESS</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #a3a3a3;
                        word-break: break-all;">{address}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family: 'Inter', sans-serif; font-size: 14px; color: #a3a3a3;
                line-height: 1.7; margin-bottom: 2rem;">
        Your wallet is encrypted and secured. Only you control access.
        <br><br>
        One more step: connect an AI engine to enable chat commands.
    </div>
    """, unsafe_allow_html=True)

    if st.button("CONTINUE", type="primary", use_container_width=True):
        st.session_state.onboarding_step = 2


def show_step_2_connect_ai(user_id: str):
    """Step 2: V10 Brutalist AI connection"""
    from api_key_setup import show_api_key_setup_modal, check_api_key_status

    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 8px;">INITIALIZATION_02</div>
        <div style="font-family: 'Inter', sans-serif; font-size: 28px; font-weight: 300;
                    color: white; letter-spacing: 0.1em;">CONNECT INTELLIGENCE</div>
    </div>
    """, unsafe_allow_html=True)

    # Progress indicator - V10 brutalist style
    st.markdown("""
    <div style="display: flex; gap: 8px; margin-bottom: 2rem;">
        <div style="flex: 1; height: 2px; background: #3b82f6;"></div>
        <div style="flex: 1; height: 2px; background: #3b82f6;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Check if already configured
    has_key, provider = check_api_key_status()

    if has_key:
        provider_labels = {
            "google": "GEMINI",
            "anthropic": "CLAUDE",
            "openai": "GPT"
        }
        model_name = provider_labels.get(provider, "AI")

        st.markdown(f"""
        <div style="
            border: 1px solid #3b82f6;
            padding: 20px;
            margin-bottom: 2rem;
        ">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #3b82f6;
                        letter-spacing: 0.15em; margin-bottom: 8px;">ENGINE_CONNECTED</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 16px; color: white;">{model_name}</div>
        </div>
        """, unsafe_allow_html=True)

        # Clear celebration
        if not st.session_state.get("_api_setup_celebration_shown"):
            st.balloons()
            st.session_state._api_setup_celebration_shown = True

        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; font-size: 14px; color: #a3a3a3;
                    line-height: 1.7; margin-bottom: 2rem;">
            System ready. Type commands to execute transactions, purchase gift cards, pay bills.
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("CHANGE ENGINE", use_container_width=True):
                st.session_state._api_setup_celebration_shown = False
                show_api_key_setup_modal()
        with col2:
            if st.button("INITIALIZE", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True

        return True

    # Not connected - show setup instructions
    st.markdown("""
    <div style="
        border: 1px solid #1a1a1a;
        padding: 24px;
        margin-bottom: 2rem;
        position: relative;
    ">
        <div style="position: absolute; top: 0; left: 0; width: 8px; height: 8px; border-top: 1px solid #404040; border-left: 1px solid #404040;"></div>
        <div style="position: absolute; top: 0; right: 0; width: 8px; height: 8px; border-top: 1px solid #404040; border-right: 1px solid #404040;"></div>
        <div style="position: absolute; bottom: 0; left: 0; width: 8px; height: 8px; border-bottom: 1px solid #404040; border-left: 1px solid #404040;"></div>
        <div style="position: absolute; bottom: 0; right: 0; width: 8px; height: 8px; border-bottom: 1px solid #404040; border-right: 1px solid #404040;"></div>

        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 16px;">SETUP_INSTRUCTIONS</div>

        <div style="font-family: 'Inter', sans-serif; font-size: 13px; color: #a3a3a3; line-height: 1.8;">
            <div style="margin-bottom: 12px;">
                <span style="color: #3b82f6; font-family: 'JetBrains Mono', monospace;">01</span>
                &nbsp;&nbsp;Navigate to <a href="https://aistudio.google.com/apikey" target="_blank"
                   style="color: #3b82f6; text-decoration: none;">aistudio.google.com/apikey</a>
            </div>
            <div style="margin-bottom: 12px;">
                <span style="color: #3b82f6; font-family: 'JetBrains Mono', monospace;">02</span>
                &nbsp;&nbsp;Select <strong style="color: white;">Get API Key</strong> then <strong style="color: white;">Create in new project</strong>
            </div>
            <div>
                <span style="color: #3b82f6; font-family: 'JetBrains Mono', monospace;">03</span>
                &nbsp;&nbsp;Return and input key below
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("INPUT API KEY", type="primary", use_container_width=True, key="connect_ai_main"):
        show_api_key_setup_modal()

    with st.expander("ALTERNATIVE ENGINES"):
        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #525252; line-height: 1.8;">
            <div style="margin-bottom: 8px;"><strong style="color: #a3a3a3;">CLAUDE</strong> — Premium quality (paid)</div>
            <div style="margin-bottom: 8px;"><strong style="color: #a3a3a3;">GPT</strong> — Industry standard (paid)</div>
            <div style="color: #404040;">Configurable in Settings at any time.</div>
        </div>
        """, unsafe_allow_html=True)

    return False
