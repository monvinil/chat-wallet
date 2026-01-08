"""
Quick Start Flow - Zero-friction onboarding
Users can start chatting immediately without any signup
"""

import streamlit as st
from wallet_manager import WalletManager
from settings_manager import SettingsManager


def create_guest_wallet():
    """
    Create a temporary guest wallet for immediate use
    User can optionally save it later by creating an account
    """
    # Check if guest wallet already exists
    if st.session_state.get("guest_wallet_address"):
        return True

    try:
        # Create wallet
        wallet_info = WalletManager.create_new_wallet()

        if wallet_info:
            # Store in session only (not cloud - this is a guest wallet)
            st.session_state.wallet_address = wallet_info["address"]
            st.session_state.wallet_data = wallet_info["wallet_data"]
            st.session_state.wallet_locked = False
            st.session_state.guest_wallet_address = wallet_info["address"]
            st.session_state.guest_mode = True
            st.session_state.guest_mnemonic = wallet_info.get("mnemonic")  # Save for later if they want to create account

            # Set a temporary user ID for guest
            st.session_state.user_id = f"guest_{wallet_info['address'][:8]}"

            return True
    except Exception as e:
        print(f"Error creating guest wallet: {e}")
        return False

    return False


def setup_demo_gemini_key():
    """
    Configure a demo Gemini key to get user started immediately
    They can replace it with their own FREE key anytime

    NOTE: This uses a shared demo key with rate limits.
    Users should get their own FREE key for best experience.
    """
    # Check if user already has an API key
    user_id = st.session_state.get("user_id")
    if user_id:
        llm_config = SettingsManager.get_llm_config(user_id)
        if llm_config.get("api_key"):
            return True  # Already configured

    # Use demo key for quick start
    # NOTE: In production, this would be a shared demo key with rate limits
    # For now, users need to get their own FREE key
    demo_key_available = False  # Set to True if you have a demo key to share

    if demo_key_available and user_id:
        SettingsManager.update_llm_settings(
            user_id,
            provider="google",
            api_key="DEMO_KEY_HERE",  # Replace with actual demo key
            model="gemini-2.0-flash-exp"
        )
        st.session_state.using_demo_key = True
        return True

    return False


def show_quick_start_banner():
    """
    Show friendly banner explaining guest mode and how to get their own FREE key
    """
    if st.session_state.get("guest_mode") and not st.session_state.get("quick_start_banner_dismissed"):
        with st.container():
            st.info("""
**🚀 Quick Start Mode**

You're using a temporary wallet. Get your **FREE** Google Gemini API key to start chatting:

1. Visit [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (takes 30 seconds)
2. Click "Get API Key" → Create in new project
3. Come back and click "Connect AI" in the sidebar

💡 **Want to save your wallet?** Create an account later to sync across devices.
""")

            if st.button("Got it! I'll get my FREE key now", key="dismiss_quick_start_banner"):
                st.session_state.quick_start_banner_dismissed = True


def show_save_account_prompt():
    """
    Show occasional prompts to encourage saving the guest wallet to an account
    """
    if st.session_state.get("guest_mode"):
        # Show after certain actions (e.g., after 3 messages or first transaction)
        message_count = len(st.session_state.get("messages", []))

        if message_count == 6:  # After 3 back-and-forth messages
            with st.expander("💾 **Save Your Wallet** (Optional)", expanded=False):
                st.markdown("""
Want to access this wallet from other devices?

**Create a free account** to:
- ✅ Sync wallet across all your devices
- ✅ Never lose access to your funds
- ✅ Backup your recovery phrase securely

Otherwise, you can keep using guest mode - your wallet works fine without an account!
""")

                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("Create Account", key="save_guest_wallet", type="primary", use_container_width=True):
                        st.session_state.show_save_account_modal = True

                with col2:
                    if st.button("Maybe Later", key="dismiss_save_prompt", use_container_width=True):
                        st.session_state.save_prompt_dismissed = True


@st.dialog("Save Your Wallet", width="large")
def save_guest_wallet_modal():
    """
    Convert guest wallet to permanent account
    """
    st.markdown("""
### Create Account to Save Your Wallet

Your current wallet will be permanently saved and accessible from any device.
""")

    email = st.text_input("Email", placeholder="your@email.com")
    password = st.text_input("Password (min 8 characters)", type="password")
    password_confirm = st.text_input("Confirm Password", type="password")

    if st.button("Create Account & Save Wallet", type="primary", use_container_width=True):
        if not email or not password:
            st.error("Please enter both email and password")
        elif password != password_confirm:
            st.error("Passwords do not match")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters")
        elif "@" not in email:
            st.error("Please enter a valid email address")
        else:
            from supabase_client import create_user, save_wallet_address, get_user_by_email
            from session_manager import SessionManager

            with st.spinner("Saving your wallet..."):
                # Check if user exists
                existing_user = get_user_by_email(email)
                if existing_user:
                    st.error("Account already exists. Please log in instead.")
                else:
                    # Hash password
                    password_hash = WalletManager.hash_password(password)

                    # Create user
                    try:
                        user = create_user(
                            email=email,
                            primary_wallet_address=st.session_state.wallet_address,
                            password_hash=password_hash
                        )

                        if user:
                            # Encrypt wallet data
                            wallet_data = st.session_state.get("wallet_data")
                            if wallet_data:
                                encrypted = WalletManager.encrypt_wallet_data(wallet_data, password)

                                # Save to cloud
                                save_wallet_address(
                                    user["id"],
                                    st.session_state.wallet_address,
                                    encrypted_wallet_data=encrypted["encrypted_data"],
                                    encryption_salt=encrypted["salt"]
                                )

                                # Update session
                                st.session_state.wallet_encrypted = encrypted["encrypted_data"]
                                st.session_state.wallet_salt = encrypted["salt"]
                                st.session_state.wallet_key = encrypted["key"]
                                st.session_state.user_id = user["id"]
                                st.session_state.user_email = email
                                st.session_state.guest_mode = False

                                # Create persistent session
                                SessionManager.login(user["id"], email, st.session_state.wallet_address)

                                # Copy API key to new user account if configured
                                guest_user_id = st.session_state.get("user_id")
                                llm_config = SettingsManager.get_llm_config(guest_user_id)
                                if llm_config.get("api_key") and not st.session_state.get("using_demo_key"):
                                    SettingsManager.update_llm_settings(
                                        user["id"],
                                        provider=llm_config.get("provider"),
                                        api_key=llm_config.get("api_key"),
                                        model=llm_config.get("model")
                                    )

                                st.success("✅ Account created! Your wallet is now saved permanently.")

                                # Show recovery phrase
                                if st.session_state.get("guest_mnemonic"):
                                    st.warning("⚠️ **Save your recovery phrase:**")
                                    st.code(st.session_state.guest_mnemonic, language=None)
                                    st.caption("Write this down - it's the only way to recover your wallet if you forget your password.")

                                st.info("Close this dialog to continue chatting.")
                                st.session_state.show_save_account_modal = False
                            else:
                                st.error("Wallet data not found in session")
                        else:
                            st.error("Failed to create account")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
