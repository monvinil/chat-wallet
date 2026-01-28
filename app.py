# -*- coding: utf-8 -*-
"""
USDChat - Your money, your words
AI-powered wallet that turns conversation into action
"""

import os
import json
import time
import streamlit as st
import qrcode
from io import BytesIO
from datetime import datetime

# Lazy import LangChain modules only when needed (saves 1-2s on initial load)
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import HumanMessage, AIMessage
# from langchain_core.tools import tool
# from langchain.agents import AgentExecutor, create_tool_calling_agent
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Local imports
from config import NETWORKS, calculate_fee
from wallet_manager import WalletManager
from chain_utils import ChainUtils
from supabase_client import (
    get_supabase_client,
    get_user_by_email,
    create_user,
    save_wallet_address,
    get_user_wallets,
    log_transaction,
    get_user_password_hash,
    update_user_password_hash,
    get_encrypted_wallet,
    get_user_login_data  # Batched login query
)
from settings_ui import settings_page
from session_manager import SessionManager
from styles import MAIN_CSS

# Import UI components from components package
from components import (
    sidebar,
    deposit_modal,
    send_modal,
    seed_phrase_modal,
    chat_interface
)

# ============================================================================
# CONFIG
# ============================================================================

SYSTEM_PROMPT = """You are a professional wallet assistant that helps users manage their self-custodial wallet across multiple blockchain networks.

**Your capabilities:**
1. Check balances - Always present in dollars first (e.g., "$50.00 USDC total")
2. **Send transactions** - Two-step process:
   - First: Call preview_transaction to show amount, fee, total
   - After user says "yes"/"approve"/"send it": Call execute_transaction with user_confirmed=True
   - NEVER execute without explicit user confirmation
3. Generate deposit addresses and QR codes for receiving funds
4. **Pay bills with USDC** via gift cards:
   - AWS bills → Amazon gift cards (AWS accepts them for billing)
   - Netflix, Spotify, Uber, etc. → Direct gift cards
   - Use pay_bill_with_giftcard tool for smart vendor detection
   - Automatically suggests correct card amount and provides redemption steps
5. **Buy gift cards** via Bitrefill API:
   - Search 1000+ gift cards (Amazon, Uber, Netflix, Starbucks, etc.)
   - Purchase with USDC
   - Codes delivered to user's email
6. **Direct crypto purchases** from merchants:
   - Domains: Porkbun, Namecheap (BTC, ETH, USDC)
   - VPN: Mullvad (anonymous, no email), Proton (BTC only)
   - Travel: Travala (hotels, flights with 90+ cryptos)
   - Use search_crypto_merchants to find merchants
   - Use buy_domain_with_crypto, subscribe_vpn_with_crypto for purchases
7. **Email automation** (if user connected email):
   - Read verification codes from emails
   - Search recent emails (last 24 hours)
   - Detect bills from emails automatically
8. Execute multi-step tasks - bill payments, gift cards, service signups
9. **Scheduled & recurring payments** (demo mode):
   - One-time scheduled transfers: "Send $50 to 0x... tomorrow at 9am"
   - Recurring payments: "Send $100 to 0x... every Friday"
   - Recurring gift cards: "Buy a $25 Starbucks card every Monday"
   - Conditional triggers: "If my balance drops below $100, alert me"
   - Use create_scheduled_transfer, create_scheduled_gift_card for setup
   - Use list_scheduled_tasks to show user's scheduled items

**Email Automation Workflow:**
When user asks to sign up for a service (e.g., Porkbun, Amazon):
1. Check if email is connected (use check_email_connected tool)
2. If not connected, ask user to connect email in Settings → Connected Accounts
3. Use the user's connected email to fill signup forms
4. After submitting form, wait 30-60 seconds
5. Use get_verification_code tool to retrieve code from email
6. Complete signup with the code

**Transaction flow:**
1. User: "Send $25 to 0x..." or "Pay my AWS bill"
2. You: Call preview_transaction → Show preview card → Ask "Ready to send?"
3. User: "Yes" / "Approve" / "Send it" / "Do it"
4. You: Call execute_transaction(user_confirmed=True) → Report success with tx hash

**Communication guidelines:**
- Present balances in dollars first: "$50.00 USDC" not "50 USDC tokens"
- After transaction preview, ask: "Ready to send?" or "Should I proceed?"
- Confirm completed actions: "Sent $20.00 to 0x1234...5678 on Arc (tx: 0xabc...)"
- Be direct and professional, not overly conversational

**Important rules:**
- User controls private keys (self-custodial)
- ALWAYS preview before executing
- NEVER execute without explicit user confirmation ("yes", "approve", etc.)
- Email access: Only last 24 hours
- Ask before signing up for external services

**Supported networks:**
Arc (testnet - primary), Base, Arbitrum, Ethereum, Solana

**Fees:** $0.005 + 0.2% (max $3) - Network fees free on testnet
"""

