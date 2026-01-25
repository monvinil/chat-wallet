"""
Modal components for Chat Wallet
V8 "The Spec Sheet" - Product Spec Aesthetic
"""

import random
import streamlit as st
import qrcode
from io import BytesIO

from config import NETWORKS
from wallet_manager import WalletManager
from chain_utils import ChainUtils


def generate_qr(data: str):
    """Generate QR code with V8 thin border"""
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def show_success_animation():
    """Show V8 style success animation"""
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

    .success-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(5, 5, 5, 0.95);
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
        border-radius: 0;
        background: #ccff00;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
        animation: success-checkmark 0.5s ease-out;
    }

    .success-icon svg {
        width: 40px;
        height: 40px;
        stroke: black;
        stroke-width: 3;
        fill: none;
    }

    .success-ring {
        position: absolute;
        width: 100px;
        height: 100px;
        border: 2px solid rgba(204, 255, 0, 0.3);
        animation: success-ring 0.6s ease-out;
    }

    .success-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #ccff00;
        letter-spacing: 0.1em;
        margin-top: 20px;
    }
    </style>

    <div class="success-overlay" id="successOverlay">
        <div class="success-content">
            <div style="position: relative; display: inline-block;">
                <div class="success-ring"></div>
                <div class="success-icon">
                    <svg viewBox="0 0 24 24">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
            </div>
            <div class="success-label">EXECUTION_COMPLETE</div>
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
    """
    V8 seed phrase modal - "PRIVATE_KEY_GENERATION"
    """
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

    st.markdown("### PRIVATE_KEY_GENERATION")

    if st.session_state.get("_seed_verify_step") == "show":
        st.warning("DO NOT SHARE. OFFLINE STORAGE ONLY.")

        st.markdown("---")

        # V8 numbered grid display
        cols = st.columns(3)
        for i, word in enumerate(words):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="
                    border: 1px solid #333;
                    padding: 10px;
                    margin-bottom: 8px;
                    background: #0A0A0A;
                ">
                    <div style="font-size: 9px; color: #525252; font-family: 'JetBrains Mono', monospace;">{i+1:02d}</div>
                    <div style="font-family: 'Inter', sans-serif; font-weight: 600; font-size: 14px; color: white;">{word}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Copyable text
        with st.expander("COPY_AS_TEXT"):
            st.code(mnemonic, language=None)

        st.caption("VERIFICATION_REQUIRED: 3 WORDS IN NEXT STEP")

        if st.button("CONFIRM SECURE STORAGE", type="primary", use_container_width=True):
            st.session_state._seed_verify_step = "verify"
            st.rerun()

    elif st.session_state.get("_seed_verify_step") == "verify":
        st.markdown("#### IDENTITY_VERIFICATION")
        st.caption("Enter the requested words to confirm backup.")

        all_correct = True
        user_inputs = []

        for i, idx in enumerate(indices):
            word_num = idx + 1
            user_input = st.text_input(
                f"WORD_{word_num:02d}",
                key=f"seed_verify_{i}",
                placeholder=f"Enter word {word_num}"
            ).strip().lower()
            user_inputs.append(user_input)

            if user_input and user_input != words[idx].lower():
                all_correct = False

        all_filled = all(u for u in user_inputs)

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("SHOW_PHRASE", use_container_width=True):
                st.session_state._seed_verify_step = "show"
                for i in range(3):
                    if f"seed_verify_{i}" in st.session_state:
                        del st.session_state[f"seed_verify_{i}"]
                st.rerun()

        with col2:
            if st.button("AUTHENTICATE", type="primary", use_container_width=True, disabled=not all_filled):
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
                    st.error("MISMATCH_DETECTED")


