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
    # Check if quick start mode - skip to AI setup
    if st.session_state.get("quick_start_active"):
        st.session_state.onboarding_step = 2
        st.rerun()
        return

    st.markdown("""
## Setup Complete: Wallet Created

**Your wallet is ready:**
✅ Secure address generated (only you control the private keys)
✅ Multi-chain support enabled (Base, Arbitrum, Polygon, Solana)
✅ Encrypted and backed up to cloud

**Next: Get your FREE AI key (takes 30 seconds)**

Chat Wallet needs a Google Gemini API key to power the chat assistant:
- ✅ Completely **FREE** (no credit card needed)
- ✅ Just sign in with Google
- ✅ 1500 requests/day included free

Or use Anthropic/OpenAI if you prefer (requires purchasing credits).
""")

    if st.button("Get FREE Gemini Key →", type="primary", use_container_width=True):
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
        # Update provider display
        if provider == "google":
            provider_name = "Google Gemini"
            emoji = "🆓"
        elif provider == "anthropic":
            provider_name = "Anthropic"
            emoji = "🟣"
        else:
            provider_name = "OpenAI"
            emoji = "🟢"

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
    st.info("""
### 🆓 Final Step: Get Your FREE AI Key (30 seconds)

**Recommended: Google Gemini (Completely FREE)**
- No credit card required
- 1500 requests/day included free
- Just sign in with Google
- Get key at: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

**Or choose:** Anthropic Claude or OpenAI GPT (requires purchasing API credits)
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
