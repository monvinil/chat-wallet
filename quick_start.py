"""
Chat02 Quick Start - Zero-friction onboarding
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
            # Set a temporary user ID for guest
            guest_user_id = f"guest_{wallet_info['address'][:8]}"

            # Encrypt wallet data immediately with a derived key from guest ID
            # This prevents plaintext private keys in session state
            from utils.encryption import PasswordEncryption
            encrypted = PasswordEncryption.encrypt(wallet_info["wallet_data"], guest_user_id)

            # Store encrypted data in session
            st.session_state.wallet_address = wallet_info["address"]
            st.session_state.wallet_encrypted = encrypted["encrypted_data"]
            st.session_state.wallet_salt = encrypted["salt"]
            st.session_state.wallet_key = encrypted["key"]
            st.session_state.wallet_locked = False
            st.session_state.guest_wallet_address = wallet_info["address"]
            st.session_state.guest_mode = True
            st.session_state.guest_mnemonic = wallet_info.get("mnemonic")  # Save for account creation
            st.session_state.user_id = guest_user_id
            st.session_state._guest_user_id = guest_user_id  # Preserve for conversion

            # Defer wallet key save to next render cycle (to let JS execute)
            st.session_state._pending_wallet_key_save = encrypted["key"]

            # Store Solana address if available (multi-chain wallet)
            if wallet_info.get("solana_address"):
                st.session_state.solana_address = wallet_info["solana_address"]
            else:
                # Log warning - Solana libraries may not be installed
                import logging
                logging.warning("No Solana address derived - check if solders, bip-utils, base58 are installed")

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
    """Show banner explaining guest mode - educational, warm"""
    if st.session_state.get("guest_mode") and not st.session_state.get("quick_start_banner_dismissed"):
        with st.container():
            st.info("""
**One quick step to start chatting**

You need a free AI key from Google:

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Get API Key** → **Create in new project**
3. Come back and paste it in Settings

Create an account anytime to access your wallet from other devices.
""")

            if st.button("Got it", key="dismiss_quick_start_banner"):
                st.session_state.quick_start_banner_dismissed = True


def show_save_account_prompt():
    """Show prompt to encourage saving the guest wallet - educational, non-pushy"""
    if st.session_state.get("guest_mode"):
        message_count = len(st.session_state.get("messages", []))

        # Show after several exchanges
        if message_count >= 6 and not st.session_state.get("save_prompt_dismissed"):
            with st.expander("Save your wallet", expanded=False):
                st.markdown("""
Create an account to keep this wallet safe and accessible everywhere.

**What you get:**
- Access from any device
- Secure cloud backup
- Never lose your funds

No pressure—guest mode works fine too.
""")

                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("Create Account", key="save_guest_wallet", type="primary", use_container_width=True):
                        st.session_state.show_save_account_modal = True

                with col2:
                    if st.button("Not now", key="dismiss_save_prompt", use_container_width=True):
                        st.session_state.save_prompt_dismissed = True


@st.dialog("Save Your Wallet", width="large")
def save_guest_wallet_modal():
    """Convert guest wallet to permanent account"""
    st.markdown("""
#### Create an account

Your wallet will be saved and accessible from any device.
""")

    email = st.text_input("Email", placeholder="your@email.com")
    password = st.text_input("Password", type="password", help="Minimum 8 characters")
    password_confirm = st.text_input("Confirm password", type="password")

    if st.button("Create Account", type="primary", use_container_width=True):
        if not email or not password:
            st.error("Please enter both email and password")
        elif password != password_confirm:
            st.error("Passwords don't match")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters")
        elif "@" not in email:
            st.error("Please enter a valid email")
        else:
            from supabase_client import create_user, save_wallet_address, get_user_by_email
            from session_manager import SessionManager

            with st.spinner("Creating account..."):
                # Check if user exists
                existing_user = get_user_by_email(email)
                if existing_user:
                    st.error("An account with this email already exists. Please sign in instead.")
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
                            # Get guest user ID BEFORE updating session (for API key migration)
                            guest_user_id = st.session_state.get("_guest_user_id")

                            # Decrypt guest wallet data to re-encrypt with user password
                            from utils.encryption import PasswordEncryption
                            wallet_data = None
                            if st.session_state.get("wallet_encrypted") and guest_user_id:
                                wallet_data = PasswordEncryption.decrypt(
                                    st.session_state.wallet_encrypted,
                                    guest_user_id,
                                    st.session_state.wallet_salt
                                )

                            if wallet_data:
                                # Re-encrypt with user's password
                                encrypted = WalletManager.encrypt_wallet_data(wallet_data, password)

                                # Save to cloud
                                save_wallet_address(
                                    user["id"],
                                    st.session_state.wallet_address,
                                    encrypted_wallet_data=encrypted["encrypted_data"],
                                    encryption_salt=encrypted["salt"]
                                )

                                # Copy API key to new user account BEFORE updating user_id
                                if guest_user_id:
                                    llm_config = SettingsManager.get_llm_config(guest_user_id)
                                    if llm_config.get("api_key") and not st.session_state.get("using_demo_key"):
                                        SettingsManager.update_llm_settings(
                                            user["id"],
                                            provider=llm_config.get("provider"),
                                            api_key=llm_config.get("api_key"),
                                            model=llm_config.get("model")
                                        )

                                # Update session with new user info
                                st.session_state.wallet_encrypted = encrypted["encrypted_data"]
                                st.session_state.wallet_salt = encrypted["salt"]
                                st.session_state.wallet_key = encrypted["key"]
                                st.session_state.user_id = user["id"]
                                st.session_state.user_email = email
                                st.session_state.guest_mode = False
                                st.session_state._guest_user_id = None  # Clear guest ID

                                # Create persistent session
                                SessionManager.login(user["id"], email, st.session_state.wallet_address)

                                st.success("Account created. Your wallet is now saved.")

                                # Show recovery phrase
                                if st.session_state.get("guest_mnemonic"):
                                    st.warning("**Save your recovery phrase**")
                                    st.code(st.session_state.guest_mnemonic, language=None)
                                    st.caption("Write this down. It's the only way to recover your wallet if you forget your password.")

                                st.caption("Close this dialog to continue.")
                                st.session_state.show_save_account_modal = False
                            else:
                                st.error("Could not find wallet data. Please try again.")
                        else:
                            st.error("Could not create account. Please try again.")
                    except Exception as e:
                        st.error(f"Something went wrong: {str(e)}")
