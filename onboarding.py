"""
Onboarding flow for new users - step-by-step setup wizard
"""

import streamlit as st
from settings_manager import SettingsManager


def show_onboarding():
    """
    Multi-step onboarding wizard that users must complete before using chat.
    Returns True if onboarding is complete, False if still in progress.
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return False

    # Check onboarding status
    llm_config = SettingsManager.get_llm_config(user_id)
    has_api_key = bool(llm_config.get("api_key"))

    # Skip onboarding if already complete
    if has_api_key:
        return True

    # Initialize onboarding step
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1

    # Header
    st.markdown("### Setup Your Wallet")

    # Progress indicator
    total_steps = 2
    current_step = st.session_state.onboarding_step
    progress = current_step / total_steps
    st.progress(progress, text=f"Step {current_step} of {total_steps}")

    st.divider()

    # Step 1: Welcome & Wallet Created
    if st.session_state.onboarding_step == 1:
        show_step_1_welcome()

    # Step 2: Connect AI
    elif st.session_state.onboarding_step == 2:
        return show_step_2_connect_ai(user_id)

    return False


def show_step_1_welcome():
    """Step 1: Welcome and explain what just happened"""
    st.markdown("""
## Setup Complete: Wallet Created

**Your wallet is ready:**
✅ Secure address generated (only you control the private keys)
✅ Multi-chain support enabled (Base, Arbitrum, Polygon, Solana)
✅ Encrypted and backed up to cloud

**Next: Connect your AI provider**

Chat Wallet uses your own Anthropic or OpenAI API key to power the assistant. This means:
- You own your conversations (we never see them)
- You pay only for what you use (~$0.01-0.05 per conversation)
- You can switch providers anytime

Think of it as: **Your wallet** (✅ created) + **Your AI** (→ next step) = Chat Wallet
""")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Continue →", type="primary", use_container_width=True):
            st.session_state.onboarding_step = 2
            st.rerun()


def show_step_2_connect_ai(user_id: str):
    """Step 2: Connect AI provider - returns True if complete"""
    st.markdown("""
## Connect AI Provider

Select which AI model will handle your chat commands:
""")

    # Get existing settings
    existing_settings = SettingsManager.get_user_settings(user_id)

    # Provider selection
    col1, col2 = st.columns(2)

    with col1:
        anthropic_selected = st.button(
            "🧠 Anthropic (Claude)",
            use_container_width=True,
            type="primary" if not existing_settings or existing_settings.get("llm_provider") == "anthropic" else "secondary"
        )

    with col2:
        openai_selected = st.button(
            "🤖 OpenAI (GPT-4)",
            use_container_width=True,
            type="primary" if existing_settings and existing_settings.get("llm_provider") == "openai" else "secondary"
        )

    # Determine provider
    if anthropic_selected:
        provider = "anthropic"
        st.session_state.onboarding_provider = provider
    elif openai_selected:
        provider = "openai"
        st.session_state.onboarding_provider = provider
    else:
        provider = st.session_state.get("onboarding_provider", "anthropic")

    st.divider()

    # Show selected provider details
    if provider == "anthropic":
        st.markdown("""
**Anthropic (Claude)** - Recommended

**Why Claude:**
- Excellent at understanding financial instructions
- Strong reasoning for complex transactions
- ~$0.01-0.05 per conversation

**Get your API key:**
1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Sign up (free tier available)
3. Go to API Keys section
4. Create new key
5. Paste below
""")
        model_options = {
            "claude-sonnet-4-20250514": "Sonnet - Balanced (recommended)",
            "claude-opus-4-20250514": "Opus - Most capable",
            "claude-haiku-4-20250514": "Haiku - Fastest & cheapest"
        }
        default_model = "claude-sonnet-4-20250514"

    else:  # OpenAI
        st.markdown("""
**OpenAI (GPT-4)** - Alternative option

**Why GPT-4:**
- Reliable performance for financial tasks
- Well-tested API
- ~$0.02-0.08 per conversation

**Get your API key:**
1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Go to API Keys section
4. Create new secret key
5. Paste below
""")
        model_options = {
            "gpt-4": "GPT-4 - Most capable",
            "gpt-4-turbo": "GPT-4 Turbo - Faster",
            "gpt-3.5-turbo": "GPT-3.5 - Cheapest"
        }
        default_model = "gpt-4"

    # Model selection
    st.markdown("**Choose model:**")
    selected_model = st.selectbox(
        "Model",
        list(model_options.keys()),
        format_func=lambda x: model_options[x],
        index=list(model_options.keys()).index(default_model),
        label_visibility="collapsed"
    )

    # API Key input
    st.markdown("**Paste your API key:**")
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder=f"sk-ant-..." if provider == "anthropic" else "sk-...",
        label_visibility="collapsed",
        key="onboarding_api_key"
    )

    st.caption("🔒 Your API key is encrypted before storage. Change it anytime in Settings.")

    # Save button
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Back"):
            st.session_state.onboarding_step = 1
            st.rerun()

    with col3:
        save_disabled = not api_key or len(api_key) < 10
        if st.button(
            "Complete Setup ✓",
            type="primary",
            disabled=save_disabled,
            use_container_width=True
        ):
            # Save settings
            success = SettingsManager.save_user_settings(
                user_id=user_id,
                llm_provider=provider,
                llm_model=selected_model,
                llm_api_key=api_key
            )

            if success:
                st.success("✅ Setup complete. Opening chat...")
                st.session_state.onboarding_step = None  # Clear onboarding
                st.session_state.onboarding_provider = None
                st.balloons()
                st.rerun()
            else:
                st.error("Failed to save settings. Please try again.")

        if save_disabled and api_key:
            st.caption("⚠️ API key seems too short")

    return False  # Still in onboarding
