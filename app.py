"""
Chat02 - Your money, your words
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


def get_deposit_address(chain: str = "base-sepolia") -> str:
    """Get deposit address for a specific chain. Args: chain - network key like 'base-sepolia' or 'arbitrum-sepolia'"""
    if "wallet_address" not in st.session_state:
        return json.dumps({"error": "No wallet connected"})

    address = st.session_state.wallet_address
    network = NETWORKS.get(chain, NETWORKS["base-sepolia"])

    return json.dumps({
        "chain": network["name"],
        "address": address,
        "explorer": ChainUtils.get_explorer_url(chain, address),
        "usdc_address": network.get("usdc_address"),
        "note": "Send USDC or native tokens to this address"
    }, indent=2)


# Old mock tools removed - now using real Bitrefill API tools from bitrefill_tools.py


def preview_transaction(to_address: str, amount_usd: float, chain: str = "base-sepolia") -> str:
    """
    Preview a transaction before execution. Shows exact amounts, fees, and timing.
    Args: to_address, amount_usd, chain (network key)
    """
    if "wallet_address" not in st.session_state:
        return json.dumps({"error": "No wallet connected"})

    network = NETWORKS.get(chain, NETWORKS["base-sepolia"])
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

    # Check if using OAuth (no API key needed) or API key
    provider = llm_config.get("provider", "anthropic")
    has_api_key = bool(llm_config.get("api_key"))
    has_oauth = llm_config.get("using_oauth", False)

    if not has_api_key and not has_oauth:
        return None  # Banner will handle this

    # Create LLM based on provider
    if provider == "google_oauth":
        # Google OAuth - user signed in with Google, uses their free Gemini quota
        import google.generativeai as genai
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Configure genai with OAuth credentials
        credentials = llm_config.get("credentials")
        if credentials:
            genai.configure(credentials=credentials)

        # Create LLM (will use the configured credentials)
        llm = ChatGoogleGenerativeAI(
            model=llm_config.get("model", "gemini-2.0-flash"),
            temperature=0.3,
            max_output_tokens=4096
        )
    elif provider == "openrouter":
        # OpenRouter - OpenAI-compatible API with many free models
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=llm_config.get("model", "deepseek/deepseek-r1t2-chimera:free"),
            api_key=llm_config.get("api_key"),
            base_url=llm_config.get("base_url", "https://openrouter.ai/api/v1"),
            temperature=0.3,
            max_tokens=4096,
            default_headers={
                "HTTP-Referer": "https://chatwallet.app",
                "X-Title": "Chat Wallet"
            }
        )
    elif provider == "openai":
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
    """Show wallet setup screen with email/password account"""
    st.title("Chat Wallet")
    st.caption("Self-custodial wallet with AI-powered transactions")

    st.info("Your wallet is encrypted locally and backed up to the cloud. Only you control the private keys.")

    tab1, tab2, tab3 = st.tabs(["Create Account", "Sign In", "Import Wallet"])

    # ========== TAB 1: SIGN UP ==========
    with tab1:
        st.markdown("#### Create Account")
        st.caption("Create a new wallet that syncs across all your devices.")

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

                                # Defer wallet key save to next render cycle (to let JS execute)
                                st.session_state._pending_wallet_key_save = encrypted["key"]

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

        st.caption("Your wallet syncs across all your devices automatically.")

    # ========== TAB 2: LOG IN ==========
    with tab2:
        st.markdown("#### Sign In")
        st.caption("Access your existing wallet.")

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
                                    st.info("Import your wallet using your recovery phrase to access your funds.")

                                # Check if onboarding was completed
                                from settings_manager import SettingsManager
                                user_settings = SettingsManager.get_llm_config(user["id"])
                                has_api_key = bool(user_settings.get("api_key"))

                                if not has_api_key:
                                    # Resume onboarding at API setup step
                                    st.session_state.onboarding_step = 2
                                    st.session_state.onboarding_complete = False
                                    st.info("Connect an AI provider to start chatting.")

                                st.rerun()
                            else:
                                st.error("No wallet found for this account")

    # ========== TAB 3: IMPORT WALLET ==========
    with tab3:
        st.markdown("#### Import Wallet")
        st.caption("Import an existing wallet using your recovery phrase or private key.")

        import_email = st.text_input("Email (optional)", key="import_email", placeholder="your@email.com")
        recovery_input = st.text_area(
            "Recovery phrase or private key",
            key="import_recovery",
            placeholder="12-word phrase or 0x...",
            help="Enter your 12-word seed phrase or private key",
            height=100
        )
        import_password = st.text_input("Password", type="password", key="import_pwd", help="This password will encrypt your wallet locally")

        st.caption("Your wallet is encrypted locally before storage.")

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
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Chat02 Design System - Professional dark theme with texture and depth
    st.markdown("""
    <style>
    /* ═══════════════════════════════════════════════════════════════════════════
       2026 CYBER-PHYSICAL DESIGN SYSTEM
       "Opinionated Luxury" - Heavy, Tactile, Precision Instrument Aesthetic
       ═══════════════════════════════════════════════════════════════════════════ */

    /* ─────────────────────────────────────────────────────────────────────────
       TYPOGRAPHY: Premium Geometric Sans + Monospace for Data
       ───────────────────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        /* Deep Void Palette - No flat blacks */
        --void-deep: #020408;
        --void-elevated: #0A0D14;
        --void-surface: #0F1318;
        --void-card: #141920;
        --void-hover: #1A2028;

        /* Electric Accents - High contrast, used sparingly */
        --accent-cyan: #00D4FF;
        --accent-cyan-dim: rgba(0, 212, 255, 0.15);
        --accent-cyan-glow: rgba(0, 212, 255, 0.4);
        --accent-emerald: #00FF9D;
        --accent-emerald-dim: rgba(0, 255, 157, 0.15);
        --accent-amber: #FFB800;
        --accent-rose: #FF3D71;

        /* Text Hierarchy */
        --text-primary: #F0F4F8;
        --text-secondary: #94A3B8;
        --text-tertiary: #64748B;
        --text-muted: #475569;

        /* Borders - Ultra thin, low opacity */
        --border-subtle: rgba(255, 255, 255, 0.04);
        --border-dim: rgba(255, 255, 255, 0.06);
        --border-visible: rgba(255, 255, 255, 0.08);
        --border-accent: rgba(0, 212, 255, 0.3);

        /* Glassmorphism */
        --glass-bg: rgba(10, 13, 20, 0.8);
        --glass-border: rgba(255, 255, 255, 0.05);
    }

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
        font-feature-settings: 'ss01' on, 'ss02' on;
        -webkit-font-smoothing: antialiased;
    }

    /* Main app background with noise texture */
    .stApp {
        background: var(--void-deep) !important;
    }

    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        /* Noise texture simulation */
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        opacity: 0.015;
    }

    /* Northern Lights ambient glow */
    .stApp::after {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        pointer-events: none;
        z-index: 0;
        background:
            radial-gradient(ellipse at 20% 20%, rgba(0, 212, 255, 0.04) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(0, 255, 157, 0.03) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(139, 92, 246, 0.02) 0%, transparent 60%);
        animation: aurora 30s ease-in-out infinite;
    }

    @keyframes aurora {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(-2%, 1%) rotate(1deg); }
        66% { transform: translate(1%, -1%) rotate(-1deg); }
    }

    /* ─────────────────────────────────────────────────────────────────────────
       TYPOGRAPHY HIERARCHY
       ───────────────────────────────────────────────────────────────────────── */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.03em !important;
        color: var(--text-primary) !important;
        font-size: 1.75rem !important;
    }

    h2 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: var(--text-primary) !important;
        font-size: 1.25rem !important;
    }

    h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: -0.01em !important;
        color: var(--text-secondary) !important;
        font-size: 1rem !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       METRIC CARDS - HUD Style with Glassmorphism
       ───────────────────────────────────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--void-card) 0%, var(--void-surface) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-dim);
        border-radius: 12px;
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        box-shadow:
            0 4px 24px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }

    /* Accent glow line at top */
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 20px;
        right: 20px;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
        opacity: 0.5;
    }

    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        font-size: 2rem !important;
        color: var(--text-primary) !important;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
    }

    [data-testid="stMetricLabel"] {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--text-tertiary) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 500;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       BUTTONS - Heavy, Tactile Feel
       ───────────────────────────────────────────────────────────────────────── */
    .stButton > button {
        font-family: 'Space Grotesk', sans-serif !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid var(--border-visible) !important;
        background: linear-gradient(180deg, var(--void-card) 0%, var(--void-surface) 100%) !important;
        color: var(--text-secondary) !important;
        box-shadow:
            0 2px 8px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.04),
            inset 0 -1px 0 rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 50%);
        pointer-events: none;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        border-color: var(--border-accent) !important;
        background: linear-gradient(180deg, var(--void-hover) 0%, var(--void-card) 100%) !important;
        color: var(--text-primary) !important;
        box-shadow:
            0 8px 24px rgba(0, 0, 0, 0.4),
            0 0 20px var(--accent-cyan-dim),
            inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }

    /* Primary buttons - Electric accent */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"],
    button[kind="primary"] {
        background: linear-gradient(180deg, var(--accent-cyan) 0%, #00B8E0 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #020408 !important;
        font-weight: 600 !important;
        box-shadow:
            0 4px 16px var(--accent-cyan-glow),
            inset 0 1px 0 rgba(255, 255, 255, 0.2),
            inset 0 -1px 0 rgba(0, 0, 0, 0.1);
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {
        background: linear-gradient(180deg, #33DFFF 0%, var(--accent-cyan) 100%) !important;
        box-shadow:
            0 8px 32px var(--accent-cyan-glow),
            0 0 40px var(--accent-cyan-dim),
            inset 0 1px 0 rgba(255, 255, 255, 0.25);
        transform: translateY(-2px);
    }

    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span,
    .stButton > button[data-testid="baseButton-primary"] p,
    .stButton > button[data-testid="baseButton-primary"] span {
        color: #020408 !important;
        font-weight: 600 !important;
    }

    .stButton > button:disabled {
        opacity: 0.3 !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       SIDEBAR - Glassmorphic Panel
       ───────────────────────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--void-elevated) 0%, var(--void-deep) 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }

    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background:
            radial-gradient(ellipse at 50% 0%, rgba(0, 212, 255, 0.03) 0%, transparent 50%);
        pointer-events: none;
    }

    [data-testid="stSidebar"] h1 {
        font-size: 1.125rem !important;
        margin-bottom: 1.5rem;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       INPUT FIELDS - Precision Instrument Style
       ───────────────────────────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-dim) !important;
        background: var(--void-surface) !important;
        padding: 14px 16px !important;
        font-size: 0.875rem !important;
        color: var(--text-primary) !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        transition: all 0.15s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow:
            0 0 0 3px var(--accent-cyan-dim),
            inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        outline: none;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-muted) !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       TABS - Capsule Navigation
       ───────────────────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--void-surface);
        border-radius: 10px;
        padding: 4px;
        border: 1px solid var(--border-subtle);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
        font-size: 0.8125rem;
        background: transparent;
        color: var(--text-tertiary);
        transition: all 0.15s ease;
        border: none;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-secondary);
        background: rgba(255, 255, 255, 0.02);
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: var(--void-card);
        color: var(--text-primary);
        box-shadow:
            0 2px 8px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       CHAT MESSAGES - Bento Card Style
       ───────────────────────────────────────────────────────────────────────── */
    [data-testid="stChatMessage"] {
        background: linear-gradient(135deg, var(--void-card) 0%, var(--void-surface) 100%);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        position: relative;
    }

    [data-testid="stChatMessage"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-visible), transparent);
    }

    /* Chat input - Terminal style */
    [data-testid="stChatInput"] textarea {
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 12px !important;
        background: var(--void-surface) !important;
        border: 1px solid var(--border-dim) !important;
        padding: 16px 20px !important;
        font-size: 0.875rem !important;
        box-shadow:
            inset 0 2px 4px rgba(0, 0, 0, 0.3),
            0 0 0 1px var(--border-subtle);
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow:
            0 0 0 3px var(--accent-cyan-dim),
            inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       CODE BLOCKS - Data Terminal Aesthetic
       ───────────────────────────────────────────────────────────────────────── */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        background: var(--void-surface) !important;
        color: var(--accent-cyan) !important;
        padding: 4px 10px !important;
        border-radius: 6px !important;
        font-size: 0.8125rem !important;
        border: 1px solid var(--border-dim);
        font-variant-numeric: tabular-nums;
    }

    pre {
        background: var(--void-surface) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       ALERTS - HUD Status Display
       ───────────────────────────────────────────────────────────────────────── */
    .stAlert {
        border-radius: 8px !important;
        border: 1px solid var(--border-dim) !important;
        background: linear-gradient(135deg, var(--void-card) 0%, var(--void-surface) 100%) !important;
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }

    .stAlert::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: var(--accent-cyan);
    }

    /* Info alerts */
    .stAlert[data-baseweb="notification"] {
        border-left: 3px solid var(--accent-cyan) !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       DIVIDERS
       ───────────────────────────────────────────────────────────────────────── */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, var(--border-dim), transparent) !important;
        margin: 2rem 0 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ─────────────────────────────────────────────────────────────────────────
       EXPANDERS - Collapsible Modules
       ───────────────────────────────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        color: var(--text-secondary) !important;
        background: linear-gradient(135deg, var(--void-card) 0%, var(--void-surface) 100%);
        border-radius: 8px;
        padding: 14px 18px !important;
        transition: all 0.15s ease;
    }

    .streamlit-expanderHeader:hover {
        background: var(--void-hover);
        color: var(--text-primary) !important;
    }

    details {
        background: transparent !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: 10px !important;
    }

    details[open] {
        border-color: var(--border-visible) !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       HUD STATUS INDICATORS
       ───────────────────────────────────────────────────────────────────────── */
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        position: relative;
    }

    .status-dot.connected {
        background: var(--accent-emerald);
        box-shadow: 0 0 12px var(--accent-emerald);
        animation: pulse-glow 2s ease-in-out infinite;
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 8px var(--accent-emerald); }
        50% { box-shadow: 0 0 16px var(--accent-emerald), 0 0 24px var(--accent-emerald-dim); }
    }

    .status-dot.disconnected {
        background: var(--text-muted);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       BENTO GRID CARDS
       ───────────────────────────────────────────────────────────────────────── */
    .section-card {
        background: linear-gradient(135deg, var(--void-card) 0%, var(--void-surface) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-dim);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 12px;
        position: relative;
        overflow: hidden;
        transition: all 0.2s ease;
    }

    .section-card:hover {
        border-color: var(--border-visible);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    .section-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       QUICK ACTION CAPSULES
       ───────────────────────────────────────────────────────────────────────── */
    .quick-action {
        font-family: 'Space Grotesk', sans-serif;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 18px;
        background: linear-gradient(180deg, var(--void-card) 0%, var(--void-surface) 100%);
        border: 1px solid var(--border-dim);
        border-radius: 100px;
        color: var(--text-secondary);
        font-size: 0.8125rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s ease;
        margin: 4px;
    }

    .quick-action:hover {
        background: var(--void-hover);
        border-color: var(--border-accent);
        color: var(--text-primary);
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 20px var(--accent-cyan-dim);
    }

    .quick-action.active {
        background: linear-gradient(180deg, var(--accent-cyan) 0%, #00B8E0 100%);
        border-color: transparent;
        color: #020408;
        box-shadow: 0 4px 16px var(--accent-cyan-glow);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       NUMBER & SELECT INPUTS
       ───────────────────────────────────────────────────────────────────────── */
    .stNumberInput > div > div > input {
        font-family: 'JetBrains Mono', monospace !important;
        font-variant-numeric: tabular-nums;
        border-radius: 8px !important;
        border: 1px solid var(--border-dim) !important;
        background: var(--void-surface) !important;
        color: var(--text-primary) !important;
    }

    .stSelectbox > div > div {
        background: var(--void-surface) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: 8px !important;
    }

    .stSelectbox > div > div:hover {
        border-color: var(--border-visible) !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       CAPTIONS & LABELS
       ───────────────────────────────────────────────────────────────────────── */
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        line-height: 1.6;
        letter-spacing: 0.01em;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       SIDEBAR LINKS
       ───────────────────────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] a {
        color: var(--text-muted) !important;
        text-decoration: none;
        transition: color 0.15s ease;
    }

    [data-testid="stSidebar"] a:hover {
        color: var(--accent-cyan) !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       PILL BUTTONS
       ───────────────────────────────────────────────────────────────────────── */
    [data-testid="stHorizontalBlock"] .stButton > button {
        border-radius: 100px !important;
        font-size: 0.75rem !important;
        padding: 0.5rem 1rem !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       LINK BUTTONS
       ───────────────────────────────────────────────────────────────────────── */
    .stLinkButton > a {
        font-family: 'Space Grotesk', sans-serif !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.8125rem !important;
        padding: 12px 20px !important;
        min-height: 42px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 1px solid var(--border-dim) !important;
        background: linear-gradient(180deg, var(--void-card) 0%, var(--void-surface) 100%) !important;
        color: var(--text-secondary) !important;
        text-decoration: none !important;
        transition: all 0.15s ease !important;
    }

    .stLinkButton > a:hover {
        background: var(--void-hover) !important;
        border-color: var(--border-accent) !important;
        color: var(--text-primary) !important;
        text-decoration: none !important;
        box-shadow: 0 0 20px var(--accent-cyan-dim);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       MODALS - Floating Modules
       ───────────────────────────────────────────────────────────────────────── */
    [data-testid="stModal"] > div {
        background: linear-gradient(135deg, var(--void-card) 0%, var(--void-elevated) 100%) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: 16px !important;
        box-shadow:
            0 24px 80px rgba(0, 0, 0, 0.5),
            0 0 1px rgba(255, 255, 255, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       PROGRESS BARS - System Diagnostic Style
       ───────────────────────────────────────────────────────────────────────── */
    .stProgress > div > div {
        background: var(--void-surface) !important;
        border-radius: 4px;
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald)) !important;
        border-radius: 4px;
        box-shadow: 0 0 12px var(--accent-cyan-glow);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       CHECKBOXES & TOGGLES
       ───────────────────────────────────────────────────────────────────────── */
    .stCheckbox > label > div[data-testid="stCheckbox"] > div {
        border-color: var(--border-visible) !important;
        background: var(--void-surface) !important;
    }

    .stCheckbox > label > div[data-testid="stCheckbox"] > div[aria-checked="true"] {
        background: var(--accent-cyan) !important;
        border-color: var(--accent-cyan) !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       RADIO BUTTONS
       ───────────────────────────────────────────────────────────────────────── */
    .stRadio > div {
        gap: 8px;
    }

    .stRadio > div > label {
        background: var(--void-surface);
        border: 1px solid var(--border-dim);
        border-radius: 8px;
        padding: 12px 16px;
        transition: all 0.15s ease;
    }

    .stRadio > div > label:hover {
        border-color: var(--border-visible);
        background: var(--void-card);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       TOOLTIPS
       ───────────────────────────────────────────────────────────────────────── */
    [data-baseweb="tooltip"] {
        background: var(--void-card) !important;
        border: 1px solid var(--border-dim) !important;
        border-radius: 8px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       SCROLLBAR - Minimal
       ───────────────────────────────────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-visible);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }

    /* ─────────────────────────────────────────────────────────────────────────
       DATA DISPLAY UTILITIES
       ───────────────────────────────────────────────────────────────────────── */
    .mono-data {
        font-family: 'JetBrains Mono', monospace !important;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
    }

    .data-label {
        font-size: 0.6875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-muted);
        font-weight: 500;
    }

    .data-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.125rem;
        color: var(--text-primary);
        font-variant-numeric: tabular-nums;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       ACCENT GLOW UTILITIES
       ───────────────────────────────────────────────────────────────────────── */
    .glow-cyan {
        box-shadow: 0 0 20px var(--accent-cyan-dim), 0 0 40px var(--accent-cyan-dim);
    }

    .glow-emerald {
        box-shadow: 0 0 20px var(--accent-emerald-dim), 0 0 40px var(--accent-emerald-dim);
    }

    .border-glow {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 20px var(--accent-cyan-dim);
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

    # Handle deferred wallet key save (from previous unlock)
    # This needs to happen on a separate render cycle so the JS component can execute
    if st.session_state.get("_pending_wallet_key_save"):
        wallet_key = st.session_state._pending_wallet_key_save
        del st.session_state._pending_wallet_key_save
        SessionManager.save_wallet_key(wallet_key)

    # Check session timeout and lock wallet if inactive
    from rate_limiter import check_and_handle_timeout, RateLimiter
    if not check_and_handle_timeout():
        st.toast("Session timed out. Wallet locked for security.")

    # Update activity timestamp on each interaction
    RateLimiter.update_activity()

    # Handle OAuth callback (simplified - no blocking sleep)
    query_params = st.query_params
    if "code" in query_params and "state" in query_params:
        code = query_params["code"]
        state = query_params["state"]

        app_url = os.getenv("APP_URL", "http://localhost:8501")
        redirect_uri = f"{app_url}/oauth/callback"

        # Determine OAuth type from state prefix
        if state.startswith("gemini:"):
            # Gemini OAuth - user signing in with Google for AI
            from gemini_oauth import GeminiOAuth
            user_id = state.replace("gemini:", "")
            success = GeminiOAuth.handle_oauth_callback(code, redirect_uri, user_id)

            # Clear params and invalidate LLM config cache to pick up new OAuth
            st.query_params.clear()
            cache_key = f"_llm_config_{user_id}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.session_state.agent = None  # Force agent recreation
            st.session_state._oauth_result = "gemini_success" if success else "gemini_error"
        else:
            # Gmail OAuth
            from gmail_oauth import GmailOAuth
            user_id = state
            success = GmailOAuth.handle_oauth_callback(code, redirect_uri, user_id)

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
