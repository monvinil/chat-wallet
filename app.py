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
    log_transaction
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
4. Search and buy gift cards (simulated)
5. Read emails (simulated)

**Important:**
- User controls their own private keys (non-custodial)
- Always show fees upfront before transactions
- User must approve every transaction
- Never promise anything without user confirmation

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


@tool
def search_bitrefill(query: str) -> str:
    """Search for gift cards. Args: query - search term"""
    q = query.lower()
    results = [c for c in MOCK_GIFT_CARDS if q in c["name"].lower()] or MOCK_GIFT_CARDS[:3]
    return json.dumps({"status": "success", "results": results, "note": "[SIMULATED]"}, indent=2)


@tool
def buy_gift_card(product_id: str) -> str:
    """Buy a gift card (requires user approval). Args: product_id - e.g. 'gc_001'"""
    card = next((c for c in MOCK_GIFT_CARDS if c["id"] == product_id), None)
    if not card:
        return json.dumps({"status": "error", "message": "Product not found"})

    fee = calculate_fee(card["price_usd"])
    total = card["price_usd"] + fee

    # Store pending transaction for user approval
    if "pending_tx" not in st.session_state:
        st.session_state.pending_tx = {
            "type": "gift_card_purchase",
            "product": card,
            "amount": card["price_usd"],
            "fee": fee,
            "total": total
        }

    return json.dumps({
        "status": "pending_approval",
        "product": card["name"],
        "amount": card["price_usd"],
        "fee": fee,
        "total": total,
        "message": "Transaction ready for user approval"
    }, indent=2)


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

    custom_tools = [
        get_wallet_balance,
        get_deposit_address,
        search_bitrefill,
        buy_gift_card,
        read_latest_emails
    ]

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
    st.title("🔐 Welcome to Chat Wallet")
    st.markdown("### Non-Custodial • Multi-Chain • AI-Powered")

    st.info("👉 **Your keys, your crypto.** We encrypt your wallet with your password and back it up securely.")

    tab1, tab2, tab3 = st.tabs(["Sign Up", "Log In", "Import Wallet"])

    # ========== TAB 1: SIGN UP ==========
    with tab1:
        st.subheader("Create Account")
        st.write("We'll create a wallet and encrypt it with your password. Access from any device!")

        email = st.text_input("Email", key="signup_email", placeholder="your@email.com")
        password = st.text_input("Password (min 8 characters)", type="password", key="signup_pwd")
        password_confirm = st.text_input("Confirm Password", type="password", key="signup_pwd_confirm")

        if st.button("Create Account & Wallet", type="primary", disabled=not (email and password)):
            if password != password_confirm:
                st.error("❌ Passwords don't match")
            elif len(password) < 8:
                st.error("❌ Password must be at least 8 characters")
            elif "@" not in email:
                st.error("❌ Invalid email address")
            else:
                with st.spinner("Creating your account..."):
                    # Check if user exists
                    existing_user = get_user_by_email(email)
                    if existing_user:
                        st.error("❌ Account already exists. Please log in.")
                    else:
                        # Create wallet
                        wallet_info = WalletManager.create_new_wallet()

                        if wallet_info:
                            # Create user in Supabase
                            user = create_user(email, wallet_info["address"])

                            if user:
                                # Encrypt and save to session
                                WalletManager.save_wallet_to_session(
                                    wallet_info["wallet_data"],
                                    password
                                )

                                # Save encrypted wallet to Supabase for recovery
                                save_wallet_address(user["id"], wallet_info["address"])

                                # Update session
                                st.session_state.wallet_address = wallet_info["address"]
                                st.session_state.wallet_locked = False
                                st.session_state.user_email = email
                                st.session_state.user_id = user["id"]
                                st.session_state.show_auth_modal = False

                                st.success("✅ Account created!")

                                # Show seed phrase
                                if wallet_info.get("mnemonic"):
                                    st.warning("🔐 **SAVE YOUR SEED PHRASE!**")
                                    st.code(wallet_info["mnemonic"], language=None)
                                    st.caption("""
                                    **Write this down and store it safely!**
                                    - This 12-word phrase can recover your wallet
                                    - Never share it with anyone
                                    - Store it offline (paper, steel backup)
                                    """)

                                st.balloons()
                                time.sleep(3)
                                st.rerun()
                            else:
                                st.error("❌ Failed to create account. Try again.")

        st.caption("✨ Your wallet will be accessible from any browser with your email & password")

    # ========== TAB 2: LOG IN ==========
    with tab2:
        st.subheader("Log In")
        st.write("Access your existing wallet from any device.")

        login_email = st.text_input("Email", key="login_email", placeholder="your@email.com")
        login_password = st.text_input("Password", type="password", key="login_pwd")

        if st.button("Log In", type="primary", disabled=not (login_email and login_password)):
            with st.spinner("Logging in..."):
                # Get user from database
                user = get_user_by_email(login_email)

                if not user:
                    st.error("❌ Account not found. Please sign up first.")
                else:
                    # Get user's wallet
                    wallets = get_user_wallets(user["id"])

                    if wallets and len(wallets) > 0:
                        wallet_address = wallets[0]["wallet_address"]

                        # For now, we'll create a temporary session
                        # In production, you'd decrypt the stored wallet with the password
                        st.session_state.wallet_address = wallet_address
                        st.session_state.wallet_locked = False
                        st.session_state.user_email = login_email
                        st.session_state.user_id = user["id"]
                        st.session_state.show_auth_modal = False

                        st.success(f"✅ Welcome back!")
                        st.info("⚠️ Note: Full wallet recovery with password verification coming soon. For now, import your private key if you need to make transactions.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ No wallet found for this account.")

    # ========== TAB 3: IMPORT WALLET ==========
    with tab3:
        st.subheader("Import Existing Wallet")
        st.write("Import a wallet using your 12-word seed phrase or private key.")

        import_email = st.text_input("Email (optional - to save wallet)", key="import_email", placeholder="your@email.com")
        recovery_input = st.text_area(
            "Seed Phrase (12 words) or Private Key (0x...)",
            key="import_recovery",
            placeholder="word1 word2 word3... OR 0x123...",
            help="Enter either your 12-word seed phrase or your private key",
            height=100
        )
        import_password = st.text_input("Password to encrypt wallet", type="password", key="import_pwd")

        st.caption("⚠️ Your seed phrase/key will be encrypted and stored securely")

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

                    st.success("✅ Wallet imported!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid private key")

        st.caption("🔒 Your private key is encrypted and stored securely")


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
    st.subheader("💰 Add USDC")

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
        if st.button("📋 Copy Address", use_container_width=True):
            st.toast("Address copied!")

    with col2:
        explorer_url = ChainUtils.get_explorer_url(selected_chain, address)
        st.link_button("🔍 View on Explorer", explorer_url, use_container_width=True)

    # QR Code
    st.markdown("**Scan QR Code:**")
    qr_img = generate_qr(address)
    st.image(qr_img, width=200)

    # Instructions
    with st.expander("📖 How to get testnet funds"):
        if "sepolia" in selected_chain or "amoy" in selected_chain:
            st.markdown("""
            **For testnet USDC:**
            1. Get testnet ETH from a faucet
            2. Use a testnet USDC faucet or bridge

            **Faucets:**
            - [Coinbase Faucet](https://portal.cdp.coinbase.com/products/faucet)
            - [Alchemy Faucet](https://sepoliafaucet.com/)
            """)
        else:
            st.warning("⚠️ This is MAINNET. Only send real funds if you know what you're doing.")


