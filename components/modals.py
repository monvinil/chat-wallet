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

        # V12 minimal numbered grid
        cols = st.columns(3)
        for i, word in enumerate(words):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="margin-bottom: 20px; text-align: center;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #444; margin-bottom: 4px;">{i+1:02d}</div>
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
            if st.button("I have saved this", type="primary", use_container_width=True):
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
            if st.button("Back", use_container_width=True):
                st.session_state._seed_verify_step = "show"
                for i in range(3):
                    if f"seed_verify_{i}" in st.session_state:
                        del st.session_state[f"seed_verify_{i}"]
                st.rerun()

        with col2:
            if st.button("Confirm", type="primary", use_container_width=True, disabled=not all_filled):
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
    """V12 deposit modal - centered void aesthetic"""
    st.markdown("<h2 style='text-align: center; font-weight: 300; margin-bottom: 20px;'>Deposit</h2>", unsafe_allow_html=True)

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

    selected_chain_name = st.selectbox("Network", list(chain_options.keys()), label_visibility="collapsed")
    selected_chain = chain_options[selected_chain_name]

    network = NETWORKS[selected_chain]

    # Get the correct address based on chain type
    if network["type"] == "solana":
        address = solana_address
        if not address:
            st.error("Solana address unavailable")
            return
    else:
        address = st.session_state.wallet_address

    # QR Code - centered
    qr_img = generate_qr(address)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_img, use_container_width=True)

    # Address display - minimal
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #888; letter-spacing: 0.02em; word-break: break-all;">
        {address}
    </div>
    """, unsafe_allow_html=True)

    # Network badge
    network_label = "Testnet" if network['testnet'] else "Mainnet"
    st.markdown(f"""
    <div style="display: flex; justify-content: center; gap: 10px; margin: 20px 0;">
        <span style="background: rgba(255,255,255,0.1); color: #888; font-size: 10px; padding: 4px 12px; border-radius: 10px; font-family: JetBrains Mono;">{network["type"].upper()}</span>
        <span style="background: {'rgba(255,255,255,0.05)' if network['testnet'] else 'white'}; color: {'#666' if network['testnet'] else 'black'}; font-size: 10px; padding: 4px 12px; border-radius: 10px; font-family: JetBrains Mono;">{network_label}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Copy", use_container_width=True):
            st.markdown(f'<script>navigator.clipboard.writeText("{address}");</script>', unsafe_allow_html=True)
            st.toast("Copied")

    with col2:
        if network["type"] == "solana":
            cluster_param = "?cluster=devnet" if network["testnet"] else ""
            explorer_url = f"{network['explorer']}/address/{address}{cluster_param}"
        else:
            explorer_url = ChainUtils.get_explorer_url(selected_chain, address)
        st.link_button("Explorer", explorer_url, use_container_width=True)

    # Faucet instructions
    if "sepolia" in selected_chain or "amoy" in selected_chain:
        with st.expander("Get testnet funds"):
            st.markdown("""
- [Coinbase Faucet](https://portal.cdp.coinbase.com/products/faucet)
- [Alchemy Faucet](https://sepoliafaucet.com/)
""")
    elif "solana-devnet" in selected_chain:
        with st.expander("Get testnet SOL"):
            st.markdown("""
- [Solana Faucet](https://faucet.solana.com/)
- CLI: `solana airdrop 2`
""")
    else:
        st.markdown("""
        <div style="color: #666; font-size: 12px; text-align: center; margin-top: 20px;">
            Mainnet — real funds only
        </div>
        """, unsafe_allow_html=True)

    # Show all addresses for multi-chain wallet
    if has_solana:
        with st.expander("All addresses"):
            st.markdown(f"""
            <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #555; margin-bottom: 4px;">EVM</div>
            """, unsafe_allow_html=True)
            st.code(st.session_state.wallet_address)
            st.markdown(f"""
            <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #555; margin-bottom: 4px; margin-top: 12px;">Solana</div>
            """, unsafe_allow_html=True)
            st.code(solana_address)


