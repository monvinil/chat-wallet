"""
Settings UI - User settings, LLM configuration, and account connections
"""

import streamlit as st
from settings_manager import SettingsManager
from typing import Optional


def settings_page():
    """Render settings page"""
    st.title("Settings")

    # Check if user is logged in
    if not st.session_state.get("wallet_address"):
        st.warning("Please log in to access settings")
        return

    # Get user ID (UUID from database, NOT wallet address)
    user_id = st.session_state.get("user_id")

    # Fallback: if user_id not in session, try to get from database
    if not user_id:
        from supabase_client import get_user_by_email
        user_email = st.session_state.get("user_email")
        if user_email:
            user = get_user_by_email(user_email)
            if user:
                user_id = user["id"]
                st.session_state.user_id = user_id

    if not user_id:
        st.warning("Please log in again to access settings")
        return

    # Load existing settings
    existing_settings = SettingsManager.get_user_settings(user_id)

    # Get the tab to show based on quick action
    settings_tab = st.session_state.get("settings_tab", None)

    # Tabs for different settings sections
    tab_names = ["AI Provider", "Display", "Connected Accounts", "Limits", "Security"]
    tab1, tab_display, tab2, tab3, tab4 = st.tabs(tab_names)

    # Auto-select tab if coming from quick action
    if settings_tab == "provider":
        st.session_state.settings_tab = None  # Reset

    # ============================================================================
    # TAB 1: AI Model Configuration
    # ============================================================================
    with tab1:
        st.subheader("Connect Your AI")
        st.caption("Choose which AI powers your assistant")

        # Current model display with friendly messaging
        llm_config = SettingsManager.get_llm_config(user_id)

        if llm_config["using_default"]:
            st.warning("No AI connected yet. Add your API key below to start.")
        else:
            st.success(f"Connected: {llm_config['provider'].title()} - {llm_config['model']}")

        st.divider()

        # LLM Provider selection with friendly descriptions
        st.markdown("**Which AI do you want to use?**")
        provider_options = ["google", "anthropic", "openai"]
        provider_labels = {
            "google": "Google Gemini - Free tier available (Recommended)",
            "anthropic": "Anthropic Claude - Conversational & helpful",
            "openai": "OpenAI GPT - You might already have this"
        }
        existing_provider = existing_settings.get("llm_provider", "google") if existing_settings else "google"
        if existing_provider not in provider_options:
            existing_provider = "google"
        provider = st.selectbox(
            "AI Provider",
            provider_options,
            format_func=lambda x: provider_labels[x],
            index=provider_options.index(existing_provider),
            label_visibility="collapsed"
        )

        # Model selection based on provider
        st.markdown("**Which version?**")
        if provider == "google":
            model_options = {
                "gemini-2.0-flash": "Gemini 2.0 Flash - Fast & free (Recommended)",
                "gemini-1.5-pro": "Gemini 1.5 Pro - More capable",
                "gemini-1.5-flash": "Gemini 1.5 Flash - Balanced"
            }
        elif provider == "anthropic":
            model_options = {
                "claude-sonnet-4-20250514": "Sonnet - Balanced (Recommended)",
                "claude-opus-4-20250514": "Opus - Most capable",
                "claude-haiku-4-20250514": "Haiku - Fastest"
            }
        else:
            model_options = {
                "gpt-4-turbo": "GPT-4 Turbo - Fast and capable",
                "gpt-4": "GPT-4 - Most capable",
                "gpt-3.5-turbo": "GPT-3.5 - Fast and cheap"
            }

        default_model = existing_settings.get("llm_model") if existing_settings else list(model_options.keys())[0]
        selected_model = st.selectbox(
            "AI Model",
            list(model_options.keys()),
            format_func=lambda x: model_options[x],
            index=list(model_options.keys()).index(default_model) if default_model in model_options else 1,
            label_visibility="collapsed"
        )

        st.divider()

        # API Key input - always shown, required for production
        st.markdown("**Your API Key**")
        st.caption("Required to use the AI assistant")

        # Show if key is already configured
        has_existing_key = bool(existing_settings and existing_settings.get("llm_api_key_encrypted"))
        if has_existing_key:
            st.success("Key saved securely")
            st.caption("Paste a new key below to change it")

        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder=f"sk-ant-..." if provider == "anthropic" else "sk-...",
            label_visibility="collapsed",
            help="Paste your API key here - it will be encrypted"
        )

        # Helpful links and guidance
        if not has_existing_key:
            st.markdown(f"""
**Don't have an API key yet?**
1. Go to [{provider.capitalize()} {'Console' if provider == 'anthropic' else 'Platform'}]({'https://console.anthropic.com' if provider == 'anthropic' else 'https://platform.openai.com'})
2. Sign up (it's free to start)
3. Create an API key
4. Copy and paste it above

*New users typically get free credits to try it out!*
""")
        else:
            st.caption(f"Need a new key? Get it at [{'console.anthropic.com' if provider == 'anthropic' else 'platform.openai.com'}]({'https://console.anthropic.com' if provider == 'anthropic' else 'https://platform.openai.com'})")

        if not has_existing_key and not api_key:
            st.info("💡 Your key is encrypted and never shared. You only pay for the messages you send (usually pennies).", icon="🔒")

        # Save button
        if st.button("Save", type="primary", key="save_ai"):
            success = SettingsManager.save_user_settings(
                user_id=user_id,
                llm_provider=provider,
                llm_model=selected_model,
                llm_api_key=api_key
            )

            if success:
                st.success("Configuration saved")
                st.session_state.settings_updated = True
                st.rerun()
            else:
                st.error("Failed to save")

    # ============================================================================
    # TAB: Display Settings
    # ============================================================================
    with tab_display:
        st.subheader("Display")
        st.caption("Customize how Chat02 looks")

        # Theme selection (light/dark)
        current_theme = existing_settings.get("theme", "dark") if existing_settings else "dark"
        theme = st.radio(
            "Theme",
            ["dark", "light"],
            format_func=lambda x: "Dark" if x == "dark" else "Light",
            index=0 if current_theme == "dark" else 1,
            horizontal=True
        )

        st.caption("Dark mode is easier on the eyes, especially at night.")

        st.divider()

        # Save display settings
        if st.button("Save", type="primary", key="save_display"):
            success = SettingsManager.save_user_settings(
                user_id=user_id,
                theme=theme
            )

            if success:
                st.success("Display settings saved")
                st.session_state.user_theme = theme
                st.rerun()
            else:
                st.error("Oops, couldn't save. Try again?")

    # ============================================================================
    # TAB 2: Connected Accounts
    # ============================================================================
    with tab2:
        st.subheader("Connected Accounts")

        # List connected accounts
        connected = SettingsManager.list_connected_accounts(user_id)

        if connected:
            for conn in connected:
                col1, col2 = st.columns([3, 1])
                with col1:
                    status = "Connected" if conn['is_active'] else "Disconnected"
                    account = conn.get('provider_user_id', '')
                    st.markdown(f"**{conn['provider'].title()}** {f'({account})' if account else ''}")
                    st.caption(status)
                with col2:
                    if conn['is_active']:
                        if st.button("Disconnect", key=f"disconnect_{conn['provider']}", use_container_width=True):
                            if SettingsManager.disconnect_account(user_id, conn['provider']):
                                st.rerun()
            st.divider()

        # Email connection
        st.markdown("**Email**")
        st.caption("Connect email for AI automation and verification codes")

        from email_manager import show_email_connection_ui
        show_email_connection_ui(user_id)

        st.divider()

        # Other providers
        st.markdown("**Coming Soon**")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Amazon", use_container_width=True, disabled=True)
        with col2:
            st.button("Twitter", use_container_width=True, disabled=True)

    # ============================================================================
    # TAB 3: Spending & Approvals
    # ============================================================================
    with tab3:
        st.subheader("Spending Limits")

        col1, col2 = st.columns(2)

        with col1:
            daily_limit = st.number_input(
                "Daily Limit (USDC)",
                min_value=1.0,
                max_value=10000.0,
                value=float(existing_settings.get("daily_spend_limit", 100.0)) if existing_settings else 100.0,
                step=10.0
            )
            st.caption("Max AI can spend per day")

        with col2:
            approval_threshold = st.number_input(
                "Approval Threshold (USDC)",
                min_value=0.0,
                max_value=1000.0,
                value=float(existing_settings.get("require_approval_above", 50.0)) if existing_settings else 50.0,
                step=5.0
            )
            st.caption("Require approval above this amount")

        st.divider()

        st.markdown("**Permissions**")

        allow_recurring = st.checkbox(
            "Allow recurring payments",
            value=existing_settings.get("allow_recurring_payments", False) if existing_settings else False
        )

        allow_access = st.checkbox(
            "Allow account access",
            value=existing_settings.get("allow_account_access", False) if existing_settings else False
        )

        st.divider()

        if st.button("Save", type="primary", key="save_limits"):
            success = SettingsManager.save_user_settings(
                user_id=user_id,
                daily_spend_limit=daily_limit,
                require_approval_above=approval_threshold,
                allow_recurring_payments=allow_recurring,
                allow_account_access=allow_access
            )

            if success:
                st.success("Preferences saved")
                st.rerun()
            else:
                st.error("Failed to save")

    # ============================================================================
    # TAB 4: Security
    # ============================================================================
    with tab4:
        st.subheader("Security")

        # Export wallet section
        st.markdown("**Export Wallet**")

        if st.button("Show Private Key", type="secondary", key="show_pk"):
            st.session_state.show_private_key = True

        if st.session_state.get("show_private_key"):
            from wallet_manager import WalletManager
            wallet_data = WalletManager.get_wallet_from_session()

            if wallet_data and wallet_data.get("private_key"):
                st.warning("Never share your private key with anyone")

                if wallet_data.get("mnemonic"):
                    st.markdown("**Seed Phrase**")
                    st.code(wallet_data["mnemonic"], language=None)

                st.markdown("**Private Key**")
                st.code(wallet_data["private_key"], language=None)

                if st.button("Hide", key="hide_pk"):
                    st.session_state.show_private_key = False
                    st.rerun()
            else:
                st.error("Cannot retrieve private key")
                if st.button("Hide", key="hide_pk_err"):
                    st.session_state.show_private_key = False
                    st.rerun()

        st.divider()

        # Data info
        st.markdown("**Data Storage**")
        st.caption("""
        Wallet keys: Encrypted in session
        API keys: AES-256 encrypted
        OAuth tokens: AES-256 encrypted
        """)

        st.divider()

        # Danger zone - these actions are available
        st.markdown("**Danger Zone**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Settings", type="secondary", use_container_width=True):
                # Actually clear the settings
                user_id = st.session_state.get("user_id")
                if user_id:
                    try:
                        SettingsManager.clear_all_settings(user_id)
                        st.success("Settings cleared")
                        st.rerun()
                    except Exception as e:
                        st.error("Could not clear settings")
                else:
                    st.warning("No active session")
        with col2:
            if st.button("Disconnect Accounts", type="secondary", use_container_width=True):
                # Disconnect OAuth accounts
                user_id = st.session_state.get("user_id")
                if user_id:
                    try:
                        SettingsManager.disconnect_all_oauth(user_id)
                        st.success("Accounts disconnected")
                        st.rerun()
                    except Exception as e:
                        st.error("Could not disconnect accounts")
                else:
                    st.warning("No active session")


def show_settings_button():
    """Show settings button in sidebar"""
    if st.session_state.get("wallet_address"):
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.show_settings = True