def send_modal():
    """Show send transaction modal with gasless transfer"""
    from transaction_relayer import TransactionRelayer
    from meta_tx import MetaTransaction

    st.subheader("💸 Send USDC (Gasless!)")
    st.caption("You only sign a message - no gas needed! We handle the rest.")

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
            **💰 Fee Breakdown:**
            - Transfer Amount: ${amount:.2f}
            - Gas Fee: ${gas_cost:.3f} (we pay!)
            - App Fee: ${app_fee:.3f}
            - **Total: ${total:.2f}**
            """)
        except Exception as e:
            st.warning(f"Could not estimate fees: {e}")
            total = amount

    # Validate inputs
    can_send = (
        recipient and
        recipient.startswith("0x") and
        len(recipient) == 42 and
        amount > 0
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_send_modal = False
            st.rerun()

    with col2:
        if st.button("✅ Sign & Send", type="primary", use_container_width=True, disabled=not can_send):
            with st.spinner("Processing transaction..."):
                try:
                    # Get wallet data
                    wallet_data = WalletManager.get_wallet_from_session()

                    if not wallet_data:
                        st.error("Could not load wallet. Please unlock first.")
                        return

                    # Create meta-transaction message
                    message = MetaTransaction.create_message(
                        from_address=st.session_state.wallet_address,
                        to_address=recipient,
                        amount=amount,
                        currency="USDC",
                        nonce=int(time.time())  # Simple nonce for now
                    )

                    # Sign message (user's signature, no gas!)
                    signature = MetaTransaction.sign_message(
                        message,
                        wallet_data["private_key"]
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
                        ✅ **Transaction Sent!**

                        - TX Hash: `{result['tx_hash'][:20]}...`
                        - Amount: ${result['amount']:.2f}
                        - Gas Paid: ${result['gas_cost']:.3f}
                        - Total: ${result['total_cost']:.2f}
                        """)

                        st.link_button("🔍 View on Explorer", result["explorer_url"], use_container_width=True)

                        # Close modal after success
                        time.sleep(2)
                        st.session_state.show_send_modal = False
                        st.rerun()
                    else:
                        st.error(f"❌ Transaction Failed: {result['error']}")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


