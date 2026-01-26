"""
Chat02 - Financial Operating System
V10 "Brutalist Fintech" - AI-powered wallet
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

    # Calculate gas cost and app fee using relayer estimation
    try:
        from transaction_relayer import TransactionRelayer
        relayer = TransactionRelayer(chain)
        gas_cost, app_fee = relayer.estimate_gas_cost(amount_usd)
    except Exception:
        # Fallback to simple fee calculation if relayer unavailable
        gas_cost = 0.02  # Default gas estimate
        app_fee = calculate_fee(amount_usd)

    total = amount_usd + gas_cost + app_fee

    preview = {
        "action": "Send USDC",
        "amount": f"${amount_usd:.2f}",
        "to": ChainUtils.format_address(to_address),
        "to_full_address": to_address,
        "network": network["name"],
        "gas_fee": f"${gas_cost:.3f} (covered)",
        "service_fee": f"${app_fee:.3f}",
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
    """Show V10 wallet setup screen - Access Portal"""
    # V10 Brutalist header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem; margin-top: 2rem;">
        <div style="font-family: 'Inter', sans-serif; font-size: 48px; letter-spacing: 0.2em; margin-bottom: 12px;">
            <span style="font-weight: 300;">CHAT</span><span style="font-weight: 800;">02</span>
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #525252;
                    letter-spacing: 0.2em;">FINANCIAL_OPERATING_SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)

    # Info card - V10 brutalist style
    st.markdown("""
    <div style="
        border: 1px solid #1a1a1a;
        padding: 16px 20px;
        margin-bottom: 2rem;
        position: relative;
    ">
        <div style="position: absolute; top: 0; left: 0; width: 6px; height: 6px; border-top: 1px solid #3b82f6; border-left: 1px solid #3b82f6;"></div>
        <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #a3a3a3;">
            Self-custodial. Encrypted locally. Only you control access.
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["ACCESS", "CREATE", "RECOVER"])

    # ========== TAB 1: LOG IN (ACCESS) ==========
    with tab1:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 1rem;">EXISTING_USER</div>
        """, unsafe_allow_html=True)

        # Use form to prevent sidebar closing and enable password autofill
        with st.form(key="login_form_v10", clear_on_submit=False):
            st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                        letter-spacing: 0.1em; margin-bottom: 4px;">IDENTITY</div>""", unsafe_allow_html=True)
            login_email = st.text_input(
                "Email",
                key="login_email_v10",
                placeholder="user@domain.com",
                autocomplete="username",
                label_visibility="collapsed"
            )

            st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                        letter-spacing: 0.1em; margin-bottom: 4px; margin-top: 12px;">KEY</div>""", unsafe_allow_html=True)
            login_password = st.text_input(
                "Password",
                type="password",
                key="login_pwd_v10",
                placeholder="ACCESS KEY_",
                autocomplete="current-password",
                label_visibility="collapsed"
            )

            submit_login = st.form_submit_button("ENTER SYSTEM", type="primary", use_container_width=True)

        if submit_login:
            if not login_email or not login_password:
                st.error("REQUIRED: IDENTITY AND KEY")
            else:
                with st.spinner("AUTHENTICATING_"):
                    # Check rate limiting before any DB queries
                    from rate_limiter import RateLimiter

                    allowed, lockout_msg = RateLimiter.check_login_allowed(login_email)
                    if not allowed:
                        st.error(lockout_msg)
                    else:
                        # OPTIMIZED: Fetch all user data in 2 queries instead of 5
                        login_data = get_user_login_data(login_email)

                        if not login_data:
                            st.error("NO_IDENTITY_FOUND")
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
                                    st.error(f"INVALID_KEY. {remaining} attempt(s) remaining.")
                                else:
                                    st.error("INVALID_KEY. System locked.")
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
                                        st.success("ACCESS GRANTED")
                                    else:
                                        st.session_state.wallet_locked = True
                                        st.success("AUTHENTICATED")
                                        st.warning("WALLET_LOCKED: Enter key to decrypt")
                                else:
                                    # No cloud backup - need manual import (legacy account)
                                    st.session_state.wallet_locked = True
                                    st.success("AUTHENTICATED")
                                    st.info("IMPORT_REQUIRED: Use recovery phrase")

                                # Check if onboarding was completed
                                from settings_manager import SettingsManager
                                user_settings = SettingsManager.get_llm_config(user["id"])
                                has_api_key = bool(user_settings.get("api_key"))

                                if not has_api_key:
                                    # Resume onboarding at API setup step
                                    st.session_state.onboarding_step = 2
                                    st.session_state.onboarding_complete = False
                                    st.info("CONNECT AI ENGINE TO CONTINUE")

                                st.rerun()
                            else:
                                st.error("NO_WALLET_FOUND")

    # ========== TAB 2: SIGN UP (CREATE) ==========
    with tab2:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 1rem;">NEW_USER</div>
        """, unsafe_allow_html=True)

        # Use form to prevent sidebar closing and enable password autofill
        with st.form(key="signup_form", clear_on_submit=False):
            st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                        letter-spacing: 0.1em; margin-bottom: 4px;">NEW_IDENTITY</div>""", unsafe_allow_html=True)
            email = st.text_input(
                "Email",
                key="signup_email",
                placeholder="user@domain.com",
                autocomplete="username",
                label_visibility="collapsed"
            )

            st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                        letter-spacing: 0.1em; margin-bottom: 4px; margin-top: 12px;">CREATE_KEY</div>""", unsafe_allow_html=True)
            password = st.text_input(
                "Password (min 8 characters)",
                type="password",
                key="signup_pwd",
                placeholder="MIN 8 CHARACTERS_",
                autocomplete="new-password",
                label_visibility="collapsed"
            )

            st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                        letter-spacing: 0.1em; margin-bottom: 4px; margin-top: 12px;">CONFIRM_KEY</div>""", unsafe_allow_html=True)
            password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                key="signup_pwd_confirm",
                placeholder="VERIFY KEY_",
                autocomplete="new-password",
                label_visibility="collapsed"
            )

            submit_signup = st.form_submit_button("GENERATE ID", type="primary", use_container_width=True)

        if submit_signup:
            if not email or not password:
                st.error("REQUIRED: IDENTITY AND KEY")
            elif password != password_confirm:
                st.error("KEY_MISMATCH")
            elif len(password) < 8:
                st.error("KEY_TOO_SHORT: MIN 8 CHARACTERS")
            elif "@" not in email:
                st.error("INVALID_IDENTITY_FORMAT")
            else:
                with st.spinner("GENERATING_WALLET_"):
                    # Check if user exists
                    existing_user = get_user_by_email(email)
                    if existing_user:
                        st.error("IDENTITY_EXISTS: Use ACCESS tab")
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

                                st.success("WALLET_GENERATED")

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
                                st.error("GENERATION_FAILED: RETRY")

        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #404040;
                    letter-spacing: 0.1em; margin-top: 1rem;">SYNC_ENABLED</div>
        """, unsafe_allow_html=True)

    # ========== TAB 3: IMPORT WALLET (RECOVER) ==========
    with tab3:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.15em; margin-bottom: 1rem;">RESTORE_EXISTING</div>
        """, unsafe_allow_html=True)

        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px;">IDENTITY (OPTIONAL)</div>""", unsafe_allow_html=True)
        import_email = st.text_input("Email (optional)", key="import_email", placeholder="user@domain.com",
                                     label_visibility="collapsed")

        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px; margin-top: 12px;">RECOVERY_PHRASE</div>""", unsafe_allow_html=True)
        recovery_input = st.text_area(
            "Recovery phrase or private key",
            key="import_recovery",
            placeholder="12 WORD PHRASE OR 0x PRIVATE KEY_",
            height=100,
            label_visibility="collapsed"
        )

        st.markdown("""<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252;
                    letter-spacing: 0.1em; margin-bottom: 4px; margin-top: 12px;">ENCRYPTION_KEY</div>""", unsafe_allow_html=True)
        import_password = st.text_input("Password", type="password", key="import_pwd",
                                        placeholder="LOCAL ENCRYPTION KEY_",
                                        label_visibility="collapsed")

        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #404040;
                    letter-spacing: 0.1em; margin-top: 1rem; margin-bottom: 1rem;">ENCRYPTED_LOCALLY</div>
        """, unsafe_allow_html=True)

        if st.button("RESTORE WALLET", type="primary", use_container_width=True,
                     disabled=not (recovery_input and import_password)):
            with st.spinner("RESTORING_"):
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

                    st.success("WALLET_RESTORED")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("INVALID_RECOVERY_DATA")


def _load_theme_css():
    """Load V10 'Brutalist Fintech' theme CSS from static file"""
    css_path = os.path.join(os.path.dirname(__file__), "static", "theme.css")
    try:
        with open(css_path, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback: log warning but don't crash
        from utils.logger import logger
        logger.warning(f"Theme CSS not found at {css_path}")


def main():
    """Main app entry point"""
    st.set_page_config(
        page_title="Chat02",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # V10 Design System: "Brutalist Fintech" - Load from static file
    _load_theme_css()

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