# Note: Mock data removed - using real API clients with built-in mock mode
# Gift cards: bitrefill_client.py has mock mode when API keys not configured
# Emails: email_tools.py uses real EmailManager with IMAP

# ============================================================================
# TOOLS
# ============================================================================

def _get_solana_address_from_session() -> str:
    """Get Solana address from wallet data in session"""
    # Try from decrypted wallet data first
    wallet_data = WalletManager.get_wallet_from_session()
    if wallet_data and wallet_data.get("solana"):
        return wallet_data["solana"].get("address")

    # Fallback: check session state directly (for guest wallets)
    if st.session_state.get("solana_address"):
        return st.session_state.solana_address

    return None


def get_wallet_balance() -> str:
    """Get current wallet balances across all chains. No arguments needed."""
    if "wallet_address" not in st.session_state:
        return json.dumps({"error": "No wallet connected"})

    address = st.session_state.wallet_address
    solana_address = _get_solana_address_from_session()
    balances = ChainUtils.get_all_balances(address, solana_address)
    total_usdc = ChainUtils.calculate_total_usdc(balances)

    # Build a clean, dollar-first response
    result = {
        "total_balance": f"${total_usdc:.2f} USDC",
        "address": ChainUtils.format_address(address),
        "breakdown_by_network": {}
    }

    # Add Solana address if available
    if solana_address:
        result["solana_address"] = ChainUtils.format_address(solana_address)

    for network_key, chain_balances in balances.items():
        network_name = NETWORKS[network_key]["name"]
        usdc = chain_balances.get("usdc", 0.0)
        native = chain_balances.get("eth", chain_balances.get("sol", 0.0))

        result["breakdown_by_network"][network_name] = {
            "usdc": f"${usdc:.2f}",
            "native_token": f"{native:.4f}" if native > 0 else "0"
        }

    return json.dumps(result, indent=2)


def get_deposit_address(chain: str = "base-mainnet") -> str:
    """Get deposit address for a specific chain. Args: chain - network key like 'base-mainnet' or 'arbitrum-mainnet'"""
    if "wallet_address" not in st.session_state:
        return json.dumps({"error": "No wallet connected"})

    address = st.session_state.wallet_address
    network = NETWORKS.get(chain, NETWORKS["base-mainnet"])

    return json.dumps({
        "chain": network["name"],
        "address": address,
        "explorer": ChainUtils.get_explorer_url(chain, address),
        "usdc_address": network.get("usdc_address"),
        "note": "Send USDC or native tokens to this address"
    }, indent=2)