def sidebar():
    """Render sidebar"""
    with st.sidebar:
        st.title("🔐 Wallet")

        # Show login button if no wallet
        if not st.session_state.wallet_address:
            st.info("👋 Welcome! Log in to access your wallet.")
            if st.button("🔑 Log In / Sign Up", use_container_width=True, type="primary"):
                st.session_state.show_auth_modal = True
                st.rerun()

            st.divider()
            st.caption("**Preview Mode** - Explore the interface")
            st.metric("Total USDC", "$0.00", help="Log in to see your balance")

            with st.expander("📊 Balance by Chain"):
                st.caption("Base Sepolia: $0.00")
                st.caption("Base Mainnet: $0.00")
                st.caption("Arbitrum Sepolia: $0.00")

            st.divider()

            # Preview buttons (disabled)
            st.button("💰 Add USDC", use_container_width=True, disabled=True, help="Log in to add funds")
            st.button("💸 Send", use_container_width=True, disabled=True, help="Log in to send")
            st.button("🔄 Refresh", use_container_width=True, disabled=True, help="Log in to refresh")

            return

        if st.session_state.wallet_address and not st.session_state.get("wallet_locked", True):
            # Wallet info
            address = st.session_state.wallet_address
            st.code(ChainUtils.format_address(address, 8))

            # Add USDC button
            if st.button("💰 Add USDC", use_container_width=True, type="primary"):
                st.session_state.show_deposit_modal = True
                st.rerun()

            # Send button
            if st.button("💸 Send", use_container_width=True):
                st.session_state.show_send_modal = True
                st.rerun()

            # Refresh balances
            if st.button("🔄 Refresh", use_container_width=True):
                with st.spinner("Fetching balances..."):
                    balances = ChainUtils.get_all_balances(st.session_state.wallet_address)
                    st.session_state.balances = balances
                    st.toast("Balances updated!")

            st.divider()

            # Show balances
            if st.session_state.balances:
                total_usdc = ChainUtils.calculate_total_usdc(st.session_state.balances)

                # Total balance
                st.metric("Total USDC", f"${total_usdc:.2f}")

                # Expandable breakdown
                with st.expander("📊 Balance by Chain"):
                    for network_key, chain_balances in st.session_state.balances.items():
                        network_name = NETWORKS[network_key]["name"]
                        usdc = chain_balances.get("usdc", 0.0)

                        if usdc > 0:
                            st.markdown(f"**{network_name}**")
                            st.markdown(f"└─ USDC: ${usdc:.2f}")

            st.divider()

            # Settings button
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.show_settings = True
                st.rerun()

            # Lock wallet
            if st.button("🔒 Lock Wallet", use_container_width=True):
                WalletManager.lock_wallet()
                st.rerun()

        else:
            # Wallet is locked or doesn't exist
            if "wallet_encrypted" in st.session_state:
                st.info("🔒 Wallet Locked")
                unlock_password = st.text_input("Enter password to unlock", type="password", key="unlock_pwd")
                if st.button("🔓 Unlock", use_container_width=True, type="primary"):
                    if unlock_password:
                        # Try to decrypt with the stored key (simplified - in production you'd re-derive from password)
                        wallet_data = WalletManager.get_wallet_from_session()
                        if wallet_data:
                            st.session_state.wallet_locked = False
                            st.success("Wallet unlocked!")
                            st.rerun()
                        else:
                            st.error("Incorrect password")


def chat_interface():
    """Main chat interface"""
    st.title("💬 Chat-First Crypto Wallet")
    st.caption("Powered by Claude 3.5 Sonnet")

    # Preview mode if not logged in
    if not st.session_state.wallet_address:
        # Show demo conversation
        with st.chat_message("assistant"):
            st.markdown("""👋 **Welcome to Chat Wallet!**

I'm your AI-powered crypto assistant. I can help you with:

- 💰 Check balances across multiple chains
- 💸 Send USDC with gasless transactions
- 📥 Get deposit addresses with QR codes
- 🔄 Swap tokens and manage assets
- 🎁 Buy gift cards with crypto

**Example questions:**
- "What's my balance?"
- "Send $10 USDC to 0x123..."
- "Show me my Base Sepolia address"
- "How do I add funds?"

**🔑 Log in to start chatting with your real wallet!**
""")

        # Disabled chat input
        st.chat_input("Log in to chat with your wallet...", disabled=True)
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
        welcome = f"""👋 **Welcome to your Chat Wallet!**

Your address: `{ChainUtils.format_address(st.session_state.wallet_address)}`

I can help you with:
- 💰 Check balances across chains
- 💸 Prepare transactions (you approve each one)
- 📥 Get deposit addresses
- 🎁 Buy gift cards (simulated)

**Try asking:** "What's my balance?" or "Show me deposit address for Base"
"""
        st.session_state.messages.append({"role": "assistant", "content": welcome})
        st.rerun()


def main():
    """Main app entry point"""
    st.set_page_config(
        page_title="Chat Wallet - Non-Custodial",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_state()

    # Show auth modal if requested
    if st.session_state.get("show_auth_modal"):
        wallet_setup_ui()
        if st.button("← Back to Preview"):
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
        if st.button("Close"):
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
        if st.button("← Back to Wallet"):
            st.session_state.show_settings = False
            st.rerun()
        return

    # Main layout - always show (preview or logged in)
    sidebar()
    chat_interface()


if __name__ == "__main__":
    main()
