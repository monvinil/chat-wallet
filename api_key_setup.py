"""
API key setup experience for Chat Wallet
V12 "Liquid Silver" - Config modal with void aesthetic
"""

import streamlit as st
from settings_manager import SettingsManager


def validate_anthropic_key(api_key: str) -> tuple[bool, str]:
    """
    Validate Anthropic API key by making a test request.
    Returns: (is_valid, message)
    """
    if not api_key or not api_key.startswith("sk-ant-"):
        return False, "Invalid format. Anthropic keys start with 'sk-ant-'"

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

        return True, "Valid API key"

    except Exception as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg or "api key" in error_msg:
            return False, "Invalid API key. Please check and try again."
        elif "credit" in error_msg or "billing" in error_msg:
            return False, "Key is valid but has no credits. Add credits at console.anthropic.com"
        else:
            return False, f"Error: {str(e)[:100]}"


def validate_openai_key(api_key: str) -> tuple[bool, str]:
    """
    Validate OpenAI API key by making a test request.
    Returns: (is_valid, message)
    """
    if not api_key or not api_key.startswith("sk-"):
        return False, "Invalid format. OpenAI keys start with 'sk-'"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

        return True, "Valid API key"

    except Exception as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg or "api key" in error_msg:
            return False, "Invalid API key. Please check and try again."
        elif "quota" in error_msg or "billing" in error_msg:
            return False, "Key is valid but has no credits. Add credits at platform.openai.com"
        else:
            return False, f"Error: {str(e)[:100]}"


