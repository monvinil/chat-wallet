"""
Modal components for Chat Wallet
Deposit, Send, and Seed Phrase modals
"""

import random
import streamlit as st
import qrcode
from io import BytesIO

from config import NETWORKS
from wallet_manager import WalletManager
from chain_utils import ChainUtils


def generate_qr(data: str):
    """Generate QR code"""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


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


def seed_phrase_modal():
    """
    Full-page modal for seed phrase display and verification after signup.
    User must verify 3 random words before proceeding.
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

    st.title("Save Your Recovery Phrase")

    if st.session_state.get("_seed_verify_step") == "show":
        st.warning("**Write this down and store it securely.** This is the only way to recover your wallet if you forget your password or lose access to your account.")

        st.markdown("---")

        # Display words in a grid
        st.markdown("#### Your 12-word recovery phrase:")
        cols = st.columns(3)
        for i, word in enumerate(words):
            with cols[i % 3]:
                st.markdown(f"**{i+1}.** {word}")

        st.markdown("---")

        # Also show as copyable code block
        with st.expander("Copy as text"):
            st.code(mnemonic, language=None)

        st.caption("You'll need to verify 3 words in the next step to confirm you've saved your phrase.")

        if st.button("I've written it down", type="primary", use_container_width=True):
            st.session_state._seed_verify_step = "verify"
            st.rerun()

    elif st.session_state.get("_seed_verify_step") == "verify":
        st.markdown("#### Verify your recovery phrase")
        st.caption("Enter the requested words to confirm you've saved your phrase.")

        all_correct = True
        user_inputs = []

        for i, idx in enumerate(indices):
            word_num = idx + 1
            user_input = st.text_input(
                f"Word #{word_num}",
                key=f"seed_verify_{i}",
                placeholder=f"Enter word {word_num}"
            ).strip().lower()
            user_inputs.append(user_input)

            if user_input and user_input != words[idx].lower():
                all_correct = False

        all_filled = all(u for u in user_inputs)

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Show phrase again", use_container_width=True):
                st.session_state._seed_verify_step = "show"
                # Clear inputs
                for i in range(3):
                    if f"seed_verify_{i}" in st.session_state:
                        del st.session_state[f"seed_verify_{i}"]
                st.rerun()

        with col2:
            if st.button("Verify", type="primary", use_container_width=True, disabled=not all_filled):
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
                    st.error("One or more words are incorrect. Please check your recovery phrase.")


def deposit_modal():
    """Show deposit address modal with multi-chain support"""
    st.markdown("### Deposit")

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

    selected_chain_name = st.selectbox("Network", list(chain_options.keys()))
    selected_chain = chain_options[selected_chain_name]

    network = NETWORKS[selected_chain]

    # Get the correct address based on chain type
    if network["type"] == "solana":
        address = solana_address
        if not address:
            st.error("Solana address not available. Try importing your wallet with a seed phrase.")
            return
    else:
        address = st.session_state.wallet_address

    # Network indicator
    if network['testnet']:
        st.caption(f"{network['name']} (Testnet)")
    else:
        st.caption(f"{network['name']} (Mainnet)")

    # Show chain type badge
    chain_type = network["type"].upper()
    st.markdown(f"**Chain:** {chain_type}")

    # Address
    st.code(address)

    col1, col2 = st.columns([1, 1])

    with col1:
        # Copy button with JavaScript clipboard integration
        copy_js = f"""
        <script>
        function copyAddress() {{
            navigator.clipboard.writeText("{address}");
        }}
        </script>
        """
        st.components.v1.html(copy_js, height=0)
        if st.button("Copy address", use_container_width=True):
            # Also set in session for JS to work
            st.markdown(f'<script>navigator.clipboard.writeText("{address}");</script>', unsafe_allow_html=True)
            st.toast("Copied to clipboard")

    with col2:
        # Build explorer URL based on chain type
        if network["type"] == "solana":
            cluster_param = "?cluster=devnet" if network["testnet"] else ""
            explorer_url = f"{network['explorer']}/address/{address}{cluster_param}"
        else:
            explorer_url = ChainUtils.get_explorer_url(selected_chain, address)
        st.link_button("View on explorer", explorer_url, use_container_width=True)

    # QR Code
    st.divider()
    qr_img = generate_qr(address)
    st.image(qr_img, width=180)

    # Instructions based on network
    if "sepolia" in selected_chain or "amoy" in selected_chain:
        with st.expander("Get testnet funds"):
            st.markdown("""