def _render_send_confirmation():
    """Render V12 send confirmation - centered void"""
    from transaction_relayer import TransactionRelayer
    from meta_tx import MetaTransaction
    from spending_limits import SpendingLimits
    import time

    details = st.session_state.get("_send_details", {})

    st.markdown("<h2 style='text-align: center; font-weight: 300; margin-bottom: 50px;'>Confirm</h2>", unsafe_allow_html=True)

    # V12 split display
    recipient = details.get('recipient', '')
    recipient_short = f"{recipient[:4]}...{recipient[-4:]}" if len(recipient) > 10 else recipient

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="text-align: right; border-right: 1px solid rgba(255,255,255,0.1); padding-right: 30px; height: 100%;">
            <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #555; margin-bottom: 8px;">SENDING</div>
            <div style="font-family: 'Inter'; font-size: 28px; font-weight: 300; color: white;">${details.get('total', 0):.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="padding-left: 30px;">
            <div style="font-family: 'JetBrains Mono'; font-size: 10px; color: #555; margin-bottom: 8px;">TO</div>
            <div style="font-family: 'Inter'; font-size: 28px; font-weight: 300; color: white;">{recipient_short}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

    # Confirm checkbox
    confirmed = st.checkbox("I confirm the recipient address is correct", key="send_confirm_checkbox")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state._send_confirm_step = False
            st.rerun()

    with col2:
        if st.button("Execute", type="primary", use_container_width=True, disabled=not confirmed):
            with st.spinner("Processing..."):
                try:
                    # Get stored transaction details
                    recipient = details.get("recipient")
                    amount = details.get("amount")
                    network_key = details.get("network_key")
                    total = details.get("total")

                    # Get wallet data
                    wallet_data = WalletManager.get_wallet_from_session()

                    if not wallet_data:
                        st.error("Wallet load failed")
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

                        show_success_animation()
                        st.markdown(f"""
<div style="text-align: center; padding: 30px 0;">
    <div style="font-family: 'JetBrains Mono'; font-size: 11px; color: #666; margin-bottom: 12px;">{result['tx_hash'][:20]}...</div>
    <div style="font-family: 'Inter'; font-size: 24px; font-weight: 300; color: white;">${result['amount']:.2f}</div>
</div>
""", unsafe_allow_html=True)
                        st.link_button("View on explorer", result["explorer_url"], use_container_width=True)

                        # Clean up and close modal
                        st.session_state._send_confirm_step = False
                        st.session_state._send_details = None
                        st.session_state.show_send_modal = False
                    else:
                        st.error(f"Failed: {result['error']}")

                except Exception as e:
                    from utils.logger import logger
                    logger.error(f"Send transaction failed: {str(e)}")
                    st.error("Transaction aborted")


def send_modal():
    """V12 send modal - void transfer"""
    from transaction_relayer import TransactionRelayer
    from spending_limits import check_spending_limit

    # Check if we're in confirmation step
    if st.session_state.get("_send_confirm_step"):
        _render_send_confirmation()
        return

    st.markdown("<h2 style='text-align: center; font-weight: 300;'>Transfer</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style="color: #555; font-size: 12px; text-align: center; margin-bottom: 30px;">
        Gas fees covered
    </div>
    """, unsafe_allow_html=True)

    # Network selector
    network_options = {
        "Base Sepolia (Testnet)": "base-sepolia",
    }
    selected_network = st.selectbox("Network", list(network_options.keys()), label_visibility="collapsed")
    network_key = network_options[selected_network]

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Recipient address
    recipient = st.text_input("Destination", placeholder="0x...", label_visibility="collapsed")

    # Amount
    amount = st.number_input("Amount USDC", min_value=0.01, step=0.01, format="%.2f", label_visibility="collapsed")

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
<div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px; margin: 20px 0; font-family: 'JetBrains Mono', monospace; font-size: 12px;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <span style="color: #555;">Amount</span>
        <span style="color: #aaa;">${amount:.2f}</span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <span style="color: #555;">Gas</span>
        <span style="color: #444;">${gas_cost:.3f} <span style="color: #888;">free</span></span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <span style="color: #555;">Fee</span>
        <span style="color: #aaa;">${app_fee:.3f}</span>
    </div>
    <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
        <span style="color: #888;">Total</span>
        <span style="color: white; font-weight: 500;">${total:.2f}</span>
    </div>
</div>
""", unsafe_allow_html=True)
        except Exception:
            pass

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
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_send_modal = False
            st.rerun()

    with col2:
        if st.button("Review", type="primary", use_container_width=True, disabled=not can_send):
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