@st.dialog("Connect AI Provider", width="large")
def show_api_key_setup_modal():
    """Modal dialog for API key setup - V12 void aesthetic"""

    st.markdown("""
    <div style="margin-bottom: 24px;">
        <div style="font-family: 'Inter'; font-size: 14px; color: #888; line-height: 1.6;">
            Chat Wallet uses your own AI provider to power the assistant. Your conversations stay private—we never see them.
        </div>
        <div style="font-family: 'Inter'; font-size: 13px; color: #666; margin-top: 12px;">
            <strong style="color: #888;">Recommended:</strong> Google Gemini is free and includes 1,500 requests per day.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Provider selection tabs
    tab1, tab2, tab3 = st.tabs(["Google Gemini (Free)", "Anthropic Claude", "OpenAI GPT"])

    with tab1:
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <div style="font-family: 'Inter'; font-size: 15px; font-weight: 400; color: white; margin-bottom: 8px;">Google Gemini</div>
            <div style="font-size: 12px; color: #666; line-height: 1.6;">Free tier with generous limits. No credit card required.</div>
        </div>
        <div style="font-size: 12px; color: #555; line-height: 1.8; margin-bottom: 16px;">
            <span style="color: #888;">To get your API key:</span><br>
            1. Go to <a href="https://aistudio.google.com/apikey" target="_blank" style="color: #888;">aistudio.google.com/apikey</a><br>
            2. Sign in with Google<br>
            3. Click <strong style="color: #888;">Get API Key</strong> → <strong style="color: #888;">Create in new project</strong><br>
            4. Copy the key (starts with "AIza...")
        </div>
        """, unsafe_allow_html=True)

        gemini_key = st.text_input(
            "API Key",
            type="password",
            placeholder="AIza...",
            key="gemini_key_input",
            help="Starts with AIza"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            st.link_button(
                "Get API key",
                "https://aistudio.google.com/apikey",
                use_container_width=True
            )
        with col2:
            if st.button("Save", key="save_gemini", type="primary", use_container_width=True):
                if gemini_key:
                    user_id = st.session_state.get("user_id")
                    SettingsManager.update_llm_settings(
                        user_id,
                        provider="google",
                        api_key=gemini_key,
                        model="gemini-2.0-flash-exp"
                    )

                    st.session_state.api_key_configured = True
                    st.session_state._api_key_just_saved = True

                    st.success("API key saved. Close this dialog to continue.")
                else:
                    st.warning("Please enter an API key")

    with tab2:
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <div style="font-family: 'Inter'; font-size: 15px; font-weight: 400; color: white; margin-bottom: 8px;">Anthropic Claude</div>
            <div style="font-size: 12px; color: #666; line-height: 1.6;">Strong reasoning capabilities. Requires prepaid credits.</div>
        </div>
        <div style="font-size: 12px; color: #555; line-height: 1.8; margin-bottom: 16px;">
            <span style="color: #888;">To get your API key:</span><br>
            1. Go to <a href="https://console.anthropic.com" target="_blank" style="color: #888;">console.anthropic.com</a><br>
            2. Create an account and add credits ($5–10 to start)<br>
            3. Create an API key in Settings → API Keys
        </div>
        """, unsafe_allow_html=True)

        anthropic_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-ant-api03-...",
            key="anthropic_key_input",
            help="Starts with sk-ant-"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            st.link_button(
                "Get API key",
                "https://console.anthropic.com/settings/keys",
                use_container_width=True
            )

        with col2:
            if st.button("Save", key="save_anthropic", type="primary", use_container_width=True):
                if anthropic_key:
                    with st.spinner("Validating..."):
                        is_valid, message = validate_anthropic_key(anthropic_key)

                        user_id = st.session_state.get("user_id")
                        SettingsManager.update_llm_settings(
                            user_id,
                            provider="anthropic",
                            api_key=anthropic_key,
                            model="claude-sonnet-4-20250514"
                        )

                        st.session_state.api_key_configured = True
                        st.session_state._api_key_just_saved = True

                        if is_valid:
                            st.success("API key saved. Close this dialog to continue.")
                        elif "credit" in message.lower():
                            st.warning(f"{message} Key saved anyway—try chatting to test it.")
                        else:
                            st.warning(f"{message} Key saved anyway—try chatting to test it.")
                else:
                    st.warning("Please enter an API key")

    with tab3:
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <div style="font-family: 'Inter'; font-size: 15px; font-weight: 400; color: white; margin-bottom: 8px;">OpenAI GPT</div>
            <div style="font-size: 12px; color: #666; line-height: 1.6;">General-purpose AI with broad capabilities. Requires prepaid credits.</div>
        </div>
        <div style="font-size: 12px; color: #555; line-height: 1.8; margin-bottom: 16px;">
            <span style="color: #888;">To get your API key:</span><br>
            1. Go to <a href="https://platform.openai.com" target="_blank" style="color: #888;">platform.openai.com</a><br>
            2. Create an account and add credits<br>
            3. Create an API key in Settings → API Keys
        </div>
        """, unsafe_allow_html=True)

        openai_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-proj-...",
            key="openai_key_input",
            help="Starts with sk-proj- or sk-"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            st.link_button(
                "Get API key",
                "https://platform.openai.com/api-keys",
                use_container_width=True
            )

        with col2:
            if st.button("Save", key="save_openai", type="primary", use_container_width=True):
                if openai_key:
                    with st.spinner("Validating..."):
                        is_valid, message = validate_openai_key(openai_key)

                        user_id = st.session_state.get("user_id")
                        SettingsManager.update_llm_settings(
                            user_id,
                            provider="openai",
                            api_key=openai_key,
                            model="gpt-4o"
                        )

                        st.session_state.api_key_configured = True
                        st.session_state._api_key_just_saved = True

                        if is_valid:
                            st.success("API key saved. Close this dialog to continue.")
                        elif "quota" in message.lower() or "billing" in message.lower():
                            st.warning(f"{message} Key saved anyway—try chatting to test it.")
                        else:
                            st.warning(f"{message} Key saved anyway—try chatting to test it.")
                else:
                    st.warning("Please enter an API key")


def check_api_key_status() -> tuple[bool, str]:
    """
    Check if user has configured an API key.
    Returns: (has_key, provider_name)
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return False, None

    llm_config = SettingsManager.get_llm_config(user_id)
    has_key = bool(llm_config.get("api_key"))
    provider = llm_config.get("provider", "anthropic")

    return has_key, provider


def show_api_key_banner():
    """Show banner when API key is missing - V12 styling"""
    st.markdown("""
    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 20px; margin: 20px 0;">
        <div style="font-family: 'Inter'; font-size: 14px; color: #888; margin-bottom: 8px;">AI provider required</div>
        <div style="font-size: 13px; color: #555; line-height: 1.6;">
            To use the chat assistant, connect an AI provider. We recommend Google Gemini—it's free and takes 30 seconds to set up.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("Connect AI provider", key="open_api_setup", type="primary", use_container_width=True):
            show_api_key_setup_modal()


def render_api_status_indicator():
    """Show current API provider status - V12 floating text"""
    has_key, provider = check_api_key_status()

    if has_key:
        provider_labels = {
            "google": "Gemini",
            "anthropic": "Claude",
            "openai": "GPT"
        }
        provider_name = provider_labels.get(provider, "AI")
        st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 10px; color: #555;'>● {provider_name}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-family: JetBrains Mono; font-size: 10px; color: #444;'>○ No AI connected</div>", unsafe_allow_html=True)