def execute_transaction(to_address: str, amount_usd: float, chain: str = "arc-testnet", user_confirmed: bool = False) -> str:
    """
    Execute a USDC transfer after user confirmation.
    IMPORTANT: Only call this AFTER the user has explicitly said 'yes', 'approve', 'send it', or similar.
    Args: to_address, amount_usd, chain (network key), user_confirmed (must be True)
    """
    if not user_confirmed:
        return json.dumps({
            "error": "User confirmation required",
            "message": "Please ask the user to confirm before executing. They must say 'yes', 'approve', or 'send it'."
        })

    if "wallet_address" not in st.session_state:
        return json.dumps({"error": "No wallet connected"})

    # Check if there's an approved transaction in session (from UI card)
    approved_tx = st.session_state.get("_tx_approved")
    if approved_tx:
        to_address = approved_tx.get("to_full_address", to_address)
        amount_usd = approved_tx.get("amount_raw", amount_usd)
        chain = approved_tx.get("chain", chain)
        st.session_state._tx_approved = None
        st.session_state._pending_tx_preview = None

    try:
        from direct_tx import get_direct_executor
        from wallet_manager import WalletManager

        wallet_data = WalletManager.get_wallet_from_session()
        if not wallet_data:
            return json.dumps({"error": "Wallet is locked. Please unlock your wallet first."})

        private_key = wallet_data.get("private_key") or wallet_data.get("evm", {}).get("private_key")
        if not private_key:
            return json.dumps({"error": "Could not access wallet keys"})

        executor = get_direct_executor(chain)
        user_id = st.session_state.get("user_id")

        result = executor.execute_transfer(
            private_key=private_key,
            to_address=to_address,
            amount_usdc=amount_usd,
            user_id=user_id
        )

        if result["success"]:
            return json.dumps({
                "status": "success",
                "message": f"Successfully sent ${amount_usd:.2f} USDC",
                "tx_hash": result["tx_hash"],
                "explorer_url": result["explorer_url"],
                "amount": result["amount"],
                "to": result["to"],
                "network": result["network"]
            }, indent=2)
        else:
            return json.dumps({"status": "failed", "error": result["error"]})

    except Exception as e:
        return json.dumps({"error": f"Transaction failed: {str(e)}"})


def preview_transaction(to_address: str, amount_usd: float, chain: str = "arc-testnet") -> str:
    """
    Preview a transaction before execution. Shows exact amounts, fees, and timing.
    Args: to_address, amount_usd, chain (network key)
    """
    if "wallet_address" not in st.session_state:
        return json.dumps({"error": "No wallet connected"})

    network = NETWORKS.get(chain, NETWORKS["base-mainnet"])
    fee = calculate_fee(amount_usd)
    total = amount_usd + fee

    preview = {
        "action": "Send USDC",
        "amount": f"${amount_usd:.2f}",
        "amount_raw": amount_usd,
        "to": ChainUtils.format_address(to_address),
        "to_full_address": to_address,
        "network": network["name"],
        "chain": chain,
        "fee": f"${fee:.3f}",
        "fee_raw": fee,
        "total_cost": f"${total:.2f}",
        "total_raw": total,
        "estimated_time": "~3-5 seconds",
        "from": ChainUtils.format_address(st.session_state.wallet_address),
        "from_full_address": st.session_state.wallet_address,
        "status": "pending_approval"
    }

    # Store in session state for UI to render as card
    st.session_state._pending_tx_preview = preview

    return json.dumps({
        "preview_generated": True,
        "amount": preview["amount"],
        "to": preview["to"],
        "network": preview["network"],
        "fee": preview["fee"],
        "total": preview["total_cost"],
        "message": "Transaction preview ready. Ask the user to confirm before proceeding."
    }, indent=2)


# read_latest_emails removed - use email_tools.search_recent_emails instead


# ============================================================================
# AGENT
# ============================================================================