def deposit_modal():
    """V8 deposit modal - "INBOUND_TRANSFER" with shipping label aesthetic"""
    st.markdown("### INBOUND_TRANSFER")

    # Get wallet data to check for Solana address
    wallet_data = WalletManager.get_wallet_from_session()
    has_solana = wallet_data and wallet_data.get("solana")
    solana_address = wallet_data.get("solana", {}).get("address") if has_solana else None

    # Fallback: check session state directly (for guest wallets before decryption)
    if not solana_address and st.session_state.get("solana_address"):
        solana_address = st.session_state.solana_address
        has_solana = True

    # Chain selector - include Solana if wallet has it
    chain_options = {
        "Base Sepolia (Testnet)": "base-sepolia",
        "Base Mainnet": "base-mainnet",
        "Arbitrum Sepolia (Testnet)": "arbitrum-sepolia",
        "Polygon Amoy (Testnet)": "polygon-amoy",
    }

    # Add Solana options if wallet supports it
    if has_solana:
        chain_options["Solana Devnet (Testnet)"] = "solana-devnet"
        chain_options["Solana Mainnet"] = "solana-mainnet"

    selected_chain_name = st.selectbox("NETWORK", list(chain_options.keys()))
    selected_chain = chain_options[selected_chain_name]

    network = NETWORKS[selected_chain]

    # Get the correct address based on chain type
    if network["type"] == "solana":
        address = solana_address
        if not address:
            st.error("SOLANA_ADDR_UNAVAILABLE")
            return
    else:
        address = st.session_state.wallet_address

    # V8 "Shipping Label" Address Display
    st.markdown(f"""
    <div style="
        margin-top: 20px;
        padding: 20px;
        background: white;
        color: black;
        text-align: center;
        margin-bottom: 20px;
    ">
        <div style="font-size: 10px; font-weight: 800; font-family: 'Inter', sans-serif; margin-bottom: 6px;">SCAN FOR ROUTING</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; word-break: break-all; margin-bottom: 12px;">
            {address}
        </div>
        <div style="height: 2px; width: 100%; background: black;"></div>
    </div>
    """, unsafe_allow_html=True)

    # QR Code
    qr_img = generate_qr(address)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_img, width=180)

    # Chain type badge
    chain_type = network["type"].upper()
    network_label = "TESTNET" if network['testnet'] else "MAINNET"

    st.markdown(f"""
    <div style="display: flex; justify-content: center; gap: 10px; margin-top: 15px;">
        <span style="background: #1a1a1a; color: #999; font-size: 9px; padding: 4px 8px; font-family: JetBrains Mono;">{chain_type}</span>
        <span style="background: {'#333' if network['testnet'] else '#ccff00'}; color: {'#999' if network['testnet'] else 'black'}; font-size: 9px; padding: 4px 8px; font-family: JetBrains Mono; font-weight: 600;">{network_label}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        # Copy button
        if st.button("COPY_ADDR", use_container_width=True):
            st.markdown(f'<script>navigator.clipboard.writeText("{address}");</script>', unsafe_allow_html=True)
            st.toast("Copied")

    with col2:
        # Explorer link
        if network["type"] == "solana":
            cluster_param = "?cluster=devnet" if network["testnet"] else ""
            explorer_url = f"{network['explorer']}/address/{address}{cluster_param}"
        else:
            explorer_url = ChainUtils.get_explorer_url(selected_chain, address)
        st.link_button("VIEW_EXPLORER", explorer_url, use_container_width=True)

    # Faucet instructions
    if "sepolia" in selected_chain or "amoy" in selected_chain:
        with st.expander("GET_TESTNET_FUNDS"):
            st.markdown("""
- [Coinbase Faucet](https://portal.cdp.coinbase.com/products/faucet)
- [Alchemy Faucet](https://sepoliafaucet.com/)
""")
    elif "solana-devnet" in selected_chain:
        with st.expander("GET_TESTNET_SOL"):
            st.markdown("""
- [Solana Faucet](https://faucet.solana.com/)
- CLI: `solana airdrop 2`
""")
    else:
        st.warning("MAINNET: REAL FUNDS ONLY")

    # Show all addresses for multi-chain wallet
    if has_solana:
        with st.expander("ALL_ADDRESSES"):
            st.markdown("""
<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; margin-bottom: 4px;">EVM_CHAINS</div>
""", unsafe_allow_html=True)
            st.code(st.session_state.wallet_address)
            st.markdown("""
<div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; margin-bottom: 4px; margin-top: 8px;">SOLANA</div>
""", unsafe_allow_html=True)
            st.code(solana_address)


def _render_send_confirmation():
    """Render V8 send confirmation - "EXECUTION_ORDER" """
    from transaction_relayer import TransactionRelayer
    from meta_tx import MetaTransaction
    from spending_limits import SpendingLimits
    import time

    details = st.session_state.get("_send_details", {})

    st.markdown("### EXECUTION_ORDER")

    # V8 Confirmation Card with volt border
    recipient = details.get('recipient', '')
    recipient_short = f"{recipient[:6]}...{recipient[-4:]}" if len(recipient) > 10 else recipient

    st.markdown(f"""
    <div style="
        background: #0A0A0A;
        border: 1px solid #ccff00;
        padding: 20px;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 20px;
    ">
        <div style="color: #ccff00; font-size: 9px; margin-bottom: 12px; letter-spacing: 0.1em;">STATUS: PENDING_SIGNATURE</div>

        <div style="display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 10px;">
            <span style="color: #666; font-size: 11px;">AMOUNT</span>
            <span style="color: white; font-size: 12px;">${details.get('amount', 0):.2f} USDC</span>
        </div>

        <div style="display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 10px;">
            <span style="color: #666; font-size: 11px;">SERVICE_FEE</span>
            <span style="color: white; font-size: 12px;">${details.get('app_fee', 0):.3f}</span>
        </div>

        <div style="display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 10px;">
            <span style="color: #666; font-size: 11px;">TOTAL</span>
            <span style="color: #ccff00; font-size: 12px; font-weight: 600;">${details.get('total', 0):.2f}</span>
        </div>

        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span style="color: #666; font-size: 11px;">DESTINATION</span>
            <span style="color: white; font-size: 11px;">{recipient_short}</span>
        </div>

        <div style="display: flex; justify-content: space-between;">
            <span style="color: #666; font-size: 11px;">NETWORK</span>
            <span style="color: white; font-size: 11px;">BASE_MAINNET</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Confirm checkbox
    confirmed = st.checkbox("I CONFIRM RECIPIENT ADDRESS IS CORRECT", key="send_confirm_checkbox")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("ABORT", use_container_width=True):
            st.session_state._send_confirm_step = False
            st.rerun()

    with col2:
        if st.button("SIGN & EXECUTE", type="primary", use_container_width=True, disabled=not confirmed):
            with st.spinner("PROCESSING..."):
                try:
                    # Get stored transaction details
                    recipient = details.get("recipient")
                    amount = details.get("amount")
                    network_key = details.get("network_key")
                    total = details.get("total")

                    # Get wallet data
                    wallet_data = WalletManager.get_wallet_from_session()

                    if not wallet_data:
                        st.error("WALLET_LOAD_FAILED")
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
                        nonce=int(time.time() * 1000)
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
                        # Record spend for daily tracking
                        user_id = st.session_state.get("user_id")
                        if user_id:
                            SpendingLimits.record_spend(user_id, total)

                        # Invalidate balance cache so UI refreshes
                        ChainUtils.invalidate_balance_cache(st.session_state.wallet_address)

                        show_success_animation()
                        st.markdown(f"""
<div style="background: #0A0A0A; border: 1px solid #333; padding: 15px; font-family: 'JetBrains Mono', monospace;">
    <div style="color: #ccff00; font-size: 9px; margin-bottom: 10px;">EXECUTION_COMPLETE</div>
    <div style="color: #666; font-size: 10px;">TX_HASH</div>
    <div style="color: white; font-size: 11px; margin-bottom: 8px;">{result['tx_hash'][:20]}...</div>
    <div style="color: #666; font-size: 10px;">AMOUNT</div>
    <div style="color: white; font-size: 11px;">${result['amount']:.2f}</div>
</div>
""", unsafe_allow_html=True)
                        st.link_button("VIEW_ON_EXPLORER", result["explorer_url"], use_container_width=True)

                        # Clean up and close modal
                        st.session_state._send_confirm_step = False
                        st.session_state._send_details = None
                        st.session_state.show_send_modal = False
                    else:
                        st.error(f"EXECUTION_FAILED: {result['error']}")

                except Exception as e:
                    from utils.logger import logger
                    logger.error(f"Send transaction failed: {str(e)}")
                    st.error("TRANSACTION_ABORTED")


def send_modal():
    """V8 send modal - "OUTBOUND_TRANSFER" """
    from transaction_relayer import TransactionRelayer
    from spending_limits import check_spending_limit

    # Check if we're in confirmation step
    if st.session_state.get("_send_confirm_step"):
        _render_send_confirmation()
        return

    st.markdown("### OUTBOUND_TRANSFER")
    st.caption("GASLESS_EXECUTION: NETWORK FEES COVERED")

    # Network selector
    network_options = {
        "Base Sepolia (Testnet)": "base-sepolia",
    }
    selected_network = st.selectbox("NETWORK", list(network_options.keys()))
    network_key = network_options[selected_network]

    # Recipient address
    recipient = st.text_input("DESTINATION_ADDR", placeholder="0x...")

    # Amount
    amount = st.number_input("QUANTITY (USDC)", min_value=0.01, step=0.01, format="%.2f")

    # Estimate fees
    total = amount
    gas_cost = 0
    app_fee = 0
    if amount > 0:
        try:
            relayer = TransactionRelayer(network_key)
            gas_cost, app_fee = relayer.estimate_gas_cost(amount)
            total = amount + gas_cost + app_fee

            st.markdown(f"""
<div style="background: #0A0A0A; border: 1px solid #1a1a1a; padding: 12px; margin: 10px 0; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: #666;">AMOUNT</span>
        <span style="color: white;">${amount:.2f}</span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: #666;">NETWORK_FEE</span>
        <span style="color: #525252;">${gas_cost:.3f} <span style="color: #ccff00;">COVERED</span></span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <span style="color: #666;">SERVICE_FEE</span>
        <span style="color: white;">${app_fee:.3f}</span>
    </div>
    <div style="display: flex; justify-content: space-between; border-top: 1px solid #333; padding-top: 6px;">
        <span style="color: #999;">TOTAL</span>
        <span style="color: #ccff00; font-weight: 600;">${total:.2f}</span>
    </div>
</div>
""", unsafe_allow_html=True)
        except Exception:
            st.caption("FEE_ESTIMATION_UNAVAILABLE")
            total = amount

    # Validate inputs with EIP-55 checksum
    valid_recipient = False
    recipient_error = ""
    checksummed_recipient = None

    if recipient:
        if not recipient.startswith("0x"):
            recipient_error = "ADDR_MUST_START_WITH_0x"
        elif len(recipient) != 42:
            recipient_error = "ADDR_LENGTH_INVALID"
        else:
            try:
                from web3 import Web3
                checksummed_recipient = Web3.to_checksum_address(recipient)
                valid_recipient = True

                if recipient != checksummed_recipient and recipient.lower() != recipient:
                    st.warning("CHECKSUM_MISMATCH: VERIFY ADDRESS")
            except ValueError:
                recipient_error = "ADDR_FORMAT_INVALID"

    if recipient and not valid_recipient:
        st.warning(recipient_error)

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

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("CANCEL", use_container_width=True):
            st.session_state.show_send_modal = False
            st.rerun()

    with col2:
        if st.button("PREPARE_ORDER →", type="primary", use_container_width=True, disabled=not can_send):
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
