"""
Chat-First Crypto Wallet - Non-Custodial Version
User controls their own wallet, AI agent assists with transactions
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
    get_encrypted_wallet
)
from settings_ui import settings_page
from session_manager import SessionManager

try:
    from cdp_langchain.agent_toolkits import CdpToolkit
    from cdp_langchain.utils import CdpAgentkitWrapper
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False

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

def get_wallet_balance() -> str:
    """Get current wallet balances across all chains. No arguments needed."""
    if "wallet_address" not in st.session_state:
        return json.dumps({"error": "No wallet connected"})

    address = st.session_state.wallet_address
    balances = ChainUtils.get_all_balances(address)
    total_usdc = ChainUtils.calculate_total_usdc(balances)

    # Build a clean, dollar-first response
    result = {
        "total_balance": f"${total_usdc:.2f} USDC",
        "address": ChainUtils.format_address(address),
        "breakdown_by_network": {}
    }

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

def create_agent():
    """Create the LangChain agent (lazy import for faster initial load)"""
    # Lazy import LangChain modules (saves 1-2s on app startup)
    from langchain_core.tools import tool
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from settings_manager import SettingsManager

    # Wrap tools with @tool decorator at runtime
    tool_get_wallet_balance = tool(get_wallet_balance)
    tool_get_deposit_address = tool(get_deposit_address)
    tool_preview_transaction = tool(preview_transaction)
    tool_read_latest_emails = tool(read_latest_emails)

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

    # Import email, Bitrefill, and merchant tools
    from email_tools import get_email_tools
    from bitrefill_tools import get_bitrefill_tools
    from merchant_tools import get_merchant_tools

    custom_tools = [
        tool_get_wallet_balance,
        tool_get_deposit_address,
        tool_preview_transaction,
        tool_read_latest_emails
    ] + get_email_tools() + get_bitrefill_tools() + get_merchant_tools()  # Add email, Bitrefill, and crypto merchant tools

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
                                st.error(f"Database error: {str(e)}")
                                st.info("💡 Tip: Make sure you've run the Supabase migrations")
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
                                st.session_state.show_auth_modal = False

                                # Create persistent session (cookie)
                                SessionManager.login(user["id"], email, wallet_info["address"])

                                st.success("Account created")

                                # Show seed phrase in expander
                                if wallet_info.get("mnemonic"):
                                    with st.expander("Save your recovery phrase", expanded=True):
                                        st.warning("Write this down and store it securely. This is the only way to recover your wallet if you lose your password.")
                                        st.code(wallet_info["mnemonic"], language=None)

                                        acknowledged = st.checkbox("I have saved my recovery phrase")

                                        if acknowledged:
                                            if st.button("Continue", type="primary", use_container_width=True):
                                                # Initialize onboarding for new user
                                                st.session_state.onboarding_step = 1
                                                st.session_state.onboarding_complete = False
                                                st.session_state.just_signed_up = True
                                                st.rerun()
                                        else:
                                            st.caption("Please confirm you've saved your recovery phrase to continue")
                                else:
                                    # No seed phrase (shouldn't happen, but handle gracefully)
                                    st.session_state.onboarding_step = 1
                                    st.session_state.onboarding_complete = False
                                    time.sleep(1)
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
                    # Get user from database
                    user = get_user_by_email(login_email)

                    if not user:
                        st.error("No account found with this email")
                    else:
                        # Verify password
                        stored_hash = get_user_password_hash(user["id"])

                        if stored_hash and not WalletManager.verify_password(login_password, stored_hash):
                            st.error("Incorrect password")
                        else:
                            # Password verified (or no hash stored - legacy account)
                            # Get user's wallet
                            wallets = get_user_wallets(user["id"])

                            if wallets and len(wallets) > 0:
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

                                # Try to restore encrypted wallet from cloud backup
                                encrypted_wallet = get_encrypted_wallet(user["id"])
                                if encrypted_wallet:
                                    # Restore wallet to session
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

                                # No animation delay - just rerun
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


def show_success_animation():
    """Show a professional success animation instead of balloons"""
    st.markdown("""
    <style>
    @keyframes success-checkmark {
        0% { transform: scale(0); opacity: 0; }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); opacity: 1; }
    }

    @keyframes success-ring {
        0% { transform: scale(0.8); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }

    @keyframes confetti-fall {
        0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
    }

    .success-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(15, 15, 20, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fade-in 0.3s ease;
    }

    @keyframes fade-in {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    .success-content {
        text-align: center;
    }

    .success-icon {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(145deg, #10B981 0%, #059669 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
        animation: success-checkmark 0.5s ease-out;
        box-shadow: 0 0 40px rgba(16, 185, 129, 0.4);
    }

    .success-icon svg {
        width: 40px;
        height: 40px;
        stroke: white;
        stroke-width: 3;
        fill: none;
    }

    .success-ring {
        position: absolute;
        width: 100px;
        height: 100px;
        border: 3px solid rgba(16, 185, 129, 0.3);
        border-radius: 50%;
        animation: success-ring 0.6s ease-out;
    }

    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        top: -10px;
        animation: confetti-fall 3s ease-out forwards;
    }

    .confetti:nth-child(1) { left: 10%; background: #3B82F6; animation-delay: 0s; }
    .confetti:nth-child(2) { left: 20%; background: #8B5CF6; animation-delay: 0.1s; }
    .confetti:nth-child(3) { left: 30%; background: #10B981; animation-delay: 0.2s; }
    .confetti:nth-child(4) { left: 40%; background: #F59E0B; animation-delay: 0.15s; }
    .confetti:nth-child(5) { left: 50%; background: #3B82F6; animation-delay: 0.25s; }
    .confetti:nth-child(6) { left: 60%; background: #EC4899; animation-delay: 0.1s; }
    .confetti:nth-child(7) { left: 70%; background: #8B5CF6; animation-delay: 0.3s; }
    .confetti:nth-child(8) { left: 80%; background: #10B981; animation-delay: 0.05s; }
    .confetti:nth-child(9) { left: 90%; background: #3B82F6; animation-delay: 0.2s; }
    </style>

    <div class="success-overlay" id="successOverlay">
        <div class="confetti"></div>
        <div class="confetti"></div>
        <div class="confetti"></div>
        <div class="confetti"></div>
        <div class="confetti"></div>
        <div class="confetti"></div>
        <div class="confetti"></div>
        <div class="confetti"></div>
        <div class="confetti"></div>
        <div class="success-content">
            <div style="position: relative; display: inline-block;">
                <div class="success-ring"></div>
                <div class="success-icon">
                    <svg viewBox="0 0 24 24">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
            </div>
        </div>
    </div>

    <script>
        setTimeout(function() {
            var overlay = document.getElementById('successOverlay');
            if (overlay) {
                overlay.style.opacity = '0';
                overlay.style.transition = 'opacity 0.5s ease';
                setTimeout(function() { overlay.remove(); }, 500);
            }
        }, 2000);
    </script>
    """, unsafe_allow_html=True)


def generate_qr(data: str):
    """Generate QR code"""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def deposit_modal():
    """Show deposit address modal"""
    st.markdown("### Deposit")

    # Chain selector
    chain_options = {
        "Base Sepolia (Testnet)": "base-sepolia",
        "Base Mainnet": "base-mainnet",
        "Arbitrum Sepolia (Testnet)": "arbitrum-sepolia",
        "Polygon Amoy (Testnet)": "polygon-amoy",
    }

    selected_chain_name = st.selectbox("Network", list(chain_options.keys()))
    selected_chain = chain_options[selected_chain_name]

    network = NETWORKS[selected_chain]
    address = st.session_state.wallet_address

    if network['testnet']:
        st.caption(f"{network['name']} (Testnet)")
    else:
        st.caption(f"{network['name']} (Mainnet)")

    # Address
    st.code(address)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Copy", use_container_width=True):
            st.toast("Address copied")

    with col2:
        explorer_url = ChainUtils.get_explorer_url(selected_chain, address)
        st.link_button("View on explorer", explorer_url, use_container_width=True)

    # QR Code
    st.divider()
    qr_img = generate_qr(address)
    st.image(qr_img, width=180)

    # Instructions
    if "sepolia" in selected_chain or "amoy" in selected_chain:
        with st.expander("Get testnet funds"):
            st.markdown("""
Get testnet tokens from these faucets:
- [Coinbase Faucet](https://portal.cdp.coinbase.com/products/faucet)
- [Alchemy Faucet](https://sepoliafaucet.com/)
""")
    else:
        st.warning("This is mainnet. Only deposit real funds.")


def send_modal():
    """Show send transaction modal with gasless transfer"""
    from transaction_relayer import TransactionRelayer
    from meta_tx import MetaTransaction

    st.markdown("### Send USDC")
    st.caption("Gasless—network fees are covered.")

    # Network selector
    network_options = {
        "Base Sepolia (Testnet)": "base-sepolia",
    }
    selected_network = st.selectbox("Network", list(network_options.keys()))
    network_key = network_options[selected_network]

    # Recipient address
    recipient = st.text_input("Recipient Address", placeholder="0x...")

    # Amount
    amount = st.number_input("Amount (USDC)", min_value=0.01, step=0.01, format="%.2f")

    # Estimate fees
    if amount > 0:
        try:
            relayer = TransactionRelayer(network_key)
            gas_cost, app_fee = relayer.estimate_gas_cost(amount)
            total = amount + gas_cost + app_fee

            st.markdown(f"""
**Fee breakdown**
- Amount: ${amount:.2f}
- Network fee: ${gas_cost:.3f} (covered)
- Service fee: ${app_fee:.3f}
- **Total: ${total:.2f}**
""")
        except Exception as e:
            st.caption(f"Could not estimate fees: {e}")
            total = amount

    # Validate inputs
    valid_recipient = False
    recipient_error = ""

    if recipient:
        if not recipient.startswith("0x"):
            recipient_error = "Address must start with 0x"
        elif len(recipient) != 42:
            recipient_error = "Address must be 42 characters"
        else:
            # Check if valid hex
            try:
                int(recipient, 16)
                valid_recipient = True
            except ValueError:
                recipient_error = "Invalid address format"

    if recipient and not valid_recipient:
        st.warning(recipient_error)

    can_send = valid_recipient and amount > 0

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_send_modal = False

    with col2:
        if st.button("Confirm & Send", type="primary", use_container_width=True, disabled=not can_send):
            with st.spinner("Processing transaction..."):
                try:
                    # Get wallet data
                    wallet_data = WalletManager.get_wallet_from_session()

                    if not wallet_data:
                        st.error("Could not load wallet. Please unlock first.")
                        return

                    # Get chain ID for signing
                    network = NETWORKS[network_key]
                    chain_id = network["chain_id"]

                    # Create meta-transaction message
                    message = MetaTransaction.create_message(
                        from_address=st.session_state.wallet_address,
                        to_address=recipient,
                        amount=amount,
                        currency="USDC",
                        nonce=int(time.time() * 1000)  # Millisecond-precision nonce for uniqueness
                    )

                    # Sign message (user's signature, no gas!)
                    signature = MetaTransaction.sign_message(
                        message,
                        wallet_data["private_key"],
                        chain_id=chain_id
                    )

                    # Execute via relayer
                    relayer = TransactionRelayer(network_key)
                    result = relayer.execute_transfer(
                        message=message,
                        signature=signature,
                        user_address=st.session_state.wallet_address
                    )

                    if result["success"]:
                        st.success("Transaction complete")
                        st.markdown(f"""
- Hash: `{result['tx_hash'][:20]}...`
- Amount: ${result['amount']:.2f}
- Fee: ${result['gas_cost']:.3f}
""")
                        st.link_button("View on explorer", result["explorer_url"], use_container_width=True)
                        st.session_state.show_send_modal = False
                    else:
                        st.error(f"Transaction failed: {result['error']}")

                except Exception as e:
                    st.error(f"Something went wrong: {str(e)}")


def sidebar():
    """Render sidebar"""
    with st.sidebar:
        st.title("Wallet")

        # Show login button if no wallet
        if not st.session_state.wallet_address:
            st.caption("Sign in to access your wallet")
            if st.button("Sign In", use_container_width=True, type="primary"):
                st.session_state.show_auth_modal = True
                st.rerun()

            st.divider()
            st.metric("Total Balance", "$0.00")

            with st.expander("Balance by Network"):
                st.caption("Base: $0.00")
                st.caption("Arbitrum: $0.00")
                st.caption("Polygon: $0.00")

            st.divider()

            # Preview buttons (disabled)
            st.button("Deposit", use_container_width=True, disabled=True)
            st.button("Send", use_container_width=True, disabled=True)

            return

        if st.session_state.wallet_address and not st.session_state.get("wallet_locked", True):
            # Wallet info
            address = st.session_state.wallet_address
            st.code(ChainUtils.format_address(address, 8))

            # Action buttons in row
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Deposit", use_container_width=True, type="primary"):
                    st.session_state.show_deposit_modal = True
                    st.rerun()
            with col2:
                if st.button("Send", use_container_width=True):
                    st.session_state.show_send_modal = True
                    st.rerun()

            st.divider()

            # Show balances
            if st.session_state.balances:
                total_usdc = ChainUtils.calculate_total_usdc(st.session_state.balances)
                st.metric("Balance", f"${total_usdc:.2f}")

                # Expandable breakdown
                with st.expander("By network"):
                    for network_key, chain_balances in st.session_state.balances.items():
                        network_name = NETWORKS[network_key]["name"]
                        usdc = chain_balances.get("usdc", 0.0)

                        if usdc > 0:
                            st.caption(f"{network_name}: ${usdc:.2f}")
            else:
                st.metric("Balance", "$0.00")

            # Refresh balances
            if st.button("Refresh balance", use_container_width=True):
                with st.spinner("Updating..."):
                    balances = ChainUtils.get_all_balances(st.session_state.wallet_address)
                    st.session_state.balances = balances
                    st.toast("Updated")

            st.divider()

            # Settings and account
            if st.button("Settings", use_container_width=True):
                st.session_state.show_settings = True
                st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Lock", use_container_width=True):
                    WalletManager.lock_wallet()
                    st.rerun()
            with col2:
                if st.button("Log out", use_container_width=True):
                    SessionManager.logout()
                    st.rerun()

        else:
            # Wallet is locked or doesn't exist
            if "wallet_encrypted" in st.session_state:
                st.caption("🔒 Wallet locked")
                st.code(ChainUtils.format_address(st.session_state.wallet_address, 8))
                unlock_password = st.text_input("Password", type="password", key="unlock_pwd")
                if st.button("Unlock", use_container_width=True, type="primary"):
                    if unlock_password:
                        if WalletManager.unlock_wallet_with_password(unlock_password):
                            st.success("Unlocked")
                            st.rerun()
                        else:
                            st.error("Incorrect password")

                st.divider()

                # Allow Settings access even when locked
                if st.button("Settings", use_container_width=True):
                    st.session_state.show_settings = True
                    st.rerun()

                if st.button("Log out", use_container_width=True):
                    SessionManager.logout()
                    st.rerun()

            elif st.session_state.get("wallet_address"):
                st.caption("Import your wallet to continue")
                st.code(ChainUtils.format_address(st.session_state.wallet_address))
                if st.button("Import Wallet", use_container_width=True, type="primary"):
                    st.session_state.show_auth_modal = True
                    st.rerun()


def render_quick_actions():
    """Render quick action chips above chat"""
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Send", key="quick_send", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I want to send money"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col2:
        if st.button("Gift Card", key="quick_giftcard", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Show me gift cards"})
            st.session_state._quick_action_triggered = True
            st.rerun()

    with col3:
        if st.button("Pay Bill", key="quick_bill", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Help me pay a bill"})
            st.session_state._quick_action_triggered = True
            st.rerun()


def render_suggested_actions():
    """Render horizontally scrollable action pills above chat input"""

    # Suggested actions data
    actions = [
        ("🎵", "Apple Music 1mo"),
        ("🎁", "Amazon Gift Card"),
        ("📺", "YouTube Vault"),
        ("💰", "Lend to Aave"),
        ("₿", "Buy Bitcoin"),
        ("🎧", "Spotify Premium"),
        ("☕", "Starbucks Card"),
    ]

    # CSS for horizontal scrolling pills
    st.markdown("""
    <style>
    .suggested-pills {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding: 12px 0;
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
    .suggested-pills::-webkit-scrollbar {
        display: none;
    }
    .pill-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 20px;
        color: #93C5FD;
        font-size: 13px;
        font-weight: 500;
        white-space: nowrap;
        cursor: pointer;
        transition: all 0.2s ease;
        flex-shrink: 0;
        text-decoration: none;
    }
    .pill-btn:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: rgba(59, 130, 246, 0.5);
        color: #BFDBFE;
        transform: translateY(-1px);
    }
    .pill-btn:active {
        transform: translateY(0);
    }
    </style>
    """, unsafe_allow_html=True)

    # Build HTML pills with data attributes for click handling
    pills_html = '<div class="suggested-pills">'
    for emoji, label in actions:
        pills_html += f'<button class="pill-btn" onclick="showComingSoon(\'{label}\')">{emoji} {label}</button>'
    pills_html += '</div>'

    # JavaScript for click handling (shows toast via Streamlit's native toast styling)
    pills_html += """
    <script>
    function showComingSoon(label) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.innerHTML = '🚧 ' + label + ' — Coming soon!';
        toast.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: #1f2937;
            color: #f3f4f6;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 9999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: fadeInOut 2.5s ease forwards;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2500);
    }
    </script>
    <style>
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateX(-50%) translateY(10px); }
        15% { opacity: 1; transform: translateX(-50%) translateY(0); }
        85% { opacity: 1; transform: translateX(-50%) translateY(0); }
        100% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
    }
    </style>
    """

    st.markdown(pills_html, unsafe_allow_html=True)


def chat_interface():
    """Main chat interface"""
    st.title("Chat Wallet")
    st.caption("Manage your wallet through conversation")

    # Quick Start mode - create guest wallet if no wallet exists
    if not st.session_state.wallet_address:
        from quick_start import create_guest_wallet

        # Show clean intro with quick start button
        with st.chat_message("assistant"):
            st.markdown("""**Chat Wallet** lets you manage crypto through conversation.

**What you can do:**
- Check balances across Base, Arbitrum, and Polygon
- Send USDC with zero gas fees
- Buy gift cards from Amazon, Uber, Netflix, and more
- Purchase domains, VPN subscriptions, and travel
- Pay bills directly with crypto

**Get started:**
1. Click **Quick Start** below to create a wallet
2. Get a free API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
3. Start chatting

Your wallet is self-custodial—you control the private keys.
""")

            _, col_center, _ = st.columns([1, 2, 1])
            with col_center:
                if st.button("Quick Start", type="primary", use_container_width=True, key="quick_start_btn"):
                    with st.spinner("Creating wallet..."):
                        if create_guest_wallet():
                            st.session_state.quick_start_active = True
                            st.success("Wallet created")
                            st.rerun()
                        else:
                            st.error("Could not create wallet. Please try again.")

            st.divider()
            st.caption("Or create an account to save your wallet across devices")

        # Disabled chat input
        st.chat_input("Message...", disabled=True, key="preview_input")
        return

    # If wallet is locked, show a message to unlock
    if st.session_state.get("wallet_locked", False) and st.session_state.get("wallet_encrypted"):
        st.info("🔒 **Wallet locked** — Enter your password in the sidebar to unlock your wallet and start chatting.")
        st.chat_input("Message...", disabled=True, key="locked_input")
        return

    # Show onboarding flow if user hasn't completed setup
    from onboarding import show_onboarding
    if not show_onboarding():
        # User is still in onboarding, don't show chat
        return

    # Check if API key is configured (show banner if missing)
    from api_key_setup import show_api_key_banner, check_api_key_status
    has_api_key, _ = check_api_key_status()

    if not has_api_key:
        # Show prominent banner instead of showing error in chat
        show_api_key_banner()
        return

    # If API key was just configured, force agent re-initialization
    if has_api_key and st.session_state.get("_api_key_just_saved"):
        st.session_state.agent = None  # Force recreation
        st.session_state._agent_initializing = False
        st.session_state._api_key_just_saved = False  # Clear flag

    # Quick action chips for logged-in users (only after onboarding complete)
    render_quick_actions()

    st.divider()

    # Normal logged-in chat interface
    # Show messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Determine if we need to process a message (from chat input OR quick action)
    prompt = None
    if st.session_state.get("_quick_action_triggered"):
        # Quick action button was clicked - get the last user message
        st.session_state._quick_action_triggered = False
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            prompt = st.session_state.messages[-1]["content"]

    # Suggested actions - scrollable pills above chat input
    render_suggested_actions()

    # Chat input (only if not processing quick action)
    if not prompt:
        prompt = st.chat_input("Message...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

    # Process the message (from either source)
    if prompt:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Safety check: ensure agent is initialized
                    if not st.session_state.get("agent"):
                        # Try to initialize agent now
                        try:
                            agent = create_agent()
                            if agent:
                                st.session_state.agent = agent
                        except Exception:
                            pass

                    if not st.session_state.get("agent"):
                        # Still no agent - provide helpful guidance
                        from api_key_setup import check_api_key_status
                        has_key, provider = check_api_key_status()

                        if not has_key:
                            response = """**AI provider not connected**

To use the chat assistant, you need to connect an AI provider first.

Click **Settings** in the sidebar, then go to **AI Provider** to add your API key. We recommend Google Gemini—it's free."""
                        else:
                            response = """**AI assistant loading...**

The assistant is still initializing. This usually takes a moment after logging in.

**Try:** Refresh the page (F5) or wait a few seconds and try again."""
                    else:
                        # Lazy import LangChain message types
                        from langchain_core.messages import HumanMessage, AIMessage

                        history = []
                        for m in st.session_state.messages[:-1]:
                            if m["role"] == "user":
                                history.append(HumanMessage(content=m["content"]))
                            else:
                                history.append(AIMessage(content=m["content"]))

                        result = st.session_state.agent.invoke({
                            "input": prompt,
                            "chat_history": history
                        })

                        response = result.get("output", "Sorry, I couldn't process that.")

                except Exception as e:
                    error_msg = str(e)

                    # Provide helpful guidance for API key errors
                    if "API key" in error_msg or "credit" in error_msg.lower() or "authentication" in error_msg.lower():
                        response = """**API key issue**

There's a problem with your AI provider. Please check your API key in **Settings** → **AI Provider**.

Common fixes:
- **Google Gemini:** Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Anthropic/OpenAI:** Make sure you have credits in your account"""
                    elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
                        response = """**Rate limit reached**

You've hit the API rate limit. Wait a minute and try again, or switch to a different AI provider in Settings."""
                    else:
                        response = f"Something went wrong: {error_msg}"

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # Welcome message for logged in users (only shown after onboarding complete)
    if not st.session_state.messages:
        welcome = f"""Wallet connected: `{ChainUtils.format_address(st.session_state.wallet_address)}`

**Try these commands:**
- "What's my balance?"
- "Send $20 to 0x..."
- "Show my deposit address"
- "Buy a $25 Amazon gift card"
- "Register mydomain.com"
- "Get Mullvad VPN"

What would you like to do?
"""
        st.session_state.messages.append({"role": "assistant", "content": welcome})


def main():
    """Main app entry point"""
    st.set_page_config(
        page_title="Chat Wallet",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Professional dark theme styling
    st.markdown("""
    <style>
    /* Smooth fade-in to prevent flash */
    .stApp {
        animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* Clean, professional typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Dark theme header styling */
    h1 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #F9FAFB !important;
    }

    h2, h3 {
        font-weight: 500 !important;
        color: #D1D5DB !important;
    }

    /* Professional card styling with texture */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1F1F2E 0%, #16161F 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    }

    [data-testid="stMetricValue"] {
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        color: #FFFFFF !important;
    }

    [data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
        font-size: 0.875rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Textured buttons with depth */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        padding: 0.625rem 1.25rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: linear-gradient(145deg, #252532 0%, #1C1C26 100%) !important;
        color: #E5E7EB !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.04);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.12) !important;
        background: linear-gradient(145deg, #2A2A3A 0%, #202030 100%) !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(145deg, #3B82F6 0%, #2563EB 100%) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 16px rgba(59,130,246,0.3), inset 0 1px 0 rgba(255,255,255,0.15);
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(145deg, #4F8FFF 0%, #3B7BF6 100%) !important;
        box-shadow: 0 8px 28px rgba(59,130,246,0.4), inset 0 1px 0 rgba(255,255,255,0.2);
    }

    /* Refined dark sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141419 0%, #0F0F14 100%);
        border-right: 1px solid rgba(255,255,255,0.04);
    }

    [data-testid="stSidebar"] h1 {
        font-size: 1.25rem !important;
        margin-bottom: 1rem;
        color: #F9FAFB !important;
    }

    /* Dark input fields with glow */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: #1A1A24 !important;
        padding: 14px !important;
        font-size: 14px !important;
        color: #E5E7EB !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15), inset 0 2px 4px rgba(0,0,0,0.2) !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #6B7280 !important;
    }

    /* Dark tabs with texture */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding-bottom: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 18px;
        font-weight: 500;
        background: transparent;
        color: #9CA3AF;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(145deg, #252532 0%, #1C1C26 100%);
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    /* Dark chat messages */
    [data-testid="stChatMessage"] {
        background: linear-gradient(145deg, #1A1A24 0%, #14141C 100%);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }

    /* Dark code blocks */
    code {
        background: #252532 !important;
        color: #A5B4FC !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        border: 1px solid rgba(255,255,255,0.06);
    }

    /* Dark alert boxes */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        background: linear-gradient(145deg, #1A1A24 0%, #14141C 100%) !important;
    }

    /* Dark dividers */
    hr {
        border-color: rgba(255,255,255,0.06) !important;
        margin: 1.5rem 0 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Dark expander */
    .streamlit-expanderHeader {
        font-weight: 500 !important;
        color: #9CA3AF !important;
        background: linear-gradient(145deg, #1A1A24 0%, #14141C 100%);
        border-radius: 10px;
        padding: 12px 16px !important;
    }

    details {
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
    }

    /* Quick action chips */
    .quick-action {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        background: linear-gradient(145deg, #252532 0%, #1C1C26 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        color: #E5E7EB;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        margin: 4px;
    }

    .quick-action:hover {
        background: linear-gradient(145deg, #2A2A3A 0%, #202030 100%);
        border-color: rgba(255,255,255,0.12);
        transform: translateY(-1px);
    }

    .quick-action.active {
        background: linear-gradient(145deg, #3B82F6 0%, #2563EB 100%);
        border-color: rgba(255,255,255,0.15);
        color: #FFFFFF;
    }

    /* Status indicator */
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-dot.connected {
        background: #10B981;
        box-shadow: 0 0 8px rgba(16,185,129,0.5);
    }

    .status-dot.disconnected {
        background: #6B7280;
    }

    /* Section cards */
    .section-card {
        background: linear-gradient(145deg, #1A1A24 0%, #14141C 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }

    /* Number input styling */
    .stNumberInput > div > div > input {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: #1A1A24 !important;
        color: #E5E7EB !important;
    }

    /* Select box styling */
    .stSelectbox > div > div {
        background: #1A1A24 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    init_state()

    # Initialize cookie manager and restore session from cookie
    # This handles page refresh - session state is cleared but cookies persist
    if not st.session_state.get("wallet_address"):
        try:
            SessionManager.get_cookie_manager()
            SessionManager.restore_session()
        except Exception as e:
            # Cookie manager can fail on first load - this is OK
            pass

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
        # Only fetch if not locked
        if not st.session_state.get("wallet_locked", True):
            try:
                balances = ChainUtils.get_all_balances(st.session_state.wallet_address)
                st.session_state.balances = balances
            except Exception as e:
                from utils.logger import logger
                logger.error(f"Balance fetch error: {e}")

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
    chat_interface()


if __name__ == "__main__":
    main()
