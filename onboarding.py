"""
Simplified onboarding flow - uses modal for API key setup
"""

import streamlit as st
from settings_manager import SettingsManager


def show_onboarding():
    """
    Multi-step onboarding wizard.
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
    """Step 2: Connect AI provider via modal dialog"""
    from api_key_setup import show_api_key_setup_modal, check_api_key_status

    st.markdown("""
## Connect AI Provider

Your chat assistant needs an AI provider to understand commands and execute transactions.
""")

    # Check if already configured (modal was just completed)
    has_key, provider = check_api_key_status()

    if has_key:
        provider_name = "Anthropic" if provider == "anthropic" else "OpenAI"
        emoji = "🟣" if provider == "anthropic" else "🟢"

        # Show persistent success state
        st.success(f"{emoji} **Connected:** {provider_name}")

        # Only show balloons once (not on every rerun)
        if not st.session_state.get("_api_setup_celebration_shown"):
            st.balloons()
            st.session_state._api_setup_celebration_shown = True

        st.info("""
✅ **Setup Complete!**

Your AI provider is connected and ready. You can now:
- Check balances across networks
- Send USDC transactions
- Buy gift cards with crypto
- Automate payments
        """)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Change Provider", use_container_width=True):
                # Clear celebration flag so balloons show again after change
                st.session_state._api_setup_celebration_shown = False
                show_api_key_setup_modal()
        with col2:
            if st.button("Continue to Chat →", type="primary", use_container_width=True):
                st.session_state.onboarding_complete = True
                # Show success animation only if just signed up
                if st.session_state.get("just_signed_up"):
                    st.session_state.just_signed_up = False  # Clear flag
                    # Import and show animation
                    import time
                    from app import show_success_animation
                    show_success_animation()
                    time.sleep(2)
                st.rerun()

        return True  # Onboarding complete

    # Show connection prompt with big CTA
    st.warning("""
### 🔑 One More Step: Connect Your AI

Chat Wallet uses **your own AI provider** (Anthropic or OpenAI) to power the assistant.

**Why?**
- ✅ You own your data (we never see conversations)
- ✅ Pay only for usage (~$0.01-0.05 per conversation)
- ✅ No monthly subscriptions

**Takes 2 minutes:** Get API key → Paste → Done
""")

    # Auto-show modal on first visit to this step
    if not st.session_state.get("_api_setup_modal_shown_once"):
        st.session_state._api_setup_modal_shown_once = True
        show_api_key_setup_modal()

    # Big prominent button
    if st.button("🔗 Connect AI Provider", type="primary", use_container_width=True, key="connect_ai_main"):
        show_api_key_setup_modal()

    # Skip button for testing
    st.markdown("---")
    if st.button("⏭️ Skip for now (testing only)", use_container_width=True):
        st.session_state.onboarding_complete = True
        st.rerun()

    return False  # Still in onboarding
