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
    # Lazy import LangChain modules (saves 1-2s on app startup)
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
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
            max_tokens=4096
        )
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=llm_config.get("model", "gemini-2.0-flash-exp"),
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
            max_tokens=4096
        )

    # Get cached tools (only created once per session)
    custom_tools = _get_cached_tools()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, custom_tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=custom_tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10
    )

    return executor


# ============================================================================
# UI COMPONENTS
# ============================================================================

def init_state():
    """Initialize session state"""
    defaults = {
        "messages": [],
        "agent": None,
        "wallet_address": None,
        "wallet_locked": True,
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
                                if wallet_info.get("solana_address"):
                                    st.session_state.solana_address = wallet_info["solana_address"]

                                # Create persistent session (cookie)
                                SessionManager.login(user["id"], email, wallet_info["address"])

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

    # V22 Design System: "Cinematic Atmosphere" - Deep Zinc, Spotlight, Glass Inputs
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        /* V22 Atmosphere Palette */
        --bg-deep: #09090b;
        --bg-surface: #18181b;
        --text-primary: #f4f4f5;
        --text-secondary: #a1a1aa;
        --border-glass: rgba(255, 255, 255, 0.08);
        --font-sans: 'Inter', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }

    /* 1. THE ATMOSPHERE BACKGROUND */
    .stApp {
        background-color: var(--bg-deep);
        background-image:
            radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.05) 0%, transparent 60%),
            linear-gradient(180deg, var(--bg-deep) 0%, #000000 100%);
        background-attachment: fixed;
    }

    html, body, [class*="css"] {
        font-family: var(--font-sans);
        color: var(--text-primary);
    }

    /* 2. TYPOGRAPHY */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 500 !important;
        letter-spacing: -0.04em !important;
        color: white !important;
    }

    /* 3. GLASS INPUTS */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stChatInput > div > div > textarea,
    .stNumberInput > div > div > input {
        background-color: rgba(255,255,255,0.03) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: 12px !important;
        color: white !important;
        font-family: 'Inter', sans-serif;
        font-size: 15px !important;
        padding: 12px 16px !important;
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:hover,
    .stTextArea > div > div > textarea:hover,
    .stChatInput > div > div > textarea:hover {
        background-color: rgba(255,255,255,0.05) !important;
        border-color: rgba(255,255,255,0.15) !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stChatInput > div > div > textarea:focus {
        border-color: rgba(255,255,255,0.3) !important;
        box-shadow: 0 0 15px rgba(255,255,255,0.05) !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stChatInput > div > div > textarea::placeholder {
        color: #555 !important;
    }

    /* 4. REFINED BUTTONS */
    .stButton > button {
        background: transparent !important;
        border: 1px solid var(--border-glass) !important;
        color: var(--text-secondary) !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif;
        font-weight: 500 !important;
        font-size: 13px !important;
        padding: 8px 20px !important;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: rgba(255,255,255,0.05) !important;
        color: white !important;
        border-color: rgba(255,255,255,0.2) !important;
        transform: translateY(-1px);
    }

    /* Primary Action Buttons */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"],
    button[kind="primary"] {
        background: white !important;
        color: black !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(255,255,255,0.15);
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        box-shadow: 0 6px 20px rgba(255,255,255,0.25);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span {
        color: black !important;
    }

    .stButton > button:disabled {
        opacity: 0.25 !important;
        transform: none !important;
    }

    /* Form submit buttons */
    [data-testid="stFormSubmitButton"] > button,
    .stFormSubmitButton > button {
        background: white !important;
        color: black !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif;
        font-size: 13px !important;
        padding: 8px 20px !important;
        box-shadow: 0 4px 12px rgba(255,255,255,0.15);
    }

    [data-testid="stFormSubmitButton"] > button:hover,
    .stFormSubmitButton > button:hover {
        box-shadow: 0 6px 20px rgba(255,255,255,0.25);
        transform: translateY(-1px);
    }

    [data-testid="stFormSubmitButton"] > button p,
    [data-testid="stFormSubmitButton"] > button span,
    .stFormSubmitButton > button p,
    .stFormSubmitButton > button span {
        color: black !important;
    }

    /* 5. SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid var(--border-glass);
    }

    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
    }

    /* Remove yellow/orange focus outlines */
    [data-testid="stSidebar"] input:focus,
    [data-testid="stSidebar"] button:focus,
    [data-testid="stForm"] input:focus,
    [data-testid="stForm"] button:focus,
    input:focus, button:focus, textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }

    /* Remove Streamlit's default focus ring */
    *:focus {
        outline: none !important;
    }

    [data-baseweb="input"]:focus-within {
        border-color: rgba(255,255,255,0.3) !important;
        box-shadow: none !important;
    }

    /* 6. CHAT BUBBLES */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 12px 0 !important;
        border: none !important;
    }

    [data-testid="stChatMessage"] [data-testid="stImage"] {
        display: none;
    }

    /* 7. TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border: none !important;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 8px;
        border: none !important;
        background: transparent;
        color: #666;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 500;
        padding: 0 16px;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #999;
        background: rgba(255,255,255,0.03);
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(255,255,255,0.1);
        color: white;
    }

    /* 8. LAYOUT - Comfortable Width for Cards + Chat */
    .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* Match chat input width to content area */
    [data-testid="stChatInput"] {
        max-width: 1100px;
        margin: 0 auto;
        padding-left: 1rem;
        padding-right: 1rem;
        box-sizing: border-box;
    }

    /* Ensure chat input inner box fills properly */
    [data-testid="stChatInput"] > div {
        max-width: 100%;
    }

    /* 8. CODE BLOCKS - V12 Minimal */
    code {
        background: transparent !important;
        color: #888 !important;
        padding: 0 !important;
        border-radius: 0 !important;
        font-size: 11px !important;
        font-family: var(--font-mono) !important;
        border: none !important;
    }

    pre {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid var(--border-hairline) !important;
        border-radius: 0 !important;
        padding: 12px 0 !important;
        margin: 0 !important;
    }

    /* st.code widget - minimal with inline copy button */
    [data-testid="stCode"] {
        background: transparent !important;
    }

    [data-testid="stCode"] > div {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid var(--border-hairline) !important;
        border-radius: 0 !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }

    [data-testid="stCode"] pre {
        background: transparent !important;
        border: none !important;
        padding: 12px 0 !important;
        margin: 0 !important;
        flex: 1 !important;
        min-width: 0 !important;
    }

    [data-testid="stCode"] code {
        background: transparent !important;
        color: #888 !important;
        font-size: 11px !important;
        word-break: break-all !important;
        white-space: pre-wrap !important;
    }

    /* Copy button - inline at end */
    [data-testid="stCode"] button {
        flex-shrink: 0 !important;
        background: transparent !important;
        border: none !important;
        color: #444 !important;
        opacity: 0.4;
        transition: opacity 0.2s ease;
        padding: 8px !important;
        margin: 0 !important;
    }

    [data-testid="stCode"] button:hover {
        opacity: 1;
        color: white !important;
        background: transparent !important;
    }

    /* 9. DIVIDERS & MISC */
    hr {
        border-color: var(--border-hairline) !important;
        margin: 2rem 0 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 10. EXPANDERS */
    .streamlit-expanderHeader {
        font-family: var(--font-mono) !important;
        font-size: 10px !important;
        color: #666 !important;
        background: transparent !important;
        border: none !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    details {
        background: transparent !important;
        border: 1px solid var(--border-hairline) !important;
        border-radius: 0 !important;
    }

    details:hover {
        border-color: rgba(255,255,255,0.15) !important;
    }

    /* 11. ALERTS */
    .stAlert {
        border-radius: 0 !important;
        border: 1px solid var(--border-hairline) !important;
        background: rgba(255,255,255,0.02) !important;
    }

    /* 12. SELECT/NUMBER INPUTS */
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid #333 !important;
        border-radius: 0 !important;
        color: var(--text-primary) !important;
        font-family: var(--font-mono) !important;
    }

    .stSelectbox > div > div:hover,
    .stNumberInput > div > div > input:hover {
        border-bottom-color: #666 !important;
    }

    /* 13. CAPTIONS */
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: #555 !important;
        font-size: 11px !important;
        font-family: var(--font-mono) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* 14. LINK BUTTONS */
    .stLinkButton > a {
        border-radius: 20px !important;
        font-weight: 500 !important;
        border: 1px solid var(--border-hairline) !important;
        background: transparent !important;
        color: #888 !important;
        font-size: 10px !important;
        font-family: var(--font-mono) !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .stLinkButton > a:hover {
        background-color: rgba(255,255,255,0.05) !important;
        color: white !important;
        border-color: white !important;
    }

    /* 15. SCROLLBAR */
    ::-webkit-scrollbar {
        width: 3px;
        height: 3px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.1);
        border-radius: 0;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.2);
    }

    /* 16. METRIC CARDS */
    [data-testid="stMetric"] {
        background: transparent;
        border: none;
        padding: 0;
    }

    [data-testid="stMetricValue"] {
        font-family: var(--font-sans) !important;
        font-weight: 300;
        color: var(--text-primary) !important;
    }

    [data-testid="stMetricLabel"] {
        font-family: var(--font-mono) !important;
        font-size: 9px !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #555 !important;
    }

    /* 17. REMOVE DEFAULT PADDING */
    .block-container {
        padding-top: 2rem;
    }

    /* 18. CHECKBOX & RADIO - VOID */
    .stCheckbox label span,
    .stRadio label span {
        color: #888 !important;
        font-size: 13px !important;
        font-family: var(--font-sans) !important;
    }

    .stCheckbox [data-testid="stCheckbox"],
    .stRadio [data-testid="stRadio"] {
        background: transparent !important;
    }

    /* 19. TOAST - MINIMAL */
    [data-testid="stToast"] {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid var(--border-hairline) !important;
        border-radius: 0 !important;
        color: #888 !important;
        font-family: var(--font-mono) !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* 20. SPINNER - SUBTLE */
    .stSpinner > div {
        border-color: rgba(255,255,255,0.1) rgba(255,255,255,0.1) rgba(255,255,255,0.1) white !important;
    }

    /* 21. NUMBER INPUT LABEL HIDE */
    .stNumberInput > label {
        font-family: var(--font-mono) !important;
        font-size: 10px !important;
        color: #555 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* 22. ALERT ICON MINIMAL */
    .stAlert [data-testid="stIcon"] {
        display: none;
    }

    .stAlert [data-testid="stMarkdownContainer"] p {
        color: #888 !important;
        font-family: var(--font-sans) !important;
        font-size: 13px !important;
    }

    /* ========================================
       MOBILE OPTIMIZATION: < 768px
       ======================================== */
    @media (max-width: 768px) {
        /* 1. BUTTONS - 48px touch target minimum */
        .stButton > button {
            padding: 14px 20px !important;
            font-size: 12px !important;
            min-height: 48px !important;
        }

        .stButton > button[kind="primary"]:hover {
            transform: none !important; /* No scale on touch */
        }

        /* 2. INPUTS - 48px height, 16px font prevents iOS zoom */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stNumberInput > div > div > input {
            font-size: 16px !important;
            padding: 14px 0 !important;
            min-height: 48px !important;
        }

        .stChatInput > div > div > textarea {
            font-size: 16px !important;
            min-height: 48px !important;
        }

        /* 3. TABS - Better touch targets */
        .stTabs [data-baseweb="tab-list"] {
            gap: 16px !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 12px !important;
            padding: 12px 8px !important;
        }

        /* 4. CHAT - Reduce excess spacing */
        [data-testid="stChatMessage"] {
            padding: 0.75rem 0 !important;
        }

        /* 5. CODE BLOCKS - Readable on small screens */
        code, [data-testid="stCode"] code {
            font-size: 12px !important;
        }

        /* 6. EXPANDERS - Better headers */
        .streamlit-expanderHeader {
            font-size: 11px !important;
            padding: 12px 0 !important;
        }

        /* 7. SELECT/RADIO - Larger targets */
        .stSelectbox > div > div {
            font-size: 14px !important;
            min-height: 48px !important;
        }

        .stCheckbox label span,
        .stRadio label span {
            font-size: 14px !important;
        }

        /* 8. SPACING - Reduce excessive margins */
        .block-container {
            padding: 1rem 1rem !important;
        }

        /* 9. ALERTS - Readable on narrow screens */
        .stAlert [data-testid="stMarkdownContainer"] p {
            font-size: 13px !important;
        }

        /* 10. HEADERS - Scale down */
        h1 { font-size: 22px !important; }
        h2 { font-size: 18px !important; }
        h3 { font-size: 16px !important; }

        /* 11. SIDEBAR - Proper drawer behavior on mobile */
        [data-testid="stSidebar"] {
            min-width: 85vw !important;
            max-width: 85vw !important;
            width: 85vw !important;
        }

        [data-testid="stSidebar"] > div {
            padding: 1rem !important;
        }

        /* Ensure sidebar collapse button is visible and touchable */
        [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {
            min-width: 48px !important;
            min-height: 48px !important;
            z-index: 999999 !important;
        }

        /* Fix sidebar overlay - ensure it doesn't block main content when collapsed */
        [data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(-100%) !important;
            pointer-events: none !important;
        }

        /* Main content should be fully accessible */
        [data-testid="stAppViewBlockContainer"],
        .main .block-container {
            pointer-events: auto !important;
        }
    }

    /* EXTRA SMALL SCREENS: < 480px (iPhone SE, older phones) */
    @media (max-width: 480px) {
        h1 { font-size: 20px !important; }

        .stButton > button {
            padding: 12px 16px !important;
            font-size: 11px !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 11px !important;
            padding: 10px 6px !important;
        }

        code, [data-testid="stCode"] code {
            font-size: 11px !important;
        }

        .block-container {
            padding: 0.75rem 0.75rem !important;
        }
    }
    </style>
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
