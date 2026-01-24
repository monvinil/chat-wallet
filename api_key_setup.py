"""
API key setup experience for Chat Wallet
Clean modal interface with clear instructions
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
    """Modal dialog for API key setup"""

    st.markdown("""
Chat Wallet uses your own AI provider to power the assistant. Your conversations stay private—we never see them.

**Recommended:** Google Gemini is free and includes 1,500 requests per day.
""")

    # Provider selection tabs
    tab1, tab2, tab3 = st.tabs(["Google Gemini (Free)", "Anthropic Claude", "OpenAI GPT"])

    with tab1:
        st.markdown("""
#### Google Gemini

Free tier with generous limits. No credit card required.

**To get your API key:**
1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with Google
3. Click **Get API Key** → **Create in new project**
4. Copy the key (starts with "AIza...")
""")

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
#### Anthropic Claude

Strong reasoning capabilities. Requires prepaid credits.

**To get your API key:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account and add credits ($5–10 to start)
3. Create an API key in Settings → API Keys
""")

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
#### OpenAI GPT

General-purpose AI with broad capabilities. Requires prepaid credits.

**To get your API key:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an account and add credits
3. Create an API key in Settings → API Keys
""")

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
    Check if user has configured an API key or OAuth.
    Returns: (has_access, provider_name)
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return False, None

    llm_config = SettingsManager.get_llm_config(user_id)
    has_key = bool(llm_config.get("api_key"))
    has_oauth = llm_config.get("using_oauth", False)
    provider = llm_config.get("provider", "anthropic")

    return has_key or has_oauth, provider


def show_api_key_banner():
    """Show banner when API key is missing"""
    import os
    from gemini_oauth import GeminiOAuth

    user_id = st.session_state.get("user_id")
    oauth_available = bool(os.getenv("GOOGLE_OAUTH_CLIENT_ID"))

    if oauth_available:
        st.info("""
**Sign in to start chatting**

Connect your Google account to use AI chat for free.
""")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("Sign in with Google", key="google_signin_banner", type="primary", use_container_width=True):
                app_url = os.getenv("APP_URL", "http://localhost:8501")
                redirect_uri = f"{app_url}/oauth/callback"

                auth_url = GeminiOAuth.get_oauth_url(user_id, redirect_uri)
                if auth_url:
                    st.markdown(f"[Click here to sign in with Google]({auth_url})")

        st.caption("Or use your own API key")
        if st.button("Use API key instead", key="open_api_setup_alt"):
            show_api_key_setup_modal()
    else:
        st.warning("""
**AI provider required**

To use the chat assistant, connect an AI provider. We recommend Google Gemini—it's free and takes 30 seconds to set up.
""")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("Connect AI provider", key="open_api_setup", type="primary", use_container_width=True):
                show_api_key_setup_modal()


def render_api_status_indicator():
    """Show current API provider status"""
    has_access, provider = check_api_key_status()

    if has_access:
        provider_labels = {
            "google": "Gemini",
            "google_oauth": "Google",
            "anthropic": "Claude",
            "openai": "GPT"
        }
        provider_name = provider_labels.get(provider, "AI")
        st.caption(f"◆ {provider_name}")
    else:
        st.caption("○ No AI connected")
