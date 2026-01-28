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
2. Send transactions - Always preview first using preview_transaction tool, then execute after user approval
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

**Communication guidelines:**
- Present balances in dollars first: "$50.00 USDC" not "50 USDC tokens"
- When user asks to send money, use preview_transaction first to show: amount, fee, total, and time
- After showing preview, ask: "Ready to send?" or "Should I proceed?" using context from conversation
- Confirm completed actions with specifics: "Sent $20.00 to 0x1234...5678 on Base (fee: $0.02)"
- Be direct and professional, not overly conversational

**Important rules:**
- User controls private keys (self-custodial)
- User must approve every transaction
- Never execute without explicit permission
- Email access: Only last 24 hours
- Ask before signing up for external services

**Supported networks:**
Base, Arbitrum, Polygon (mainnet and testnets), Solana (coming soon)

**Fees:** $0.005 + 0.2% (max $3)
"""

# Mock data
MOCK_GIFT_CARDS = [
    {"id": "gc_001", "name": "Amazon Gift Card", "price_usd": 10},
    {"id": "gc_002", "name": "Amazon Gift Card", "price_usd": 25},
    {"id": "gc_003", "name": "Uber Gift Card", "price_usd": 25},
    {"id": "gc_004", "name": "Spotify Premium", "price_usd": 10},
    {"id": "gc_005", "name": "Netflix Gift Card", "price_usd": 15},
]

MOCK_EMAILS = [
    {"id": "1", "from": "billing@aws.amazon.com", "subject": "AWS Invoice", "snippet": "Total: $127.43", "date": "2024-12-28"},
    {"id": "2", "from": "noreply@coinbase.com", "subject": "Deposit confirmed", "snippet": "0.5 ETH", "date": "2024-12-27"},
]

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


# Old mock tools removed - now using real Bitrefill API tools from bitrefill_tools.py


def preview_transaction(to_address: str, amount_usd: float, chain: str = "base-mainnet") -> str:
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
        "to": ChainUtils.format_address(to_address),
        "to_full_address": to_address,
        "network": network["name"],
        "fee": f"${fee:.3f}",
        "total_cost": f"${total:.2f}",
        "estimated_time": "~3-5 seconds",
        "from": ChainUtils.format_address(st.session_state.wallet_address),
        "note": "User must confirm before execution"
    }

    return json.dumps(preview, indent=2)


def read_latest_emails(count: int = 3) -> str:
    """Read latest emails. Args: count - number of emails"""
    return json.dumps({"status": "success", "emails": MOCK_EMAILS[:min(count, 10)], "note": "[SIMULATED]"}, indent=2)


# ============================================================================
# AGENT
# ============================================================================

def _get_cached_tools():
    """Get cached tool list (created once per session)"""
    if "_cached_tools" not in st.session_state:
        from langchain_core.tools import tool

        # Wrap tools with @tool decorator (only done once)
        tool_get_wallet_balance = tool(get_wallet_balance)
        tool_get_deposit_address = tool(get_deposit_address)
        tool_preview_transaction = tool(preview_transaction)
        tool_read_latest_emails = tool(read_latest_emails)

        # Import and get external tools (only done once)
        from email_tools import get_email_tools
        from bitrefill_tools import get_bitrefill_tools
        from merchant_tools import get_merchant_tools
        from scheduler_tools import get_scheduler_tools

        st.session_state._cached_tools = [
            tool_get_wallet_balance,
            tool_get_deposit_address,
            tool_preview_transaction,
            tool_read_latest_emails
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
            model=llm_config.get("model", "gemini-2.0-flash"),
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


def wallet_setup_ui():
    """Show wallet setup screen with email/password account - V12 Liquid Silver"""
    # V12 Header - centered, minimal
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 24px; font-weight: 300; letter-spacing: -0.04em; margin-bottom: 12px; text-transform: none !important;">USDChat</h1>
        <div style="font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 300; color: #666; line-height: 1.6;">
            Self-custodial wallet with AI-powered transactions
        </div>
    </div>
    """, unsafe_allow_html=True)

    # V12 Info box - subtle border, no icon
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 0; padding: 16px; margin-bottom: 24px;">
        <div style="font-family: 'Inter', sans-serif; font-size: 13px; color: #888; line-height: 1.6;">
            Your wallet is encrypted locally and backed up to the cloud. Only you control the private keys.
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Sign Up", "Log In", "Import Wallet"])

    # ========== TAB 1: SIGN UP ==========
    with tab1:
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <div style="font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 400; color: white; margin-bottom: 8px;">Sign Up</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #555; line-height: 1.6;">Create a new wallet that syncs across all your devices.</div>
        </div>
        """, unsafe_allow_html=True)

        # Use form to prevent sidebar closing and enable password autofill
        with st.form(key="signup_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                key="signup_email",
                placeholder="your@email.com",
                autocomplete="username"
            )
            password = st.text_input(
                "Password (min 8 characters)",
                type="password",
                key="signup_pwd",
                autocomplete="new-password"
            )
            password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                key="signup_pwd_confirm",
                autocomplete="new-password"
            )

            submit_signup = st.form_submit_button("Create Account", type="primary", use_container_width=True)

        if submit_signup:
            if not email or not password:
                st.error("Please enter both email and password")
            elif password != password_confirm:
                st.error("Passwords do not match")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters")
            elif "@" not in email:
                st.error("Please enter a valid email address")
            else:
                with st.spinner("Creating your account..."):
                    # Check if user exists
                    existing_user = get_user_by_email(email)
                    if existing_user:
                        st.error("Account already exists. Please log in.")
                    else:
                        # Create wallet
                        wallet_info = WalletManager.create_new_wallet()

                        if wallet_info:
                            # Hash password for storage (for login verification)
                            password_hash = WalletManager.hash_password(password)

                            # Create user in Supabase with password hash
                            try:
                                user = create_user(
                                    email=email,
                                    primary_wallet_address=wallet_info["address"],
                                    password_hash=password_hash
                                )
                            except Exception as e:
                                from utils.logger import logger
                                logger.error(f"Create user failed: {str(e)}")
                                st.error("Could not create account. Please try again in a moment.")
                                user = None

                            if user:
                                # Encrypt wallet data
                                encrypted = WalletManager.encrypt_wallet_data(
                                    wallet_info["wallet_data"],
                                    password
                                )

                                # Save to session
                                st.session_state.wallet_encrypted = encrypted["encrypted_data"]
                                st.session_state.wallet_salt = encrypted["salt"]
                                st.session_state.wallet_key = encrypted["key"]
                                st.session_state.wallet_locked = False

                                # SECURITY: Do NOT save wallet key to cookie
                                # Users must re-enter password after page refresh

                                # Save encrypted wallet to Supabase for cloud backup
                                save_wallet_address(
                                    user["id"],
                                    wallet_info["address"],
                                    encrypted_wallet_data=encrypted["encrypted_data"],
                                    encryption_salt=encrypted["salt"]
                                )

                                # Update session
                                st.session_state.wallet_address = wallet_info["address"]
                                st.session_state.wallet_locked = False
                                st.session_state.user_email = email
                                st.session_state.user_id = user["id"]

                                # Store Solana address if available
                                solana_addr = wallet_info.get("solana_address")
                                if solana_addr:
                                    st.session_state.solana_address = solana_addr
                                    # Save Solana address to wallets table for persistence
                                    save_wallet_address(user["id"], solana_addr, chain="solana")

                                # Create persistent session (cookie) - include Solana address
                                SessionManager.login(user["id"], email, wallet_info["address"], solana_addr)

                                st.success("Account created")

                                # Store mnemonic for seed phrase modal and trigger it
                                if wallet_info.get("mnemonic"):
                                    st.session_state._pending_seed_phrase = wallet_info["mnemonic"]
                                    st.session_state.show_auth_modal = False
                                    st.session_state.show_seed_phrase_modal = True
                                    st.rerun()
                                else:
                                    # No seed phrase (shouldn't happen, but handle gracefully)
                                    st.session_state.show_auth_modal = False
                                    st.session_state.onboarding_step = 1
                                    st.session_state.onboarding_complete = False
                                    st.rerun()
                            else:
                                st.error("Could not create account. Please try again.")

        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; font-size: 11px; color: #444; margin-top: 16px;">
            Your wallet syncs across all your devices automatically.
        </div>
        """, unsafe_allow_html=True)

    # ========== TAB 2: LOG IN ==========
    with tab2:
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <div style="font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 400; color: white; margin-bottom: 8px;">Log In</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #555; line-height: 1.6;">Access your existing wallet.</div>
        </div>
        """, unsafe_allow_html=True)

        # Use form to prevent sidebar closing and enable password autofill
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
            if not login_email or not login_password:
                st.error("Please enter email and password")
            else:
                with st.spinner("Signing in..."):
                    # Check rate limiting before any DB queries
                    from rate_limiter import RateLimiter

                    allowed, lockout_msg = RateLimiter.check_login_allowed(login_email)
                    if not allowed:
                        st.error(lockout_msg)
                    else:
                        # OPTIMIZED: Fetch all user data in 2 queries instead of 5
                        login_data = get_user_login_data(login_email)

                        if not login_data:
                            st.error("No account found with this email")
                        else:
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
                                    st.error("Incorrect password. Account temporarily locked.")
                            elif wallets and len(wallets) > 0:
                                # Record successful login
                                RateLimiter.record_login_attempt(login_email, success=True)

                                wallet_address = wallets[0]["wallet_address"]

                                st.session_state.wallet_address = wallet_address
                                st.session_state.user_email = login_email
                                st.session_state.user_id = user["id"]
                                st.session_state.show_auth_modal = False

                                # Create persistent session (cookie)
                                SessionManager.login(user["id"], login_email, wallet_address)

                                # If no password hash stored (legacy), update it now
                                if not stored_hash:
                                    new_hash = WalletManager.hash_password(login_password)
                                    update_user_password_hash(user["id"], new_hash)

                                # Restore encrypted wallet from batched data
                                if encrypted_wallet:
                                    st.session_state.wallet_encrypted = encrypted_wallet["encrypted_data"]
                                    st.session_state.wallet_salt = encrypted_wallet["salt"]

                                    # Decrypt with password
                                    if WalletManager.unlock_wallet_with_password(login_password):
                                        st.session_state.wallet_locked = False
                                        st.success("Signed in. Wallet restored.")

                                        # Update session with Solana address from decrypted wallet
                                        wallet_data = WalletManager.get_wallet_from_session()
                                        if wallet_data and wallet_data.get("solana"):
                                            sol_addr = wallet_data["solana"].get("address")
                                            if sol_addr:
                                                st.session_state.solana_address = sol_addr
                                                # Save to wallets table for persistence
                                                save_wallet_address(user["id"], sol_addr, chain="solana")
                                    else:
                                        st.session_state.wallet_locked = True
                                        st.success("Signed in")
                                        st.warning("Could not decrypt wallet. Enter your password to unlock.")
                                else:
                                    # No cloud backup - need manual import (legacy account)
                                    st.session_state.wallet_locked = True
                                    st.success("Signed in")
                                    st.markdown("<div style='font-family: Inter; font-size: 12px; color: #666; margin-top: 8px;'>Import your wallet using your recovery phrase to access your funds.</div>", unsafe_allow_html=True)

                                # Check if onboarding was completed
                                from settings_manager import SettingsManager
                                user_settings = SettingsManager.get_llm_config(user["id"])
                                has_api_key = bool(user_settings.get("api_key"))

                                if not has_api_key:
                                    # Resume onboarding at API setup step
                                    st.session_state.onboarding_step = 2
                                    st.session_state.onboarding_complete = False
                                    st.markdown("<div style='font-family: Inter; font-size: 12px; color: #666; margin-top: 8px;'>Connect an AI provider to start chatting.</div>", unsafe_allow_html=True)

                                st.rerun()
                            else:
                                st.error("No wallet found for this account")

    # ========== TAB 3: IMPORT WALLET ==========
    with tab3:
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <div style="font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 400; color: white; margin-bottom: 8px;">Import Wallet</div>
            <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #555; line-height: 1.6;">Import an existing wallet using your recovery phrase or private key.</div>
        </div>
        """, unsafe_allow_html=True)

        import_email = st.text_input("Email (optional)", key="import_email", placeholder="your@email.com")
        recovery_input = st.text_area(
            "Recovery phrase or private key",
            key="import_recovery",
            placeholder="12-word phrase or 0x...",
            help="Enter your 12-word seed phrase or private key",
            height=100
        )
        import_password = st.text_input("Password", type="password", key="import_pwd", help="This password will encrypt your wallet locally")

        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; font-size: 11px; color: #444; margin-top: 8px;">
            Your wallet is encrypted locally before storage.
        </div>
        """, unsafe_allow_html=True)

        if st.button("Import Wallet", type="primary", disabled=not (recovery_input and import_password)):
            with st.spinner("Importing wallet..."):
                wallet_info = WalletManager.import_wallet(recovery_input.strip())

                if wallet_info:
                    # Save to session
                    WalletManager.save_wallet_to_session(
                        wallet_info["wallet_data"],
                        import_password
                    )

                    st.session_state.wallet_address = wallet_info["address"]
                    st.session_state.wallet_locked = False
                    st.session_state.show_auth_modal = False

                    # Optionally save to Supabase if email provided
                    if import_email and "@" in import_email:
                        user = get_user_by_email(import_email)
                        if not user:
                            user = create_user(import_email, wallet_info["address"])

                        if user:
                            save_wallet_address(user["id"], wallet_info["address"])
                            st.session_state.user_email = import_email
                            st.session_state.user_id = user["id"]

                    st.success("Wallet imported")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid recovery phrase or private key")


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
        try:
            SessionManager.get_cookie_manager()
            restored = SessionManager.restore_session()

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
