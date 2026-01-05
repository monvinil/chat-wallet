"""
Settings UI - User settings, LLM configuration, and account connections
"""

import streamlit as st
from settings_manager import SettingsManager
from typing import Optional


def settings_page():
    """Render settings page"""
    st.title("⚙️ Settings")
    st.caption("Customize your wallet experience")

    # Check if user is logged in
    if not st.session_state.get("wallet_address"):
        st.warning("Please log in to access settings")
        return

    # Get user ID (for now, use wallet address as user_id)
    user_id = st.session_state.wallet_address

    # Load existing settings
    existing_settings = SettingsManager.get_user_settings(user_id)

    # Tabs for different settings sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AI Model",
        "🔗 Connected Accounts",
        "💰 Spending & Approvals",
        "🔒 Security"
    ])

    # ============================================================================
    # TAB 1: AI Model Configuration
    # ============================================================================
    with tab1:
        st.subheader("AI Model Configuration")
        st.write("Choose which AI model powers your wallet assistant.")

        # Current model display
        llm_config = SettingsManager.get_llm_config(user_id)

        if llm_config["using_default"]:
            st.info(f"**Currently using:** Default model ({llm_config['model']})")
            st.caption("Using our API key. You're not charged for AI usage.")
        else:
            st.success(f"**Currently using:** Your custom {llm_config['provider']} ({llm_config['model']})")

        st.divider()

        # LLM Provider selection
        provider = st.selectbox(
            "AI Provider",
            ["anthropic", "openai"],
            format_func=lambda x: {
                "anthropic": "Anthropic (Claude)",
                "openai": "OpenAI (GPT-4)"
            }[x],
            index=0 if not existing_settings else
                  ["anthropic", "openai"].index(existing_settings.get("llm_provider", "anthropic"))
        )

        # Model selection based on provider
        if provider == "anthropic":
            model_options = {
                "claude-opus-4-20250514": "Claude Opus 4 (Most capable, slower)",
                "claude-sonnet-4-20250514": "Claude Sonnet 4 (Balanced) ⭐",
                "claude-haiku-4-20250514": "Claude Haiku 4 (Fast, economical)"
            }
        else:  # openai
            model_options = {
                "gpt-4-turbo": "GPT-4 Turbo (Most capable) ⭐",
                "gpt-4": "GPT-4 (Balanced)",
                "gpt-3.5-turbo": "GPT-3.5 Turbo (Fast, economical)"
            }

        default_model = existing_settings.get("llm_model") if existing_settings else list(model_options.keys())[1]
        selected_model = st.selectbox(
            "Model",
            list(model_options.keys()),
            format_func=lambda x: model_options[x],
            index=list(model_options.keys()).index(default_model) if default_model in model_options else 1
        )

        # API Key input
        st.markdown("### API Key (Optional)")
        st.caption("Leave empty to use our default model. Add your own key for custom usage.")

        show_api_key = st.checkbox("Enter custom API key", value=bool(existing_settings and existing_settings.get("llm_api_key_encrypted")))

        api_key = None
        if show_api_key:
            api_key = st.text_input(
                "API Key",
                type="password",
                placeholder=f"sk-ant-..." if provider == "anthropic" else "sk-...",
                help=f"Get your API key from {provider.capitalize()}"
            )

            st.caption(f"🔗 Get API key: [{'Anthropic Console' if provider == 'anthropic' else 'OpenAI Platform'}]({'https://console.anthropic.com' if provider == 'anthropic' else 'https://platform.openai.com'})")

        # Save button
        if st.button("💾 Save AI Configuration", type="primary"):
            success = SettingsManager.save_user_settings(
                user_id=user_id,
                llm_provider=provider,
                llm_model=selected_model,
                llm_api_key=api_key
            )

            if success:
                st.success("✅ AI configuration saved!")
                st.session_state.settings_updated = True
                st.rerun()
            else:
                st.error("❌ Failed to save settings")

    # ============================================================================
    # TAB 2: Connected Accounts
    # ============================================================================
    with tab2:
        st.subheader("Connected Accounts")
        st.write("Link external accounts to enable autonomous actions.")

        # List connected accounts
        connected = SettingsManager.list_connected_accounts(user_id)

        if connected:
            st.markdown("### Your Connections")
            for conn in connected:
                with st.expander(f"{'✅' if conn['is_active'] else '❌'} {conn['provider'].title()}"):
                    st.write(f"**Status:** {'Connected' if conn['is_active'] else 'Disconnected'}")
                    if conn.get('provider_user_id'):
                        st.write(f"**Account:** {conn['provider_user_id']}")
                    st.write(f"**Connected:** {conn['created_at'][:10]}")
                    if conn.get('scopes'):
                        st.write(f"**Permissions:** {', '.join(conn['scopes'])}")

                    if conn['is_active']:
                        if st.button(f"Disconnect {conn['provider']}", key=f"disconnect_{conn['provider']}"):
                            if SettingsManager.disconnect_account(user_id, conn['provider']):
                                st.success("Disconnected!")
                                st.rerun()
        else:
            st.info("No accounts connected yet.")

        st.divider()

        # Connect new accounts
        st.markdown("### Connect New Account")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📧 Connect Gmail", use_container_width=True, disabled=True):
                st.info("Gmail OAuth coming soon!")
                # TODO: Implement OAuth flow

        with col2:
            if st.button("🔐 Connect Google", use_container_width=True, disabled=True):
                st.info("Google OAuth coming soon!")
                # TODO: Implement OAuth flow

        st.caption("More integrations coming: Amazon, Twitter, Discord, etc.")

    # ============================================================================
    # TAB 3: Spending & Approvals
    # ============================================================================
    with tab3:
        st.subheader("Spending & Approvals")
        st.write("Control how your AI assistant spends your funds.")

        # Daily spending limit
        daily_limit = st.number_input(
            "Daily Spending Limit (USDC)",
            min_value=1.0,
            max_value=10000.0,
            value=float(existing_settings.get("daily_spend_limit", 100.0)) if existing_settings else 100.0,
            step=10.0,
            help="Maximum amount AI can spend per day"
        )

        # Approval threshold
        approval_threshold = st.number_input(
            "Require Approval Above (USDC)",
            min_value=0.0,
            max_value=1000.0,
            value=float(existing_settings.get("require_approval_above", 50.0)) if existing_settings else 50.0,
            step=5.0,
            help="Ask for approval before spending more than this amount"
        )

        # Recurring payments
        allow_recurring = st.checkbox(
            "Allow Recurring Payments",
            value=existing_settings.get("allow_recurring_payments", False) if existing_settings else False,
            help="Enable AI to set up recurring payments (subscriptions, auto-refills, etc.)"
        )

        # Account access
        allow_access = st.checkbox(
            "Allow Account Access",
            value=existing_settings.get("allow_account_access", False) if existing_settings else False,
            help="Allow AI to access connected accounts (Gmail, Google, etc.)"
        )

        st.divider()

        # Save button
        if st.button("💾 Save Preferences", type="primary"):
            success = SettingsManager.save_user_settings(
                user_id=user_id,
                daily_spend_limit=daily_limit,
                require_approval_above=approval_threshold,
                allow_recurring_payments=allow_recurring,
                allow_account_access=allow_access
            )

            if success:
                st.success("✅ Preferences saved!")
                st.rerun()
            else:
                st.error("❌ Failed to save preferences")

        # Preview
        st.markdown("### Current Rules")
        st.info(f"""
        **Daily Limit:** ${daily_limit:.2f} USDC
        **Auto-approve:** Transactions under ${approval_threshold:.2f}
        **Recurring Payments:** {'Enabled' if allow_recurring else 'Disabled'}
        **Account Access:** {'Enabled' if allow_access else 'Disabled'}
        """)

    # ============================================================================
    # TAB 4: Security
    # ============================================================================
    with tab4:
        st.subheader("Security & Privacy")
        st.write("Manage your security settings and data.")

        st.markdown("### Data Storage")
        st.info("""
        - **Wallet keys:** Encrypted in your browser session
        - **API keys:** Encrypted in database (AES-256)
        - **OAuth tokens:** Encrypted in database (AES-256)
        - **Transaction history:** Stored in Supabase
        """)

        st.markdown("### Permissions")
        st.warning("""
        **What the AI can access:**
        - Your wallet balance and transaction history
        - Connected accounts (if you grant access)
        - Spending within your limits

        **What the AI cannot do:**
        - Access your wallet without permission
        - Spend beyond your limits
        - Share your data with third parties
        """)

        st.divider()

        # Danger zone
        st.markdown("### Danger Zone")

        if st.button("🗑️ Delete All Settings", type="secondary"):
            if st.checkbox("I understand this will delete all my settings"):
                # TODO: Implement delete
                st.warning("This feature is coming soon")

        if st.button("🔓 Revoke All Connected Accounts", type="secondary"):
            if st.checkbox("I understand this will disconnect all accounts"):
                # TODO: Implement revoke all
                st.warning("This feature is coming soon")


def show_settings_button():
    """Show settings button in sidebar"""
    if st.session_state.get("wallet_address"):
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.show_settings = True