def _get_cached_tools():
    """Get cached tool list (created once per session)"""
    if "_cached_tools" not in st.session_state:
        from langchain_core.tools import tool

        # Wrap core tools with @tool decorator (only done once)
        tool_get_wallet_balance = tool(get_wallet_balance)
        tool_get_deposit_address = tool(get_deposit_address)
        tool_preview_transaction = tool(preview_transaction)
        tool_execute_transaction = tool(execute_transaction)

        # Import and get external tools (only done once)
        from email_tools import get_email_tools
        from bitrefill_tools import get_bitrefill_tools
        from merchant_tools import get_merchant_tools
        from scheduler_tools import get_scheduler_tools

        st.session_state._cached_tools = [
            tool_get_wallet_balance,
            tool_get_deposit_address,
            tool_preview_transaction,
            tool_execute_transaction,
        ] + get_email_tools() + get_bitrefill_tools() + get_merchant_tools() + get_scheduler_tools()

    return st.session_state._cached_tools


def create_agent():
    """Create the LangChain agent (lazy import for faster initial load)"""
    # Lazy import LangChain modules - using new langchain 1.2+ API
    from langchain.agents import create_agent
    from settings_manager import SettingsManager

    # Get user's LLM config (custom API key if set, otherwise app default)
    user_id = st.session_state.get("user_id")
    llm_config = SettingsManager.get_llm_config(user_id)

    # Validate API key exists (should be caught by banner, but safety check)
    if not llm_config.get("api_key"):
        return None  # Banner will handle this

    # Create LLM based on provider
    provider = llm_config.get("provider", "anthropic")

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=llm_config.get("model", "gpt-4o"),
            api_key=llm_config.get("api_key"),
            temperature=0.3,
            max_tokens=4096,
            streaming=True
        )
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=llm_config.get("model", "gemini-2.5-flash"),
            google_api_key=llm_config.get("api_key"),
            temperature=0.3,
            max_output_tokens=4096
        )
    else:  # Default to Anthropic
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=llm_config.get("model", "claude-sonnet-4-20250514"),
            api_key=llm_config.get("api_key"),
            temperature=0.3,
            max_tokens=4096,
            streaming=True
        )

    # Get cached tools (only created once per session)
    custom_tools = _get_cached_tools()

    # Create agent using new langchain 1.2+ API
    agent = create_agent(
        model=llm,
        tools=custom_tools,
        system_prompt=SYSTEM_PROMPT
    )

    return agent


# ============================================================================
# UI COMPONENTS
# ============================================================================