Get testnet tokens from these faucets:
- [Coinbase Faucet](https://portal.cdp.coinbase.com/products/faucet)
- [Alchemy Faucet](https://sepoliafaucet.com/)
""")
    elif "solana-devnet" in selected_chain:
        with st.expander("Get testnet SOL"):
            st.markdown("""
Get testnet SOL from:
- [Solana Faucet](https://faucet.solana.com/)
- Or use CLI: `solana airdrop 2`
""")
    else:
        st.warning("This is mainnet. Only deposit real funds.")

    # Show both addresses if multi-chain wallet
    if has_solana:
        with st.expander("All deposit addresses"):
            st.markdown("**EVM (Base, Arbitrum, Polygon):**")
            st.code(st.session_state.wallet_address)
            st.markdown("**Solana:**")
            st.code(solana_address)


def _render_send_confirmation():
    """Render send confirmation step"""
    from transaction_relayer import TransactionRelayer
    from meta_tx import MetaTransaction
    from spending_limits import SpendingLimits
    import time

    details = st.session_state.get("_send_details", {})

    st.markdown("### Confirm Transaction")
    st.warning("Please review carefully before sending.")

    # Show transaction summary
    st.markdown(f"""
**Sending to:**
`{details.get('recipient', '')}`

**Amount:** ${details.get('amount', 0):.2f} USDC
**Network:** {details.get('network_name', '')}
**Total (with fees):** ${details.get('total', 0):.2f}
""")

    # Confirm checkbox
    confirmed = st.checkbox("I confirm this is the correct recipient address", key="send_confirm_checkbox")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Back", use_container_width=True):
            st.session_state._send_confirm_step = False
            st.rerun()

    with col2:
        if st.button("Send Now", type="primary", use_container_width=True, disabled=not confirmed):
            with st.spinner("Processing transaction..."):
                try:
                    # Get stored transaction details
                    recipient = details.get("recipient")
                    amount = details.get("amount")
                    network_key = details.get("network_key")
                    total = details.get("total")

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

                        st.success("Transaction complete")
                        st.markdown(f"""
- Hash: `{result['tx_hash'][:20]}...`
- Amount: ${result['amount']:.2f}
- Fee: ${result['gas_cost']:.3f}
""")
                        st.link_button("View on explorer", result["explorer_url"], use_container_width=True)

                        # Clean up and close modal
                        st.session_state._send_confirm_step = False
                        st.session_state._send_details = None
                        st.session_state.show_send_modal = False
                    else:
                        st.error(f"Transaction failed: {result['error']}")

                except Exception as e:
                    from utils.logger import logger
                    logger.error(f"Send transaction failed: {str(e)}")
                    st.error("Transaction could not be completed. Please try again.")


def send_modal():
    """Show send transaction modal with gasless transfer and confirmation"""
    from transaction_relayer import TransactionRelayer
    from spending_limits import check_spending_limit

    # Check if we're in confirmation step
    if st.session_state.get("_send_confirm_step"):
        _render_send_confirmation()
        return

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
    total = amount
    gas_cost = 0
    app_fee = 0
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
        except Exception:
            st.caption("Could not estimate fees")
            total = amount

    # Validate inputs with EIP-55 checksum
    valid_recipient = False
    recipient_error = ""
    checksummed_recipient = None

    if recipient:
        if not recipient.startswith("0x"):
            recipient_error = "Address must start with 0x"
        elif len(recipient) != 42:
            recipient_error = "Address must be 42 characters"
        else:
            # Check if valid hex and validate/convert checksum
            try:
                from web3 import Web3
                # This validates the address and returns checksummed version
                checksummed_recipient = Web3.to_checksum_address(recipient)
                valid_recipient = True

                # Warn if user entered non-checksummed address (potential typo risk)
                if recipient != checksummed_recipient and recipient.lower() != recipient:
                    st.warning("Address checksum mismatch. Please verify this is correct.")
            except ValueError:
                recipient_error = "Invalid address format"

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
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_send_modal = False
            st.rerun()

    with col2:
        if st.button("Review", type="primary", use_container_width=True, disabled=not can_send):
            # Store transaction details for confirmation step (use checksummed address)
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
