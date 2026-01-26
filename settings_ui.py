"""
Settings UI - User settings, LLM configuration, and account connections
V10 "Brutalist Fintech" - Revolut x Gentle Monster
"""

import streamlit as st
from settings_manager import SettingsManager
from typing import Optional


def settings_page():
    """Render V10 settings page"""
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                letter-spacing: 0.15em; margin-bottom: 1.5rem;">CONFIGURATION</div>
    """, unsafe_allow_html=True)

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

    # Tabs for different settings sections - V10 styling
    tab_names = ["AI_ENGINE", "DISPLAY", "ACCOUNTS", "LIMITS", "SECURITY"]
    tab1, tab_display, tab2, tab3, tab4 = st.tabs(tab_names)

    # Auto-select tab if coming from quick action
    if settings_tab == "provider":
        st.session_state.settings_tab = None  # Reset

    # ============================================================================
    # TAB 1: AI Model Configuration
    # ============================================================================
    with tab1:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 0.5rem;">AI_ENGINE_CONFIG</div>
        """, unsafe_allow_html=True)
        st.caption("SELECT_AI_PROVIDER")

        # Current model display with V10 messaging
        llm_config = SettingsManager.get_llm_config(user_id)

        if llm_config["using_default"]:
            st.warning("NO_ENGINE_CONNECTED. Add API key below.")
        else:
            st.success(f"CONNECTED: {llm_config['provider'].upper()} - {llm_config['model']}")

        st.divider()

        # LLM Provider selection with V10 descriptions
        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px;">SELECT_PROVIDER</div>""", unsafe_allow_html=True)
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
        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px; margin-top: 12px;">SELECT_MODEL</div>""", unsafe_allow_html=True)
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
        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px; margin-top: 12px;">API_KEY</div>""", unsafe_allow_html=True)
        st.caption("REQUIRED_FOR_AI_ENGINE")

        # Show if key is already configured
        has_existing_key = bool(existing_settings and existing_settings.get("llm_api_key_encrypted"))
        if has_existing_key:
            st.success("KEY_STORED_SECURELY")
            st.caption("PASTE_NEW_KEY_TO_UPDATE")

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
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 0.5rem;">DISPLAY_CONFIG</div>
        """, unsafe_allow_html=True)
        st.caption("INTERFACE_PREFERENCES")

        # Theme selection (light/dark)
        current_theme = existing_settings.get("theme", "dark") if existing_settings else "dark"
        theme = st.radio(
            "Theme",
            ["dark", "light"],
            format_func=lambda x: "DARK" if x == "dark" else "LIGHT",
            index=0 if current_theme == "dark" else 1,
            horizontal=True
        )

        st.caption("DARK_MODE_RECOMMENDED")

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
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 0.5rem;">CONNECTED_ACCOUNTS</div>
        """, unsafe_allow_html=True)

        # List connected accounts
        connected = SettingsManager.list_connected_accounts(user_id)

        if connected:
            for conn in connected:
                col1, col2 = st.columns([3, 1])
                with col1:
                    status = "ACTIVE" if conn['is_active'] else "INACTIVE"
                    account = conn.get('provider_user_id', '')
                    st.markdown(f"**{conn['provider'].upper()}** {f'({account})' if account else ''}")
                    st.caption(status)
                with col2:
                    if conn['is_active']:
                        if st.button("DISCONNECT", key=f"disconnect_{conn['provider']}", use_container_width=True):
                            if SettingsManager.disconnect_account(user_id, conn['provider']):
                                st.rerun()
            st.divider()

        # Email connection
        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px;">EMAIL_CONNECTION</div>""", unsafe_allow_html=True)
        st.caption("CONNECT_EMAIL_FOR_AI_AUTOMATION")

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
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 0.5rem;">SPENDING_LIMITS</div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            daily_limit = st.number_input(
                "DAILY_LIMIT (USDC)",
                min_value=1.0,
                max_value=10000.0,
                value=float(existing_settings.get("daily_spend_limit", 100.0)) if existing_settings else 100.0,
                step=10.0
            )
            st.caption("MAX_AI_SPEND_PER_DAY")

        with col2:
            approval_threshold = st.number_input(
                "APPROVAL_THRESHOLD (USDC)",
                min_value=0.0,
                max_value=1000.0,
                value=float(existing_settings.get("require_approval_above", 50.0)) if existing_settings else 50.0,
                step=5.0
            )
            st.caption("REQUIRE_APPROVAL_ABOVE")

        st.divider()

        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px;">PERMISSIONS</div>""", unsafe_allow_html=True)

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
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 0.5rem;">SECURITY_CONFIG</div>
        """, unsafe_allow_html=True)

        # Export wallet section
        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px;">EXPORT_WALLET</div>""", unsafe_allow_html=True)

        if st.button("SHOW_PRIVATE_KEY", type="secondary", key="show_pk"):
            st.session_state.show_private_key = True

        if st.session_state.get("show_private_key"):
            from wallet_manager import WalletManager
            wallet_data = WalletManager.get_wallet_from_session()

            if wallet_data and wallet_data.get("private_key"):
                st.warning("NEVER_SHARE_PRIVATE_KEY")

                if wallet_data.get("mnemonic"):
                    st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                                letter-spacing: 0.1em; margin-bottom: 4px;">SEED_PHRASE</div>""", unsafe_allow_html=True)
                    st.code(wallet_data["mnemonic"], language=None)

                st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                            letter-spacing: 0.1em; margin-bottom: 4px; margin-top: 8px;">PRIVATE_KEY</div>""", unsafe_allow_html=True)
                st.code(wallet_data["private_key"], language=None)

                if st.button("HIDE", key="hide_pk"):
                    st.session_state.show_private_key = False
                    st.rerun()
            else:
                st.error("CANNOT_RETRIEVE_KEY")
                if st.button("HIDE", key="hide_pk_err"):
                    st.session_state.show_private_key = False
                    st.rerun()

        st.divider()

        # Data info
        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px;">DATA_STORAGE</div>""", unsafe_allow_html=True)
        st.caption("""
        WALLET_KEYS: ENCRYPTED_IN_SESSION
        API_KEYS: AES-256_ENCRYPTED
        OAUTH_TOKENS: AES-256_ENCRYPTED
        """)

        st.divider()

        # Danger zone - these actions are available
        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #ef4444;
                    letter-spacing: 0.1em; margin-bottom: 4px;">DANGER_ZONE</div>""", unsafe_allow_html=True)
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
