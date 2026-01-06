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

SYSTEM_PROMPT = """You are a helpful crypto wallet assistant. You help users manage their non-custodial wallet across multiple chains.

**Your capabilities:**
1. Check wallet balances across Base Sepolia, Base Mainnet, Arbitrum, Polygon, Solana
2. Help prepare transactions (user must approve each one)
3. Provide deposit addresses for receiving funds
4. **Buy gift cards with crypto** via Bitrefill API:
   - Search for Amazon, Uber, Netflix, Starbucks, and 1000+ other gift cards
   - Purchase gift cards with USDC/crypto
   - Send gift card codes to user's email automatically
5. **Email automation** - If user connected email:
   - Read verification codes from emails (for signups/2FA)
   - Search recent emails (last 24 hours)
   - Help with automated signups on external services
6. Autonomous tasks - buy domains, purchase gift cards, sign up for services

**Email Automation Workflow:**
When user asks to sign up for a service (e.g., Porkbun, Amazon):
1. Check if email is connected (use check_email_connected tool)
2. If not connected, ask user to connect email in Settings → Connected Accounts
3. Use the user's connected email to fill signup forms
4. After submitting form, wait 30-60 seconds
5. Use get_verification_code tool to retrieve code from email
6. Complete signup with the code

**Important:**
- User controls their own private keys (non-custodial)
- Always show fees upfront before transactions
- User must approve every transaction
- Never promise anything without user confirmation
- For email automation: Only access recent emails (last 24 hours)
- Always ask permission before signing up for external services

Network Support:
- Base Sepolia (testnet) ✅ Real
- Base Mainnet ✅ Real
- Arbitrum Sepolia (testnet) ✅ Real
- Polygon Amoy (testnet) ✅ Real
- Solana Devnet (testnet) 🔜 Coming soon

Fee Structure: $0.005 + 0.2% (max $3)
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

    result = {
        "address": ChainUtils.format_address(address),
        "total_usdc": total_usdc,
        "balances_by_chain": {}
    }

    for network_key, chain_balances in balances.items():
        network_name = NETWORKS[network_key]["name"]
        result["balances_by_chain"][network_name] = chain_balances

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


def read_latest_emails(count: int = 3) -> str:
    """Read latest emails. Args: count - number of emails"""
    return json.dumps({"status": "success", "emails": MOCK_EMAILS[:min(count, 10)], "note": "[SIMULATED]"}, indent=2)


# ============================================================================
# AGENT
# ============================================================================

def create_agent():
    """Create the LangChain agent (lazy import for faster initial load)"""
    # Lazy import LangChain modules (saves 1-2s on app startup)
    from langchain_anthropic import ChatAnthropic
    from langchain_core.tools import tool
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from settings_manager import SettingsManager

    # Wrap tools with @tool decorator at runtime
    tool_get_wallet_balance = tool(get_wallet_balance)
    tool_get_deposit_address = tool(get_deposit_address)
    tool_read_latest_emails = tool(read_latest_emails)

    # Get user's LLM config (custom API key if set, otherwise app default)
    user_id = st.session_state.get("user_id")
    llm_config = SettingsManager.get_llm_config(user_id)

    # Use the configured API key (falls back to ANTHROPIC_API_KEY env var)
    llm = ChatAnthropic(
        model=llm_config.get("model", "claude-sonnet-4-20250514"),
        api_key=llm_config.get("api_key"),
        temperature=0.3,
        max_tokens=4096
    )

    # Import email and Bitrefill tools
    from email_tools import get_email_tools
    from bitrefill_tools import get_bitrefill_tools

    custom_tools = [
        tool_get_wallet_balance,
        tool_get_deposit_address,
        tool_read_latest_emails
    ] + get_email_tools() + get_bitrefill_tools()  # Add email automation and Bitrefill tools

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
    st.markdown("##### Self-custody wallet with AI-powered transactions")

    st.info("**You control your keys.** Your wallet is encrypted client-side and backed up securely to the cloud.")

    tab1, tab2, tab3 = st.tabs(["Sign Up", "Log In", "Import Wallet"])

    # ========== TAB 1: SIGN UP ==========
    with tab1:
        st.subheader("Create Account")
        st.caption("Create a new wallet. Access it from any device with your credentials.")

        email = st.text_input("Email", key="signup_email", placeholder="your@email.com")
        password = st.text_input("Password (min 8 characters)", type="password", key="signup_pwd")
        password_confirm = st.text_input("Confirm Password", type="password", key="signup_pwd_confirm")

        if st.button("Create Account", type="primary", disabled=not (email and password)):
            if password != password_confirm:
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

                                st.success("Account created successfully")

                                # Show seed phrase
                                if wallet_info.get("mnemonic"):
                                    st.warning("**Important: Save your recovery phrase**")
                                    st.code(wallet_info["mnemonic"], language=None)
                                    st.caption("""
                                    Write this 12-word phrase down and store it securely.
                                    This is the only way to recover your wallet if you lose access.
                                    Never share it with anyone.
                                    """)

                                show_success_animation()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Failed to create user account.")
                                st.info("Possible causes: Supabase credentials not configured, email already exists, or database migrations not run.")

        st.caption("Your wallet syncs across all your devices automatically.")

    # ========== TAB 2: LOG IN ==========
    with tab2:
        st.subheader("Log In")
        st.caption("Access your existing wallet from any device.")

        login_email = st.text_input("Email", key="login_email", placeholder="your@email.com")
        login_password = st.text_input("Password", type="password", key="login_pwd")

        if st.button("Log In", type="primary", disabled=not (login_email and login_password)):
            with st.spinner("Logging in..."):
                # Get user from database
                user = get_user_by_email(login_email)

                if not user:
                    st.error("Account not found. Please sign up first.")
                else:
                    # Verify password
                    stored_hash = get_user_password_hash(user["id"])

                    if stored_hash and not WalletManager.verify_password(login_password, stored_hash):
                        st.error("Incorrect password. Please try again.")
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
                                    st.success("Welcome back. Wallet restored from cloud.")
                                else:
                                    st.session_state.wallet_locked = True
                                    st.success("Welcome back.")
                                    st.warning("Could not decrypt wallet. Try unlocking with your password.")
                            else:
                                # No cloud backup - need manual import (legacy account)
                                st.session_state.wallet_locked = True
                                st.success("Welcome back.")
                                st.info("To access your funds, import your wallet using your seed phrase or private key.")

                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("No wallet found for this account.")

    # ========== TAB 3: IMPORT WALLET ==========
    with tab3:
        st.subheader("Import Wallet")
        st.caption("Import an existing wallet using your recovery phrase or private key.")

        import_email = st.text_input("Email (optional)", key="import_email", placeholder="your@email.com")
        recovery_input = st.text_area(
            "Recovery Phrase or Private Key",
            key="import_recovery",
            placeholder="Enter 12-word phrase or 0x...",
            help="Enter either your 12-word seed phrase or your private key",
            height=100
        )
        import_password = st.text_input("Encryption Password", type="password", key="import_pwd")

        st.caption("Your credentials are encrypted locally before storage.")

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

                    st.success("Wallet imported successfully.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid recovery phrase or private key.")

        st.caption("Private keys are encrypted with AES-256 before storage.")


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
    st.subheader("Deposit")

    # Chain selector
    chain_options = {
        "Base Sepolia (Testnet)": "base-sepolia",
        "Base Mainnet": "base-mainnet",
        "Arbitrum Sepolia (Testnet)": "arbitrum-sepolia",
        "Polygon Amoy (Testnet)": "polygon-amoy",
    }

    selected_chain_name = st.selectbox("Select Network", list(chain_options.keys()))
    selected_chain = chain_options[selected_chain_name]

    network = NETWORKS[selected_chain]
    address = st.session_state.wallet_address

    st.markdown(f"**Network:** {network['name']}")
    st.markdown(f"**Type:** {'Testnet' if network['testnet'] else 'Mainnet'}")

    # Address
    st.code(address)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Copy Address", use_container_width=True):
            st.toast("Address copied")

    with col2:
        explorer_url = ChainUtils.get_explorer_url(selected_chain, address)
        st.link_button("View on Explorer", explorer_url, use_container_width=True)

    # QR Code
    st.markdown("**QR Code**")
    qr_img = generate_qr(address)
    st.image(qr_img, width=200)

    # Instructions
    with st.expander("Getting testnet funds"):
        if "sepolia" in selected_chain or "amoy" in selected_chain:
            st.markdown("""
            **Testnet USDC:**
            1. Obtain testnet ETH from a faucet
            2. Use a testnet USDC faucet or bridge

            **Faucets:**
            - [Coinbase Faucet](https://portal.cdp.coinbase.com/products/faucet)
            - [Alchemy Faucet](https://sepoliafaucet.com/)
            """)
        else:
            st.warning("This is mainnet. Only deposit real funds if intended.")


def send_modal():
    """Show send transaction modal with gasless transfer"""
    from transaction_relayer import TransactionRelayer
    from meta_tx import MetaTransaction

    st.subheader("Send USDC")
    st.caption("Gasless transaction - we cover the network fees.")

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

            st.info(f"""
            **Fee Summary**
            - Amount: ${amount:.2f}
            - Network Fee: ${gas_cost:.3f} (covered)
            - Service Fee: ${app_fee:.3f}
            - **Total: ${total:.2f}**
            """)
        except Exception as e:
            st.warning(f"Could not estimate fees: {e}")
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
        st.warning(f"⚠️ {recipient_error}")

    can_send = valid_recipient and amount > 0

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_send_modal = False
            st.rerun()

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
                        st.success(f"""
                        **Transaction Complete**

                        Hash: `{result['tx_hash'][:20]}...`
                        Amount: ${result['amount']:.2f}
                        Network Fee: ${result['gas_cost']:.3f}
                        Total: ${result['total_cost']:.2f}
                        """)

                        st.link_button("View on Explorer", result["explorer_url"], use_container_width=True)

                        # Close modal after success
                        time.sleep(2)
                        st.session_state.show_send_modal = False
                        st.rerun()
                    else:
                        st.error(f"Transaction failed: {result['error']}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def sidebar():
    """Render sidebar"""
    with st.sidebar:
        st.title("Wallet")

        # Show login button if no wallet
        if not st.session_state.wallet_address:
            st.info("Sign in to access your wallet")
            if st.button("Sign In", use_container_width=True, type="primary"):
                st.session_state.show_auth_modal = True
                st.rerun()

            st.divider()
            st.caption("**Preview Mode**")
            st.metric("Total Balance", "$0.00", help="Sign in to view balance")

            with st.expander("Balance by Network"):
                st.caption("Base Sepolia: $0.00")
                st.caption("Base Mainnet: $0.00")
                st.caption("Arbitrum Sepolia: $0.00")

            st.divider()

            # Preview buttons (disabled)
            st.button("Deposit", use_container_width=True, disabled=True, help="Sign in to deposit")
            st.button("Send", use_container_width=True, disabled=True, help="Sign in to send")
            st.button("Refresh", use_container_width=True, disabled=True, help="Sign in to refresh")

            return

        if st.session_state.wallet_address and not st.session_state.get("wallet_locked", True):
            # Wallet info
            address = st.session_state.wallet_address
            st.code(ChainUtils.format_address(address, 8))

            # Add USDC button
            if st.button("Deposit", use_container_width=True, type="primary"):
                st.session_state.show_deposit_modal = True
                st.rerun()

            # Send button
            if st.button("Send", use_container_width=True):
                st.session_state.show_send_modal = True
                st.rerun()

            # Refresh balances
            if st.button("Refresh", use_container_width=True):
                with st.spinner("Updating..."):
                    balances = ChainUtils.get_all_balances(st.session_state.wallet_address)
                    st.session_state.balances = balances
                    st.toast("Balances updated")

            st.divider()

            # Show balances
            if st.session_state.balances:
                total_usdc = ChainUtils.calculate_total_usdc(st.session_state.balances)

                # Total balance
                st.metric("Total Balance", f"${total_usdc:.2f}")

                # Expandable breakdown
                with st.expander("Balance by Network"):
                    for network_key, chain_balances in st.session_state.balances.items():
                        network_name = NETWORKS[network_key]["name"]
                        usdc = chain_balances.get("usdc", 0.0)

                        if usdc > 0:
                            st.markdown(f"**{network_name}**")
                            st.markdown(f"USDC: ${usdc:.2f}")

            st.divider()

            # Settings button
            if st.button("Settings", use_container_width=True):
                st.session_state.show_settings = True
                st.rerun()

            # Lock wallet (keep session)
            if st.button("Lock", use_container_width=True):
                WalletManager.lock_wallet()
                st.rerun()

            # Logout (clear session)
            if st.button("Logout", use_container_width=True):
                SessionManager.logout()
                st.rerun()

        else:
            # Wallet is locked or doesn't exist
            if "wallet_encrypted" in st.session_state:
                st.info("Wallet locked")
                unlock_password = st.text_input("Password", type="password", key="unlock_pwd")
                if st.button("Unlock", use_container_width=True, type="primary"):
                    if unlock_password:
                        # Re-derive encryption key from password and verify
                        if WalletManager.unlock_wallet_with_password(unlock_password):
                            st.success("Wallet unlocked")
                            st.rerun()
                        else:
                            st.error("Incorrect password")
            elif st.session_state.get("wallet_address"):
                # Logged in but no wallet data in session - need to import
                st.info("Import your wallet to continue")
                st.caption(f"Address: {ChainUtils.format_address(st.session_state.wallet_address)}")
                if st.button("Import Wallet", use_container_width=True, type="primary"):
                    st.session_state.show_auth_modal = True
                    st.rerun()


def render_quick_actions():
    """Render quick action chips above chat"""
    # Check connection status
    email_connected = st.session_state.get("gmail_connected", False)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if email_connected:
            if st.button("Email Connected", key="email_status", use_container_width=True):
                st.session_state.show_settings = True
                st.session_state.settings_tab = "accounts"
                st.rerun()
        else:
            if st.button("Connect Email", key="connect_email_quick", use_container_width=True):
                st.session_state.show_settings = True
                st.session_state.settings_tab = "accounts"
                st.rerun()

    with col2:
        if st.button("AI Provider", key="ai_provider_quick", use_container_width=True):
            st.session_state.show_settings = True
            st.session_state.settings_tab = "provider"
            st.rerun()

    with col3:
        if st.button("Settings", key="settings_quick", use_container_width=True):
            st.session_state.show_settings = True
            st.rerun()


def chat_interface():
    """Main chat interface"""
    st.title("Chat Wallet")
    st.caption("AI-powered self-custody wallet")

    # Preview mode if not logged in
    if not st.session_state.wallet_address:
        # Show demo conversation
        with st.chat_message("assistant"):
            st.markdown("""**Welcome to Chat Wallet**

I'm your AI assistant for managing digital assets. I can help you:

- Check balances across multiple networks
- Send USDC with gasless transactions
- Generate deposit addresses and QR codes
- Purchase gift cards with crypto
- Automate common wallet tasks

**Example queries:**
- "What's my balance?"
- "Send $10 USDC to 0x..."
- "Show deposit address for Base"

Sign in to get started.
""")

        # Disabled chat input
        st.chat_input("Sign in to start...", disabled=True)
        return

    # Quick action chips for logged-in users
    render_quick_actions()

    st.divider()

    # Normal logged-in chat interface
    # Show messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything about your wallet..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
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
                    response = f"Error: {e}"

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # Welcome message for logged in users
    if not st.session_state.messages:
        welcome = f"""**Welcome back**

Your wallet: `{ChainUtils.format_address(st.session_state.wallet_address)}`

I can help you with:
- Check balances across networks
- Prepare and execute transactions
- Generate deposit addresses
- Purchase gift cards

Try: "What's my balance?" or "Show deposit address for Base"
"""
        st.session_state.messages.append({"role": "assistant", "content": welcome})
        st.rerun()


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
        animation: fadeIn 0.2s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* Hide skeleton loaders during initial load to prevent boxes from showing */
    .stSkeleton {
        display: none !important;
    }

    /* Hide Streamlit's default loading animation */
    .stSpinner > div {
        display: none !important;
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

    # Initialize cookie manager (happens once, no forced rerun)
    if "_cookie_manager_init" not in st.session_state:
        st.session_state._cookie_manager_init = True
        SessionManager.get_cookie_manager()
        # Cookie manager needs one render cycle to be ready
        # Use stop() instead of rerun to prevent flash
        st.stop()

    # Restore session from cookie if not already done
    if not st.session_state.get("_app_initialized"):
        session_restored = SessionManager.restore_session()
        st.session_state._app_initialized = True

        # Only rerun if we actually restored a session (to show logged-in UI)
        if session_restored:
            st.rerun()

    # Handle OAuth callback
    query_params = st.query_params
    if "code" in query_params and "state" in query_params:
        # OAuth callback from Google
        from gmail_oauth import GmailOAuth

        code = query_params["code"]
        user_id = query_params["state"]  # User ID passed as state

        # Get app URL for redirect
        app_url = os.getenv("APP_URL", "http://localhost:8501")
        redirect_uri = f"{app_url}/oauth/callback"

        with st.spinner("Connecting Gmail..."):
            success = GmailOAuth.handle_oauth_callback(code, redirect_uri, user_id)

        if success:
            st.success("Gmail connected successfully")
            show_success_animation()
        else:
            st.error("Failed to connect Gmail")

        # Clear query params and redirect back to settings
        st.query_params.clear()
        st.session_state.show_settings = True
        time.sleep(2)  # Show success message
        st.rerun()

    # Show auth modal if requested
    if st.session_state.get("show_auth_modal"):
        wallet_setup_ui()
        if st.button("Back", use_container_width=False):
            st.session_state.show_auth_modal = False
            st.rerun()
        return

    # Initialize agent only if wallet exists (async, non-blocking)
    if st.session_state.wallet_address and st.session_state.agent is None:
        if not st.session_state.get("_agent_initializing"):
            st.session_state._agent_initializing = True

            try:
                # Create agent (fast)
                agent = create_agent()
                st.session_state.agent = agent

                # Fetch balances in background (don't block UI)
                if not st.session_state.get("balances"):
                    st.session_state.balances = {}

            except Exception as e:
                st.error(f"Failed to initialize: {e}")
                st.session_state._agent_initializing = False

    # Lazy-load balances after agent is ready (non-blocking)
    if st.session_state.wallet_address and not st.session_state.get("_balances_loaded"):
        if st.session_state.get("agent"):
            st.session_state._balances_loaded = True
            # Fetch in background - will update on next rerun
            try:
                balances = ChainUtils.get_all_balances(st.session_state.wallet_address)
                st.session_state.balances = balances
            except Exception as e:
                print(f"Balance fetch error: {e}")

    # Show deposit modal if requested (only if logged in)
    if st.session_state.get("show_deposit_modal") and st.session_state.wallet_address:
        deposit_modal()
        if st.button("Back"):
            st.session_state.show_deposit_modal = False
            st.rerun()
        return

    # Show send modal if requested (only if logged in)
    if st.session_state.get("show_send_modal") and st.session_state.wallet_address:
        send_modal()
        return

    # Show settings page if requested (only if logged in)
    if st.session_state.get("show_settings") and st.session_state.wallet_address:
        settings_page()
        if st.button("Back"):
            st.session_state.show_settings = False
            st.rerun()
        return

    # Main layout - always show (preview or logged in)
    sidebar()
    chat_interface()


if __name__ == "__main__":
    main()
