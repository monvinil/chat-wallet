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

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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

@tool
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


@tool
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


@tool
def read_latest_emails(count: int = 3) -> str:
    """Read latest emails. Args: count - number of emails"""
    return json.dumps({"status": "success", "emails": MOCK_EMAILS[:min(count, 10)], "note": "[SIMULATED]"}, indent=2)


# ============================================================================
# AGENT
# ============================================================================

def create_agent():
    """Create the LangChain agent"""
    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0.3,
        max_tokens=4096
    )

    # Import email and Bitrefill tools
    from email_tools import get_email_tools
    from bitrefill_tools import get_bitrefill_tools

    custom_tools = [
        get_wallet_balance,
        get_deposit_address,
        read_latest_emails
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

                                st.balloons()
                                time.sleep(3)
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

            # Lock wallet
            if st.button("Lock", use_container_width=True):
                WalletManager.lock_wallet()
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

    # Professional VC/TradFi styling
    st.markdown("""
    <style>
    /* Clean, professional typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Refined header styling */
    h1 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #1A1A2E !important;
    }

    h2, h3 {
        font-weight: 500 !important;
        color: #2D3748 !important;
    }

    /* Professional card styling */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    [data-testid="stMetricValue"] {
        font-weight: 600 !important;
        color: #1A1A2E !important;
    }

    /* Cleaner buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s ease !important;
        border: 1px solid transparent !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,102,255,0.15);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0066FF 0%, #0052CC 100%) !important;
    }

    /* Refined sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border-right: 1px solid #E2E8F0;
    }

    [data-testid="stSidebar"] h1 {
        font-size: 1.25rem !important;
        margin-bottom: 1rem;
    }

    /* Professional input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
        padding: 12px !important;
        font-size: 14px !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #0066FF !important;
        box-shadow: 0 0 0 3px rgba(0,102,255,0.1) !important;
    }

    /* Cleaner tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }

    /* Chat message styling */
    [data-testid="stChatMessage"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }

    /* Code blocks */
    code {
        background: #F1F5F9 !important;
        color: #1A1A2E !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 13px !important;
    }

    /* Info/Warning/Error boxes */
    .stAlert {
        border-radius: 8px !important;
        border: none !important;
    }

    /* Dividers */
    hr {
        border-color: #E2E8F0 !important;
        margin: 1.5rem 0 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Professional expander */
    .streamlit-expanderHeader {
        font-weight: 500 !important;
        color: #4A5568 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    init_state()

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
            st.balloons()
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

    # Initialize agent only if wallet exists
    if st.session_state.wallet_address and st.session_state.agent is None:
        with st.spinner("Initializing AI Agent..."):
            try:
                agent = create_agent()
                st.session_state.agent = agent

                # Fetch initial balances
                balances = ChainUtils.get_all_balances(st.session_state.wallet_address)
                st.session_state.balances = balances
            except Exception as e:
                st.error(f"Failed to initialize: {e}")
                st.stop()

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
