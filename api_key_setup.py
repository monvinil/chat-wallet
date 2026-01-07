"""
Improved API key setup experience
- Modal popup instead of sidebar
- Direct links to get keys
- Instant validation
- Clear pricing info
"""

import streamlit as st
from settings_manager import SettingsManager


def validate_anthropic_key(api_key: str) -> tuple[bool, str]:
    """
    Validate Anthropic API key by making a test request

    Returns: (is_valid, message)
    """
    if not api_key or not api_key.startswith("sk-ant-"):
        return False, "Invalid format. Anthropic keys start with 'sk-ant-'"

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        # Test with minimal request (costs ~$0.0001)
        client.messages.create(
            model="claude-3-5-haiku-20241022",  # Cheapest model for validation
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

        return True, "✅ Valid API key"

    except Exception as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg or "api key" in error_msg:
            return False, "❌ Invalid API key. Check your key and try again."
        elif "credit" in error_msg or "billing" in error_msg:
            return False, "⚠️ Valid key but no credits. Add credits at console.anthropic.com/settings/billing"
        else:
            return False, f"❌ Error: {str(e)[:100]}"


def validate_openai_key(api_key: str) -> tuple[bool, str]:
    """
    Validate OpenAI API key by making a test request

    Returns: (is_valid, message)
    """
    if not api_key or not api_key.startswith("sk-"):
        return False, "Invalid format. OpenAI keys start with 'sk-'"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Test with minimal request (costs ~$0.0001)
        client.chat.completions.create(
            model="gpt-4o-mini",  # Cheapest model for validation
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

        return True, "✅ Valid API key"

    except Exception as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg or "api key" in error_msg:
            return False, "❌ Invalid API key. Check your key and try again."
        elif "quota" in error_msg or "billing" in error_msg:
            return False, "⚠️ Valid key but no credits. Add credits at platform.openai.com/settings/organization/billing"
        else:
            return False, f"❌ Error: {str(e)[:100]}"


@st.dialog("Connect AI Provider", width="large")
def show_api_key_setup_modal():
    """
    Modal dialog for API key setup
    Better UX than sidebar - focused, clear, guided
    """

    st.markdown("""
### Why do I need this?

Chat Wallet uses **your own AI provider** (Anthropic or OpenAI) to power the assistant. This means:
- ✅ **You own your data** - we never see your conversations
- ✅ **Pay only for what you use** - typically $0.01-0.05 per conversation
- ✅ **No monthly subscriptions** - just API usage costs
- ✅ **Switch providers anytime**

**Important:** API keys are separate from claude.ai or ChatGPT subscriptions. You need to purchase API credits separately:
- Anthropic: Add credits at [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing) (start with $5-10)
- OpenAI: Add credits at [platform.openai.com/settings/organization/billing](https://platform.openai.com/settings/organization/billing)

---
""")

    # Provider selection tabs
    tab1, tab2, tab3 = st.tabs(["🆓 Google Gemini (FREE)", "🟣 Anthropic", "🟢 OpenAI"])

    with tab1:
        st.markdown("""
#### Google Gemini 2.0 Flash ⭐ FREE TIER

**Why choose Gemini:**
- ✅ **Completely FREE** - 60 requests/minute, 1500 requests/day
- ✅ **No credit card required** - Just need a Google account
- ✅ **Fast and capable** - Latest Gemini 2.0 Flash model
- ✅ **Perfect for getting started** - No billing setup needed

**Pricing:**
- FREE Tier: 60 RPM, 1500 RPD (enough for ~100+ conversations/day)
- Paid Tier: Only if you need higher limits ($0.10 per 1M tokens)

**Get your FREE API key:**
1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Get API Key" → Create in new project
4. Copy your key (starts with "AIza...")
5. That's it! No credit card needed.
""")

        gemini_key = st.text_input(
            "Google API Key",
            type="password",
            placeholder="AIza...",
            key="gemini_key_input",
            help="Starts with AIza - Get it FREE at aistudio.google.com/apikey"
        )

        if st.button("🔗 Get FREE API Key", key="get_gemini_key", type="primary", use_container_width=True):
            st.link_button(
                "Open Google AI Studio →",
                "https://aistudio.google.com/apikey",
                use_container_width=True
            )

        if st.button("✅ Save & Start Chatting", key="save_gemini", type="primary", use_container_width=True):
            if gemini_key:
                # Save to settings without validation (free tier, no validation needed)
                user_id = st.session_state.get("user_id")
                SettingsManager.update_llm_settings(
                    user_id,
                    provider="google",
                    api_key=gemini_key,
                    model="gemini-2.0-flash-exp"
                )

                # Set success flag for persistent message
                st.session_state.api_key_configured = True
                st.session_state._api_key_just_saved = True

                st.success("✅ API key saved! You're ready to chat for FREE.")
                st.info("Click outside this dialog or press ESC to continue.")
            else:
                st.warning("Please enter an API key")

    with tab2:
        st.markdown("""
#### Anthropic Claude

**Why choose Anthropic:**
- High quality reasoning and analysis
- Best for financial tasks and structured data
- Lower latency for chat

**Pricing:**
- Haiku: $0.25 per 1M input tokens (~$0.01 per conversation)
- Sonnet: $3 per 1M input tokens (~$0.03 per conversation)
- Requires purchasing API credits

**Get your API key:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create account (free)
3. Add $5-10 credits in [Billing](https://console.anthropic.com/settings/billing)
4. Create API key in [API Keys](https://console.anthropic.com/settings/keys)
""")

        anthropic_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-api03-...",
            key="anthropic_key_input",
            help="Starts with sk-ant-"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔗 Get API Key", key="get_anthropic_key", type="secondary"):
                st.link_button(
                    "Open Anthropic Console →",
                    "https://console.anthropic.com/settings/keys",
                    use_container_width=True
                )

        with col2:
            if st.button("💾 Save Without Validation", key="save_anthropic_skip", use_container_width=True):
                if anthropic_key:
                    # Save to settings without validation
                    user_id = st.session_state.get("user_id")
                    SettingsManager.update_llm_settings(
                        user_id,
                        provider="anthropic",
                        api_key=anthropic_key,
                        model="claude-sonnet-4-20250514"
                    )

                    st.session_state.api_key_configured = True
                    st.session_state._api_key_just_saved = True

                    st.success("✅ API key saved! Try chatting to test it.")
                    st.info("Click outside this dialog or press ESC to continue.")
                else:
                    st.warning("Please enter an API key")

        if st.button("✅ Validate & Save", key="save_anthropic", type="primary", use_container_width=True):
            if anthropic_key:
                with st.spinner("Validating API key..."):
                    is_valid, message = validate_anthropic_key(anthropic_key)

                    if is_valid:
                        user_id = st.session_state.get("user_id")
                        SettingsManager.update_llm_settings(
                            user_id,
                            provider="anthropic",
                            api_key=anthropic_key,
                            model="claude-sonnet-4-20250514"
                        )

                        st.session_state.api_key_configured = True
                        st.session_state._api_key_just_saved = True

                        st.success("✅ API key saved! You're ready to chat.")
                        st.info("Click outside this dialog or press ESC to continue.")
                    elif "credit" in message.lower():
                        st.warning(message)
                        st.info("💡 **Tip:** You can still save the key and it may work if you have an active subscription.")

                        user_id = st.session_state.get("user_id")
                        SettingsManager.update_llm_settings(
                            user_id,
                            provider="anthropic",
                            api_key=anthropic_key,
                            model="claude-sonnet-4-20250514"
                        )

                        st.session_state.api_key_configured = True
                        st.session_state._api_key_just_saved = True

                        st.success("✅ API key saved! Try chatting to test it.")
                    else:
                        st.error(message)
            else:
                st.warning("Please enter an API key")

    with tab3:
        st.markdown("""
#### OpenAI GPT

**Why choose OpenAI:**
- More general-purpose capabilities
- Wider ecosystem support
- Good for diverse tasks

**Pricing:**
- GPT-4o Mini: $0.15 per 1M input tokens (~$0.015 per conversation)
- GPT-4o: $2.50 per 1M input tokens (~$0.05 per conversation)

**Get your API key:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account
3. Add credits in [Billing](https://platform.openai.com/settings/organization/billing)
4. Create API key in [API Keys](https://platform.openai.com/api-keys)
""")

        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-proj-...",
            key="openai_key_input",
            help="Starts with sk-proj- or sk-"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("📋 Copy Example", key="copy_openai_example"):
                st.code("sk-proj-...")

        with col2:
            if st.button("🔗 Get API Key", key="get_openai_key", type="secondary"):
                st.link_button(
                    "Open OpenAI Platform →",
                    "https://platform.openai.com/api-keys",
                    use_container_width=True
                )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("💾 Save Without Validation", key="save_openai_skip", use_container_width=True):
                if openai_key:
                    # Save to settings without validation
                    user_id = st.session_state.get("user_id")
                    SettingsManager.update_llm_settings(
                        user_id,
                        provider="openai",
                        api_key=openai_key,
                        model="gpt-4o"
                    )

                    # Set success flag for persistent message
                    st.session_state.api_key_configured = True
                    st.session_state._api_key_just_saved = True

                    st.success("✅ API key saved! Try chatting to test it.")
                    st.info("Click outside this dialog or press ESC to continue.")
                else:
                    st.warning("Please enter an API key")

        with col2:
            if st.button("✅ Validate & Save", key="save_openai", type="primary", use_container_width=True):
                if openai_key:
                    with st.spinner("Validating API key..."):
                        is_valid, message = validate_openai_key(openai_key)

                        if is_valid:
                            # Save to settings
                            user_id = st.session_state.get("user_id")
                            SettingsManager.update_llm_settings(
                                user_id,
                                provider="openai",
                                api_key=openai_key,
                                model="gpt-4o"
                            )

                            # Set success flag for persistent message
                            st.session_state.api_key_configured = True
                            st.session_state._api_key_just_saved = True

                            st.success("✅ API key saved! You're ready to chat.")
                            st.info("Click outside this dialog or press ESC to continue.")
                        elif "quota" in message.lower() or "billing" in message.lower():
                            # Billing issue - save anyway with warning
                            st.warning(message)
                            st.info("💡 **Tip:** You can still save the key and it may work if you have an active subscription.")

                            # Save to settings
                            user_id = st.session_state.get("user_id")
                            SettingsManager.update_llm_settings(
                                user_id,
                                provider="openai",
                                api_key=openai_key,
                                model="gpt-4o"
                            )

                            # Set success flag
                            st.session_state.api_key_configured = True
                            st.session_state._api_key_just_saved = True

                            st.success("✅ API key saved! Try chatting to test it.")
                        else:
                            st.error(message)
                else:
                    st.warning("Please enter an API key")

    # Skip option (for testing)
    st.markdown("---")
    if st.button("⏭️ Skip for now", key="skip_api_setup", use_container_width=True):
        st.session_state.api_key_skipped = True
        st.rerun()


def check_api_key_status() -> tuple[bool, str]:
    """
    Check if user has configured API key

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
    """
    Show prominent banner when API key is missing
    Better than error in chat
    """
    st.warning("""
### 🔑 AI Provider Required

To use the chat assistant, connect your Anthropic or OpenAI account.

**Why?** You own your API key = you own your data + pay only for usage (~$0.01-0.05 per conversation)
""", icon="🤖")

    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        if st.button("🔗 Connect AI Provider", key="open_api_setup", type="primary", use_container_width=True):
            show_api_key_setup_modal()


def render_api_status_indicator():
    """
    Show current API provider status in UI
    Small indicator, not intrusive
    """
    has_key, provider = check_api_key_status()

    if has_key:
        # Show small status indicator
        if provider == "google":
            provider_name = "Google Gemini"
            emoji = "🆓"
        elif provider == "anthropic":
            provider_name = "Anthropic"
            emoji = "🟣"
        else:
            provider_name = "OpenAI"
            emoji = "🟢"

        st.caption(f"{emoji} Connected: {provider_name}")
    else:
        st.caption("⚪ No AI provider connected")
