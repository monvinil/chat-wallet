"""
Modal components for Chat Wallet
V12 "Liquid Silver" - The Void Modals
"""

import random
import streamlit as st
import qrcode
from io import BytesIO

from config import NETWORKS
from wallet_manager import WalletManager
from chain_utils import ChainUtils
from rate_limiter import RateLimiter


def generate_qr(data: str):
    """Generate QR code - minimal border"""
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color="transparent")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def show_success_animation():
    """Show V12 minimal success animation"""
    st.markdown("""
    <style>
    @keyframes success-fade {
        0% { opacity: 0; transform: scale(0.9); }
        100% { opacity: 1; transform: scale(1); }
    }

    .success-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(5, 5, 5, 0.98);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: success-fade 0.3s ease;
    }

    .success-content {
        text-align: center;
    }

    .success-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 24px;
    }

    .success-icon svg {
        width: 28px;
        height: 28px;
        stroke: black;
        stroke-width: 2.5;
        fill: none;
    }

    .success-label {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 300;
        color: white;
        letter-spacing: -0.02em;
    }
    </style>

    <div class="success-overlay" id="successOverlay">
        <div class="success-content">
            <div class="success-icon">
                <svg viewBox="0 0 24 24">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <div class="success-label">Complete</div>
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


def seed_phrase_modal():
    """V12 seed phrase modal - centered void aesthetic"""
    RateLimiter.update_activity()  # Keep session active during modal
    mnemonic = st.session_state.get("_pending_seed_phrase", "")
    if not mnemonic:
        st.session_state.show_seed_phrase_modal = False
        st.rerun()
        return

    words = mnemonic.split()

    # Initialize verification state if not set
    if "_seed_verify_indices" not in st.session_state:
        indices = sorted(random.sample(range(len(words)), 3))
        st.session_state._seed_verify_indices = indices
        st.session_state._seed_verify_step = "show"

    indices = st.session_state._seed_verify_indices

    st.markdown("<h2 style='text-align: center; font-weight: 300; margin-bottom: 40px;'>Private Key</h2>", unsafe_allow_html=True)

    if st.session_state.get("_seed_verify_step") == "show":
        st.markdown("""
        <div style="color: #666; font-size: 13px; text-align: center; margin-bottom: 30px;">
            Write these words down. Never share them.
        </div>
        """, unsafe_allow_html=True)

        # V12 minimal numbered grid (2 columns for mobile-friendly)
        cols = st.columns(2)
        for i, word in enumerate(words):
            with cols[i % 2]:
                st.markdown(f"""
                <div style="margin-bottom: 16px; text-align: center;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #444; margin-bottom: 4px;">{i+1:02d}</div>
                    <div style="font-family: 'Inter', sans-serif; font-weight: 400; font-size: 15px; color: white;">{word}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

        # Copyable text
        with st.expander("Copy as text"):
            st.code(mnemonic, language=None)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("SAVED", type="primary", use_container_width=True):
                st.session_state._seed_verify_step = "verify"
                st.rerun()

    elif st.session_state.get("_seed_verify_step") == "verify":
        st.markdown("""
        <div style="color: #666; font-size: 13px; text-align: center; margin-bottom: 30px;">
            Verify your backup by entering 3 words
        </div>
        """, unsafe_allow_html=True)

        all_correct = True
        user_inputs = []

        for i, idx in enumerate(indices):
            word_num = idx + 1
            user_input = st.text_input(
                f"Word {word_num}",
                key=f"seed_verify_{i}",
                placeholder=f"Enter word {word_num}"
            ).strip().lower()
            user_inputs.append(user_input)

            if user_input and user_input != words[idx].lower():
                all_correct = False

        all_filled = all(u for u in user_inputs)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("BACK", use_container_width=True):
                st.session_state._seed_verify_step = "show"
                for i in range(3):
                    if f"seed_verify_{i}" in st.session_state:
                        del st.session_state[f"seed_verify_{i}"]
                st.rerun()

        with col2:
            if st.button("CONFIRM", type="primary", use_container_width=True, disabled=not all_filled):
                if all_correct:
                    # Clean up state
                    st.session_state._seed_verify_indices = None
                    st.session_state._seed_verify_step = None
                    st.session_state._pending_seed_phrase = None
                    st.session_state.show_seed_phrase_modal = False
                    st.session_state.onboarding_step = 1
                    st.session_state.onboarding_complete = False
                    st.session_state.just_signed_up = True
                    st.rerun()
                else:
                    st.error("Words don't match")


def deposit_modal():
    """V12 deposit modal - shows both addresses upfront"""
    RateLimiter.update_activity()  # Keep session active during modal
    st.markdown("<h2 style='text-align: center; font-weight: 300; margin-bottom: 8px;'>Deposit</h2>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; font-size: 12px; color: #555; margin-bottom: 24px;'>Send USDC to your wallet address</div>", unsafe_allow_html=True)

    # Get wallet addresses
    evm_address = st.session_state.wallet_address
    wallet_data = WalletManager.get_wallet_from_session()
    solana_address = wallet_data.get("solana", {}).get("address") if wallet_data and wallet_data.get("solana") else None

    # Fallback for guest wallets
    if not solana_address and st.session_state.get("solana_address"):
        solana_address = st.session_state.solana_address

    # Track which address is selected for QR
    if "_deposit_view" not in st.session_state:
        st.session_state._deposit_view = "evm"

    # === EVM ADDRESS SECTION ===
    st.markdown("""
    <div style="font-family: JetBrains Mono; font-size: 11px; color: #666; margin-bottom: 8px; letter-spacing: 0.1em;">
        EVM ADDRESS <span style="color: #444;">(Base, Arbitrum, Polygon)</span>
    </div>
    """, unsafe_allow_html=True)
    st.code(evm_address, language=None)

    # === SOLANA ADDRESS SECTION (if available) ===
    if solana_address:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: JetBrains Mono; font-size: 11px; color: #666; margin-bottom: 8px; letter-spacing: 0.1em;">
            SOLANA ADDRESS
        </div>
        """, unsafe_allow_html=True)
        st.code(solana_address, language=None)

    # === QR CODE SECTION ===
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # QR toggle if both addresses exist
    if solana_address:
        qr_tabs = st.radio(
            "Show QR for",
            ["EVM", "Solana"],
            horizontal=True,
            label_visibility="collapsed",
            key="qr_address_type"
        )
        qr_address = evm_address if qr_tabs == "EVM" else solana_address
    else:
        qr_address = evm_address

    # QR Code - centered
    qr_img = generate_qr(qr_address)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_img, use_container_width=True)

    # === NETWORK SELECTOR (for explorer link) ===
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    with st.expander("Network details", expanded=False):
        # All supported networks
        network_options = {
            "Ethereum": "eth-mainnet",
            "Base": "base-mainnet",
            "Arbitrum": "arbitrum-mainnet",
        }

        if solana_address:
            network_options["Solana"] = "solana-mainnet"

        # Testnets
        network_options["Ethereum Sepolia (Testnet)"] = "eth-sepolia"
        network_options["Arc (Testnet)"] = "arc-testnet"

        selected_chain = st.selectbox(
            "Network",
            list(network_options.keys()),
            label_visibility="collapsed",
            key="deposit_network_select"
        )

        network_key = network_options[selected_chain]
        network = NETWORKS[network_key]

        # Explorer link
        if network["type"] == "solana":
            explorer_url = f"{network['explorer']}/address/{solana_address}"
        else:
            explorer_url = ChainUtils.get_explorer_url(network_key, evm_address)

        st.link_button("VIEW ON EXPLORER", explorer_url, use_container_width=True)

        # Faucet instructions for testnets
        if network["testnet"]:
            st.markdown("""
<div style="font-size: 11px; color: #555; margin-top: 12px;">
    <strong style="color: #666;">Get testnet funds:</strong><br>
    • <a href="https://faucet.circle.com/" target="_blank" style="color: #888;">Circle USDC Faucet</a><br>
    • <a href="https://sepoliafaucet.com/" target="_blank" style="color: #888;">Alchemy Faucet</a>
</div>
            """, unsafe_allow_html=True)


def _render_send_confirmation():
    """Render V12 send confirmation - centered void"""
    from direct_tx import get_direct_executor
    from spending_limits import SpendingLimits

    details = st.session_state.get("_send_details", {})

    st.markdown("<h2 style='text-align: center; font-weight: 300; margin-bottom: 50px;'>Confirm</h2>", unsafe_allow_html=True)

    # V12 split display
    recipient = details.get('recipient', '')
    recipient_short = f"{recipient[:4]}...{recipient[-4:]}" if len(recipient) > 10 else recipient

    # Mobile-friendly stacked layout
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 24px;">
        <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #555; margin-bottom: 8px;">SENDING</div>
        <div style="font-family: 'Inter'; font-size: 32px; font-weight: 300; color: white;">${details.get('amount', 0):.2f}</div>
    </div>
    <div style="text-align: center;">
        <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #555; margin-bottom: 8px;">TO</div>
        <div style="font-family: 'Inter'; font-size: 18px; font-weight: 300; color: white;">{recipient_short}</div>
    </div>
    <div style="text-align: center; margin-top: 16px;">
        <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #444;">
            on {details.get('network_name', 'Arc Testnet')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    # Confirm checkbox
    confirmed = st.checkbox("I confirm the recipient address is correct", key="send_confirm_checkbox")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("CANCEL", use_container_width=True):
            st.session_state._send_confirm_step = False
            st.rerun()

    with col2:
        if st.button("EXECUTE", type="primary", use_container_width=True, disabled=not confirmed):
            with st.spinner("Signing & broadcasting..."):
                try:
                    # Get stored transaction details
                    recipient = details.get("recipient")
                    amount = details.get("amount")
                    network_key = details.get("network_key")
                    total = details.get("total")

                    # Get wallet data with private key
                    wallet_data = WalletManager.get_wallet_from_session()

                    if not wallet_data:
                        st.error("Wallet locked. Please unlock to send.")
                        return

                    private_key = wallet_data.get("private_key") or wallet_data.get("evm", {}).get("private_key")
                    if not private_key:
                        st.error("Could not access private key")
                        return

                    # Execute direct transfer (user signs, user pays gas)
                    executor = get_direct_executor(network_key)
                    user_id = st.session_state.get("user_id")

                    result = executor.execute_transfer(
                        private_key=private_key,
                        to_address=recipient,
                        amount_usdc=amount,
                        user_id=user_id
                    )

                    if result["success"]:
                        show_success_animation()
                        st.markdown(f"""
<div style="text-align: center; padding: 30px 0;">
    <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #22c55e; margin-bottom: 8px;">SENT</div>
    <div style="font-family: 'Inter'; font-size: 28px; font-weight: 300; color: white; margin-bottom: 16px;">${result['amount']:.2f} USDC</div>
    <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #555;">{result['tx_hash'][:16]}...{result['tx_hash'][-8:]}</div>
</div>
""", unsafe_allow_html=True)
                        st.link_button("VIEW ON EXPLORER", result["explorer_url"], use_container_width=True)

                        # Clean up and close modal after delay
                        import time
                        time.sleep(2)
                        st.session_state._send_confirm_step = False
                        st.session_state._send_details = None
                        st.session_state.show_send_modal = False
                    else:
                        st.error(f"Failed: {result['error']}")

                except Exception as e:
                    from utils.logger import logger
                    logger.error(f"Send transaction failed: {str(e)}")
                    st.error(f"Transaction failed: {str(e)}")


def send_modal():
    """V12 send modal - void transfer"""
    RateLimiter.update_activity()  # Keep session active during modal
    from direct_tx import get_direct_executor
    from spending_limits import check_spending_limit

    # Check if we're in confirmation step
    if st.session_state.get("_send_confirm_step"):
        _render_send_confirmation()
        return

    st.markdown("<h2 style='text-align: center; font-weight: 300;'>Transfer</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style="color: #555; font-size: 12px; text-align: center; margin-bottom: 30px;">
        Send USDC to any address
    </div>
    """, unsafe_allow_html=True)

    # Network selector - Arc testnet first for MVP
    network_options = {
        "Arc (Testnet)": "arc-testnet",
        "Ethereum Sepolia (Testnet)": "eth-sepolia",
        "Base": "base-mainnet",
        "Ethereum": "eth-mainnet",
        "Arbitrum": "arbitrum-mainnet",
    }
    selected_network = st.selectbox("Network", list(network_options.keys()), label_visibility="collapsed")
    network_key = network_options[selected_network]

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Recipient address
    recipient = st.text_input("Destination", placeholder="0x...", label_visibility="collapsed")

    # Amount
    amount = st.number_input("Amount USDC", min_value=0.01, step=0.01, format="%.2f", label_visibility="collapsed")

    # Estimate fees using direct executor
    total = amount
    gas_cost = 0.0
    app_fee = 0.0
    if amount > 0 and st.session_state.get("wallet_address"):
        try:
            executor = get_direct_executor(network_key)
            fees = executor.estimate_fee_usd(
                st.session_state.wallet_address,
                recipient or "0x0000000000000000000000000000000000000000",
                amount
            )
            gas_cost = fees["gas_cost_usd"]
            app_fee = fees["app_fee"]
            total = amount + app_fee  # Gas shown separately

            # Check if testnet (free gas)
            is_testnet = NETWORKS.get(network_key, {}).get("testnet", False)
            gas_label = "free" if is_testnet else f"${gas_cost:.3f}"

            st.markdown(f"""
<div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px; margin: 20px 0; font-family: 'JetBrains Mono', monospace; font-size: 12px;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <span style="color: #555;">Amount</span>
        <span style="color: #aaa;">${amount:.2f}</span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <span style="color: #555;">Network fee</span>
        <span style="color: #22c55e;">{gas_label}</span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <span style="color: #555;">Service fee</span>
        <span style="color: #aaa;">${app_fee:.3f}</span>
    </div>
    <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
        <span style="color: #888;">Total</span>
        <span style="color: white; font-weight: 500;">${total:.2f}</span>
    </div>
</div>
""", unsafe_allow_html=True)
        except Exception as e:
            from utils.logger import logger
            logger.warning(f"Fee estimation failed: {e}")

    # Validate inputs with EIP-55 checksum
    valid_recipient = False
    recipient_error = ""
    checksummed_recipient = None

    if recipient:
        if not recipient.startswith("0x"):
            recipient_error = "Address must start with 0x"
        elif len(recipient) != 42:
            recipient_error = "Invalid address length"
        else:
            try:
                from web3 import Web3
                checksummed_recipient = Web3.to_checksum_address(recipient)
                valid_recipient = True

                if recipient != checksummed_recipient and recipient.lower() != recipient:
                    st.markdown("""
                    <div style="color: #666; font-size: 11px; margin: 10px 0;">Checksum mismatch — verify address</div>
                    """, unsafe_allow_html=True)
            except ValueError:
                recipient_error = "Invalid address format"

    if recipient and not valid_recipient:
        st.markdown(f"""
        <div style="color: #888; font-size: 11px; margin: 10px 0;">{recipient_error}</div>
        """, unsafe_allow_html=True)

    # Check spending limits
    user_id = st.session_state.get("user_id")
    spending_blocked = False
    spending_message = None

    if user_id and amount > 0:
        can_proceed, msg = check_spending_limit(user_id, total, "USDC transfer")
        if not can_proceed:
            spending_blocked = True
            spending_message = msg
            st.error(msg)

    can_send = valid_recipient and amount > 0 and not spending_blocked

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("CANCEL", use_container_width=True):
            st.session_state.show_send_modal = False
            st.rerun()

    with col2:
        if st.button("REVIEW", type="primary", use_container_width=True, disabled=not can_send):
            # Store transaction details for confirmation step
            st.session_state._send_confirm_step = True
            st.session_state._send_details = {
                "recipient": checksummed_recipient or recipient,
                "amount": amount,
                "total": total,
                "gas_cost": gas_cost,
                "app_fee": app_fee,
                "network_key": network_key,
                "network_name": selected_network
            }
            st.rerun()