def init_state():
    """Initialize session state"""
    defaults = {
        "messages": [],
        "agent": None,
        "wallet_address": None,
        "wallet_locked": False,  # Don't lock by default - let session restore handle it
        "authenticated": False,
        "user_email": None,
        "balances": {},
        "pending_tx": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _handle_login(login_email: str, login_password: str):
    """Handle login form submission"""
    if not login_email or not login_password:
        st.error("Please enter email and password")
        return

    with st.spinner("Signing in..."):
        from rate_limiter import RateLimiter

        allowed, lockout_msg = RateLimiter.check_login_allowed(login_email)
        if not allowed:
            st.error(lockout_msg)
            return

        login_data = get_user_login_data(login_email)

        if not login_data:
            st.error("No account found with this email")
            return

        user = login_data["user"]
        stored_hash = login_data["password_hash"]
        wallets = login_data["wallets"]
        encrypted_wallet = login_data["encrypted_wallet"]

        # Verify password
        if stored_hash and not WalletManager.verify_password(login_password, stored_hash):
            RateLimiter.record_login_attempt(login_email, success=False)
            remaining = RateLimiter.get_remaining_attempts(login_email)
            if remaining > 0:
                st.error(f"Incorrect password. {remaining} attempt(s) remaining.")
            else:
                st.error("Account temporarily locked.")
            return

        if not wallets or len(wallets) == 0:
            st.error("No wallet found for this account")
            return

        # Successful login
        RateLimiter.record_login_attempt(login_email, success=True)
        wallet_address = wallets[0]["wallet_address"]

        st.session_state.wallet_address = wallet_address
        st.session_state.user_email = login_email
        st.session_state.user_id = user["id"]
        st.session_state.show_auth_modal = False

        SessionManager.login(user["id"], login_email, wallet_address)

        # Update password hash if legacy account
        if not stored_hash:
            new_hash = WalletManager.hash_password(login_password)
            update_user_password_hash(user["id"], new_hash)

        # Restore encrypted wallet
        if encrypted_wallet:
            st.session_state.wallet_encrypted = encrypted_wallet["encrypted_data"]
            st.session_state.wallet_salt = encrypted_wallet["salt"]

            if WalletManager.unlock_wallet_with_password(login_password):
                st.session_state.wallet_locked = False
                wallet_data = WalletManager.get_wallet_from_session()
                if wallet_data and wallet_data.get("solana"):
                    sol_addr = wallet_data["solana"].get("address")
                    if sol_addr:
                        st.session_state.solana_address = sol_addr
                        save_wallet_address(user["id"], sol_addr, chain="solana")
            else:
                st.session_state.wallet_locked = True
        else:
            st.session_state.wallet_locked = True

        # Check onboarding status
        from settings_manager import SettingsManager
        user_settings = SettingsManager.get_llm_config(user["id"])
        if not user_settings.get("api_key"):
            st.session_state.onboarding_step = 2
            st.session_state.onboarding_complete = False

        st.rerun()


def _handle_signup(email: str, password: str):
    """Handle signup form submission"""
    with st.spinner("Creating account..."):
        existing_user = get_user_by_email(email)
        if existing_user:
            st.error("Account already exists. Please log in.")
            return

        wallet_info = WalletManager.create_new_wallet()
        if not wallet_info:
            st.error("Could not create wallet. Please try again.")
            return

        password_hash = WalletManager.hash_password(password)

        try:
            user = create_user(
                email=email,
                primary_wallet_address=wallet_info["address"],
                password_hash=password_hash
            )
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Create user failed: {str(e)}")
            st.error("Could not create account. Please try again.")
            return

        if not user:
            st.error("Could not create account. Please try again.")
            return

        # Encrypt wallet
        encrypted = WalletManager.encrypt_wallet_data(wallet_info["wallet_data"], password)

        st.session_state.wallet_encrypted = encrypted["encrypted_data"]
        st.session_state.wallet_salt = encrypted["salt"]
        st.session_state.wallet_key = encrypted["key"]
        st.session_state.wallet_locked = False

        # Save to cloud
        save_wallet_address(
            user["id"],
            wallet_info["address"],
            encrypted_wallet_data=encrypted["encrypted_data"],
            encryption_salt=encrypted["salt"]
        )

        st.session_state.wallet_address = wallet_info["address"]
        st.session_state.user_email = email
        st.session_state.user_id = user["id"]

        # Solana address
        solana_addr = wallet_info.get("solana_address")
        if solana_addr:
            st.session_state.solana_address = solana_addr
            save_wallet_address(user["id"], solana_addr, chain="solana")

        SessionManager.login(user["id"], email, wallet_info["address"], solana_addr)

        # Show seed phrase modal
        if wallet_info.get("mnemonic"):
            st.session_state._pending_seed_phrase = wallet_info["mnemonic"]
            st.session_state.show_auth_modal = False
            st.session_state.show_seed_phrase_modal = True
            st.rerun()
        else:
            st.session_state.show_auth_modal = False
            st.session_state.onboarding_step = 1
            st.session_state.onboarding_complete = False
            st.rerun()


def wallet_setup_ui():
    """Show wallet setup screen with email/password account - V24 Streamlined"""
    from design_system import DS

    # Clean header - centered, minimal
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-family: {DS.typography.FONT_SANS}; font-size: 28px; font-weight: 300; letter-spacing: -0.04em; margin-bottom: 8px; color: {DS.colors.TEXT_PRIMARY};">USDChat</h1>
        <div style="font-family: {DS.typography.FONT_SANS}; font-size: 14px; font-weight: 300; color: {DS.colors.TEXT_SECONDARY};">
            Your AI wallet assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Two tabs only - Log In first (most users are returning)
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    # ========== TAB 1: LOG IN ==========
    with tab1:
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <div style="font-family: {DS.typography.FONT_SANS}; font-size: 13px; color: {DS.colors.TEXT_MUTED};">Welcome back</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form(key="login_form", clear_on_submit=False):
            login_email = st.text_input(
                "Email",
                key="login_email",
                placeholder="your@email.com",
                autocomplete="username"
            )
            login_password = st.text_input(
                "Password",
                type="password",
                key="login_pwd",
                autocomplete="current-password"
            )

            submit_login = st.form_submit_button("Log In", type="primary", use_container_width=True)

        if submit_login:
            _handle_login(login_email, login_password)

        # Import wallet link (not a full tab)
        st.markdown(f"""
        <div style="text-align: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid {DS.colors.BORDER_HAIRLINE};">
            <div style="font-family: {DS.typography.FONT_MONO}; font-size: 11px; color: {DS.colors.TEXT_MUTED};">
                Have a recovery phrase?
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Import existing wallet", use_container_width=True, key="import_link"):
            st.session_state._show_import = True
            st.rerun()

    # ========== TAB 2: SIGN UP ==========
    with tab2:
        st.markdown(f"""
        <div style="margin-bottom: 24px;">
            <div style="font-family: {DS.typography.FONT_SANS}; font-size: 13px; color: {DS.colors.TEXT_MUTED};">Create your wallet</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form(key="signup_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                key="signup_email",
                placeholder="your@email.com",
                autocomplete="username"
            )
            password = st.text_input(
                "Password",
                type="password",
                key="signup_pwd",
                autocomplete="new-password",
                help="Minimum 8 characters"
            )

            submit_signup = st.form_submit_button("Create Account", type="primary", use_container_width=True)

        if submit_signup:
            if not email or not password:
                st.error("Please enter both email and password")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters")
            elif "@" not in email:
                st.error("Please enter a valid email address")
            else:
                _handle_signup(email, password)

        st.markdown(f"""
        <div style="font-family: {DS.typography.FONT_MONO}; font-size: 10px; color: {DS.colors.TEXT_GHOST}; margin-top: 16px; text-align: center;">
            Encrypted backup syncs across devices
        </div>
        """, unsafe_allow_html=True)

    # ========== IMPORT WALLET MODAL ==========
    if st.session_state.get("_show_import"):
        # Back button
        if st.button("← Back to login", key="back_from_import"):
            st.session_state._show_import = False
            st.rerun()

        st.markdown(f"""
        <div style="margin: 16px 0 24px 0;">
            <div style="font-family: {DS.typography.FONT_SANS}; font-size: 16px; font-weight: 400; color: {DS.colors.TEXT_PRIMARY}; margin-bottom: 4px;">Import Wallet</div>
            <div style="font-family: {DS.typography.FONT_SANS}; font-size: 12px; color: {DS.colors.TEXT_MUTED};">Use your 12-word recovery phrase or private key</div>
        </div>
        """, unsafe_allow_html=True)

        recovery_input = st.text_area(
            "Recovery phrase or private key",
            key="import_recovery",
            placeholder="word1 word2 word3 ... or 0x...",
            height=80,
            label_visibility="collapsed"
        )
        import_password = st.text_input(
            "Encryption password",
            type="password",
            key="import_pwd",
            placeholder="Password to encrypt wallet"
        )
        import_email = st.text_input(
            "Email (optional)",
            key="import_email",
            placeholder="your@email.com",
            help="Link to an account for cloud backup"
        )

        if st.button("Import Wallet", type="primary", use_container_width=True, disabled=not (recovery_input and import_password)):
            with st.spinner("Importing..."):
                wallet_info = WalletManager.import_wallet(recovery_input.strip())

                if wallet_info:
                    WalletManager.save_wallet_to_session(wallet_info["wallet_data"], import_password)
                    st.session_state.wallet_address = wallet_info["address"]
                    st.session_state.wallet_locked = False
                    st.session_state.show_auth_modal = False
                    st.session_state._show_import = False

                    if import_email and "@" in import_email:
                        user = get_user_by_email(import_email)
                        if not user:
                            user = create_user(import_email, wallet_info["address"])
                        if user:
                            save_wallet_address(user["id"], wallet_info["address"])
                            st.session_state.user_email = import_email
                            st.session_state.user_id = user["id"]

                    st.success("Wallet imported")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid recovery phrase or private key")


def _show_loading_skeleton():
    """Show loading skeleton while session restores"""
    st.markdown("""
    <style>
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    .loading-skeleton {
        background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s ease-in-out infinite;
        border-radius: 8px;
    }
    .loading-container {
        max-width: 1100px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    .loading-header {
        height: 24px;
        width: 120px;
        margin-bottom: 24px;
    }
    .loading-cards {
        display: flex;
        gap: 12px;
        margin-bottom: 32px;
    }
    .loading-card {
        flex: 1;
        height: 96px;
        border-radius: 14px;
    }
    .loading-tabs {
        display: flex;
        gap: 24px;
        margin-bottom: 16px;
    }
    .loading-tab {
        height: 14px;
        width: 60px;
    }
    .loading-chat {
        height: 200px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    .loading-input {
        height: 48px;
        border-radius: 24px;
    }
    </style>
    <div class="loading-container">
        <div class="loading-skeleton loading-header"></div>
        <div class="loading-cards">
            <div class="loading-skeleton loading-card"></div>
            <div class="loading-skeleton loading-card"></div>
            <div class="loading-skeleton loading-card"></div>
            <div class="loading-skeleton loading-card"></div>
        </div>
        <div class="loading-tabs">
            <div class="loading-skeleton loading-tab"></div>
            <div class="loading-skeleton loading-tab"></div>
            <div class="loading-skeleton loading-tab"></div>
            <div class="loading-skeleton loading-tab"></div>
        </div>
        <div class="loading-skeleton loading-chat"></div>
        <div class="loading-skeleton loading-input"></div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main app entry point"""
    st.set_page_config(
        page_title="Chat Wallet",
        page_icon="◈",
        layout="wide",  # Keep wide but use CSS for responsive
        initial_sidebar_state="auto"  # Collapse on mobile
    )

    # V22 Design System CSS - loaded from cached module constant
    st.markdown(MAIN_CSS, unsafe_allow_html=True)

    # PWA Meta Tags - mobile app-like experience
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
    <meta name="theme-color" content="#09090b">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    """, unsafe_allow_html=True)

    init_state()

    # Initialize cookie manager and restore session from cookie
    # This handles page refresh - session state is cleared but cookies persist
    if not st.session_state.get("wallet_address"):
        # First run: show skeleton while we attempt restore
        if not st.session_state.get("_session_restore_attempted"):
            _show_loading_skeleton()

            try:
                SessionManager.get_cookie_manager()
                restored = SessionManager.restore_session()
                st.session_state._session_restore_attempted = True

                if restored:
                    # Load user theme preference if logged in
                    user_id = st.session_state.get("user_id")
                    if user_id and not st.session_state.get("user_theme"):
                        from settings_manager import SettingsManager
                        user_settings = SettingsManager.get_user_settings(user_id)
                        if user_settings and user_settings.get("theme"):
                            st.session_state.user_theme = user_settings["theme"]
            except Exception as e:
                # Log session restore errors server-side only
                from utils.logger import logger
                logger.warning(f"Session restore error: {e}")
                st.session_state._session_restore_attempted = True

            # Rerun to show proper UI (either restored session or auth modal)
            st.rerun()

    # SECURITY: Removed wallet key cookie saving
    # Wallet key is only stored in session state (memory)
    # Users must re-enter password after page refresh

    # Check session timeout and lock wallet if inactive
    from rate_limiter import check_and_handle_timeout, RateLimiter
    if not check_and_handle_timeout():
        st.toast("Session timed out. Wallet locked for security.")

    # Update activity timestamp on each interaction
    RateLimiter.update_activity()

    # Handle OAuth callback (simplified - no blocking sleep)
    query_params = st.query_params
    if "code" in query_params and "state" in query_params:
        from gmail_oauth import GmailOAuth

        code = query_params["code"]
        user_id = query_params["state"]

        app_url = os.getenv("APP_URL", "http://localhost:8501")
        redirect_uri = f"{app_url}/oauth/callback"

        success = GmailOAuth.handle_oauth_callback(code, redirect_uri, user_id)

        # Clear params immediately to prevent reprocessing
        st.query_params.clear()
        st.session_state.show_settings = True
        st.session_state._oauth_result = "success" if success else "error"

    # Show auth modal if requested
    if st.session_state.get("show_auth_modal"):
        wallet_setup_ui()
        if st.button("← Back to Home", use_container_width=False):
            st.session_state.show_auth_modal = False
        return

    # Initialize agent if user is logged in (even if wallet is locked - agent can still help)
    # Agent needs: user_id (for API key lookup) and either wallet_address or user session
    if (st.session_state.get("user_id") or st.session_state.wallet_address) and st.session_state.agent is None:
        if not st.session_state.get("_agent_initializing"):
            st.session_state._agent_initializing = True
            try:
                agent = create_agent()
                if agent:
                    st.session_state.agent = agent
            except Exception as e:
                from utils.logger import logger
                logger.error(f"Agent initialization error: {e}")
            finally:
                st.session_state._agent_initializing = False

    # Fetch balances once (don't block, just set empty if not loaded)
    if st.session_state.wallet_address and not st.session_state.get("balances"):
        st.session_state.balances = {}
        st.session_state._balance_loading = True
        # Only fetch if not locked
        if not st.session_state.get("wallet_locked", True):
            try:
                solana_addr = _get_solana_address_from_session()
                balances = ChainUtils.get_all_balances(st.session_state.wallet_address, solana_addr)
                st.session_state.balances = balances
            except Exception as e:
                from utils.logger import logger
                logger.error(f"Balance fetch error: {e}")
            finally:
                st.session_state._balance_loading = False

    # Show seed phrase modal after signup (must be shown before anything else)
    if st.session_state.get("show_seed_phrase_modal") and st.session_state.get("_pending_seed_phrase"):
        seed_phrase_modal()
        return

    # Show deposit modal if requested (only if logged in)
    if st.session_state.get("show_deposit_modal") and st.session_state.wallet_address:
        deposit_modal()
        if st.button("← Back"):
            st.session_state.show_deposit_modal = False
        return

    # Show send modal if requested (only if logged in)
    if st.session_state.get("show_send_modal") and st.session_state.wallet_address:
        send_modal()
        return

    # Show settings page if requested (allow access even when wallet is locked)
    if st.session_state.get("show_settings") and (st.session_state.wallet_address or st.session_state.get("user_id")):
        # Keep sidebar visible for consistent navigation
        sidebar()

        # Show OAuth result toast if just completed
        if st.session_state.get("_oauth_result"):
            if st.session_state._oauth_result == "success":
                st.success("Gmail connected successfully!")
            else:
                st.error("Failed to connect Gmail")
            st.session_state._oauth_result = None
        settings_page()
        if st.button("← Back"):
            st.session_state.show_settings = False
        return

    # Main layout - always show (preview or logged in)
    sidebar()
    chat_interface(create_agent)


if __name__ == "__main__":
    main()
