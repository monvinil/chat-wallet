"""
Modal components for Chat Wallet
2026 Cyber-Physical Design - Modular Widget Style
"""

import random
import streamlit as st
import qrcode
from io import BytesIO

from config import NETWORKS
from wallet_manager import WalletManager
from chain_utils import ChainUtils


def generate_qr(data: str):
    """Generate QR code with dark theme"""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    # Dark theme QR - cyan on void
    img = qr.make_image(fill_color="#00D4FF", back_color="#0A0D14")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def show_success_animation():
    """Show HUD-style success animation with cyber-physical aesthetic"""
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

    @keyframes success-pulse {
        0%, 100% { box-shadow: 0 0 40px rgba(0, 255, 157, 0.4); }
        50% { box-shadow: 0 0 60px rgba(0, 255, 157, 0.6); }
    }

    @keyframes particle-rise {
        0% { transform: translateY(0) scale(1); opacity: 1; }
        100% { transform: translateY(-100px) scale(0); opacity: 0; }
    }

    .success-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(2, 4, 8, 0.95);
        backdrop-filter: blur(20px);
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
        background: linear-gradient(145deg, #00FF9D 0%, #00D4FF 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
        animation: success-checkmark 0.5s ease-out, success-pulse 2s ease-in-out infinite;
    }

    .success-icon svg {
        width: 40px;
        height: 40px;
        stroke: #020408;
        stroke-width: 3;
        fill: none;
    }

    .success-ring {
        position: absolute;
        width: 100px;
        height: 100px;
        border: 1px solid rgba(0, 255, 157, 0.3);
        border-radius: 50%;
        animation: success-ring 0.6s ease-out;
    }

    .success-ring-outer {
        position: absolute;
        width: 120px;
        height: 120px;
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 50%;
        animation: success-ring 0.8s ease-out;
    }

    .success-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #00FF9D;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        margin-top: 24px;
    }

    .particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: #00FF9D;
        border-radius: 50%;
        animation: particle-rise 1.5s ease-out forwards;
    }

    .particle:nth-child(1) { left: 30%; animation-delay: 0s; }
    .particle:nth-child(2) { left: 40%; animation-delay: 0.1s; background: #00D4FF; }
    .particle:nth-child(3) { left: 50%; animation-delay: 0.2s; }
    .particle:nth-child(4) { left: 60%; animation-delay: 0.15s; background: #00D4FF; }
    .particle:nth-child(5) { left: 70%; animation-delay: 0.25s; }
    </style>

    <div class="success-overlay" id="successOverlay">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="success-content">
            <div style="position: relative; display: inline-flex; align-items: center; justify-content: center;">
                <div class="success-ring-outer"></div>
                <div class="success-ring"></div>
                <div class="success-icon">
                    <svg viewBox="0 0 24 24">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
            </div>
            <div class="success-text">Transaction Complete</div>
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


def render_modal_header(title: str, subtitle: str = None):
    """Render HUD-style modal header"""
    st.markdown(f"""
    <div style="
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        ">
            <div style="
                width: 3px;
                height: 24px;
                background: linear-gradient(180deg, #00D4FF, #00FF9D);
                border-radius: 2px;
            "></div>
            <h2 style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.5rem;
                font-weight: 600;
                color: #F0F4F8;
                margin: 0;
                letter-spacing: -0.02em;
            ">{title}</h2>
        </div>
        {"<p style='font-family: Space Grotesk, sans-serif; font-size: 0.875rem; color: #64748B; margin: 0; padding-left: 15px;'>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def render_warning_banner(message: str):
    """Render HUD-style warning banner"""
    st.markdown(f"""
    <div style="
        background: rgba(255, 184, 0, 0.08);
        border: 1px solid rgba(255, 184, 0, 0.2);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 20px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    ">
        <div style="
            width: 20px;
            height: 20px;
            background: rgba(255, 184, 0, 0.15);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            margin-top: 2px;
        ">
            <span style="color: #FFB800; font-size: 0.75rem;">⚠</span>
        </div>
        <p style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.875rem;
            color: #FFB800;
            margin: 0;
            line-height: 1.5;
        ">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def seed_phrase_modal():
    """
    Full-page modal for seed phrase display and verification after signup.
    User must verify 3 random words before proceeding.
    HUD-style 2026 Cyber-Physical design.
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

    render_modal_header("Recovery Phrase", "Your wallet's master key")

    if st.session_state.get("_seed_verify_step") == "show":
        render_warning_banner("Write this down and store it securely. This is the only way to recover your wallet if you lose access.")

        # Display words in HUD-style grid
        st.markdown("""
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.6875rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #64748B;
            margin-bottom: 12px;
        ">12-Word Recovery Phrase</div>
        """, unsafe_allow_html=True)

        # Build grid HTML for words
        word_html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 20px;">'
        for i, word in enumerate(words):
            word_html += f"""
            <div style="
                background: rgba(10, 13, 20, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                padding: 12px;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <span style="
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.6875rem;
                    color: #475569;
                    min-width: 20px;
                ">{i+1:02d}</span>
                <span style="
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.875rem;
                    color: #F0F4F8;
                    font-weight: 500;
                ">{word}</span>
            </div>
            """
        word_html += '</div>'
        st.markdown(word_html, unsafe_allow_html=True)

        # Copyable code block
        with st.expander("Copy as text", expanded=False):
            st.code(mnemonic, language=None)

        st.markdown("""
        <p style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.75rem;
            color: #475569;
            margin: 16px 0;
        ">You'll verify 3 words in the next step to confirm you've saved your phrase.</p>
        """, unsafe_allow_html=True)

        if st.button("I've written it down", type="primary", use_container_width=True):
            st.session_state._seed_verify_step = "verify"
            st.rerun()

    elif st.session_state.get("_seed_verify_step") == "verify":
        st.markdown("""
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.6875rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #64748B;
            margin-bottom: 16px;
        ">Verify Your Phrase</div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <p style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.875rem;
            color: #94A3B8;
            margin-bottom: 20px;
        ">Enter the requested words to confirm you've saved your phrase.</p>
        """, unsafe_allow_html=True)

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

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

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
    """Show deposit address modal with HUD-style multi-chain support"""
    render_modal_header("Deposit", "Receive funds to your wallet")

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

    # Network selector label
    st.markdown("""
    <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748B;
        margin-bottom: 6px;
    ">Select Network</div>
    """, unsafe_allow_html=True)

    selected_chain_name = st.selectbox("Network", list(chain_options.keys()), label_visibility="collapsed")
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

    # Network status indicator
    is_testnet = network['testnet']
    status_color = "#FFB800" if is_testnet else "#00FF9D"
    status_text = "TESTNET" if is_testnet else "MAINNET"
    chain_type = network["type"].upper()

    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 16px 0;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(0, 212, 255, 0.08);
            border: 1px solid rgba(0, 212, 255, 0.15);
            border-radius: 100px;
        ">
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.625rem;
                color: #00D4FF;
                letter-spacing: 0.05em;
            ">{chain_type}</span>
        </div>
        <div style="
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba({status_color}, 0.08);
            border: 1px solid rgba({status_color}, 0.2);
            border-radius: 100px;
        ">
            <div style="
                width: 5px;
                height: 5px;
                background: {status_color};
                border-radius: 50%;
            "></div>
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.625rem;
                color: {status_color};
                letter-spacing: 0.05em;
            ">{status_text}</span>
        </div>
    </div>
    """.replace("rgba(#FFB800", "rgba(255, 184, 0").replace("rgba(#00FF9D", "rgba(0, 255, 157"), unsafe_allow_html=True)

    # Address display module
    st.markdown("""
    <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748B;
        margin-bottom: 8px;
    ">Deposit Address</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        background: rgba(10, 13, 20, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    ">
        <code style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: #F0F4F8;
            word-break: break-all;
            line-height: 1.6;
        ">{address}</code>
    </div>
    """, unsafe_allow_html=True)

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

    # QR Code with HUD styling
    st.markdown("""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px;
        margin-top: 16px;
        background: rgba(10, 13, 20, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
    ">
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.625rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #475569;
            margin-bottom: 12px;
        ">Scan to Deposit</div>
    """, unsafe_allow_html=True)

    qr_img = generate_qr(address)
    st.image(qr_img, width=160)

    st.markdown("</div>", unsafe_allow_html=True)

    # Instructions based on network
    if "sepolia" in selected_chain or "amoy" in selected_chain:
        with st.expander("Get testnet funds", expanded=False):
            st.markdown("""
Get testnet tokens from these faucets:
- [Coinbase Faucet](https://portal.cdp.coinbase.com/products/faucet)
- [Alchemy Faucet](https://sepoliafaucet.com/)
""")
    elif "solana-devnet" in selected_chain:
        with st.expander("Get testnet SOL", expanded=False):
            st.markdown("""
Get testnet SOL from:
- [Solana Faucet](https://faucet.solana.com/)
- Or use CLI: `solana airdrop 2`
""")
    else:
        render_warning_banner("This is mainnet. Only deposit real funds you can afford to lose.")

    # Show both addresses if multi-chain wallet
    if has_solana:
        with st.expander("All deposit addresses", expanded=False):
            st.markdown("""
            <div style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.625rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #64748B;
                margin-bottom: 6px;
            ">EVM Networks</div>
            """, unsafe_allow_html=True)
            st.code(st.session_state.wallet_address)

            st.markdown("""
            <div style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.625rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #64748B;
                margin: 12px 0 6px 0;
            ">Solana</div>
            """, unsafe_allow_html=True)
            st.code(solana_address)


def _render_send_confirmation():
    """Render HUD-style send confirmation step"""
    from transaction_relayer import TransactionRelayer
    from meta_tx import MetaTransaction
    from spending_limits import SpendingLimits
    import time

    details = st.session_state.get("_send_details", {})

    render_modal_header("Confirm Transaction", "Review and authorize")

    render_warning_banner("Please review carefully. Transactions cannot be reversed.")

    # Transaction summary module
    recipient = details.get('recipient', '')
    amount = details.get('amount', 0)
    total = details.get('total', 0)
    network_name = details.get('network_name', '')

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(10, 13, 20, 0.9) 0%, rgba(5, 8, 12, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    ">
        <!-- Recipient -->
        <div style="margin-bottom: 16px;">
            <div style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.625rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #64748B;
                margin-bottom: 6px;
            ">Recipient</div>
            <code style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.75rem;
                color: #F0F4F8;
                word-break: break-all;
            ">{recipient}</code>
        </div>

        <!-- Amount Row -->
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-top: 1px solid rgba(255, 255, 255, 0.04);
        ">
            <span style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.875rem;
                color: #94A3B8;
            ">Amount</span>
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 1rem;
                color: #F0F4F8;
                font-variant-numeric: tabular-nums;
            ">${amount:.2f} <span style="color: #64748B; font-size: 0.75rem;">USDC</span></span>
        </div>

        <!-- Network Row -->
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-top: 1px solid rgba(255, 255, 255, 0.04);
        ">
            <span style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.875rem;
                color: #94A3B8;
            ">Network</span>
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8125rem;
                color: #00D4FF;
            ">{network_name}</span>
        </div>

        <!-- Total Row -->
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0 0 0;
            border-top: 1px solid rgba(0, 255, 157, 0.15);
            margin-top: 8px;
        ">
            <span style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.875rem;
                color: #F0F4F8;
                font-weight: 500;
            ">Total</span>
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 1.25rem;
                color: #00FF9D;
                font-weight: 600;
                font-variant-numeric: tabular-nums;
            ">${total:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Confirm checkbox
    confirmed = st.checkbox("I confirm this is the correct recipient address", key="send_confirm_checkbox")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

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

                        show_success_animation()

                        # Success display
                        st.markdown(f"""
                        <div style="
                            background: rgba(0, 255, 157, 0.08);
                            border: 1px solid rgba(0, 255, 157, 0.2);
                            border-radius: 8px;
                            padding: 16px;
                            margin-top: 16px;
                        ">
                            <div style="
                                font-family: 'JetBrains Mono', monospace;
                                font-size: 0.75rem;
                                color: #00FF9D;
                                margin-bottom: 12px;
                            ">✓ Transaction Complete</div>
                            <div style="
                                font-family: 'JetBrains Mono', monospace;
                                font-size: 0.6875rem;
                                color: #64748B;
                            ">
                                Hash: {result['tx_hash'][:20]}...<br>
                                Amount: ${result['amount']:.2f}<br>
                                Fee: ${result['gas_cost']:.3f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

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
    """Show HUD-style send transaction modal with gasless transfer"""
    from transaction_relayer import TransactionRelayer
    from spending_limits import check_spending_limit

    # Check if we're in confirmation step
    if st.session_state.get("_send_confirm_step"):
        _render_send_confirmation()
        return

    render_modal_header("Send USDC", "Gasless transfer")

    # Gasless indicator
    st.markdown("""
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: rgba(0, 255, 157, 0.08);
        border: 1px solid rgba(0, 255, 157, 0.15);
        border-radius: 100px;
        margin-bottom: 20px;
    ">
        <div style="
            width: 6px;
            height: 6px;
            background: #00FF9D;
            border-radius: 50%;
        "></div>
        <span style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.625rem;
            color: #00FF9D;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        ">Network Fees Covered</span>
    </div>
    """, unsafe_allow_html=True)

    # Network selector
    st.markdown("""
    <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748B;
        margin-bottom: 6px;
    ">Network</div>
    """, unsafe_allow_html=True)

    network_options = {
        "Base Sepolia (Testnet)": "base-sepolia",
    }
    selected_network = st.selectbox("Network", list(network_options.keys()), label_visibility="collapsed")
    network_key = network_options[selected_network]

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # Recipient address
    st.markdown("""
    <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748B;
        margin-bottom: 6px;
    ">Recipient Address</div>
    """, unsafe_allow_html=True)

    recipient = st.text_input("Recipient Address", placeholder="0x...", label_visibility="collapsed")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # Amount
    st.markdown("""
    <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6875rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #64748B;
        margin-bottom: 6px;
    ">Amount (USDC)</div>
    """, unsafe_allow_html=True)

    amount = st.number_input("Amount (USDC)", min_value=0.01, step=0.01, format="%.2f", label_visibility="collapsed")

    # Estimate fees
    total = amount
    gas_cost = 0
    app_fee = 0
    if amount > 0:
        try:
            relayer = TransactionRelayer(network_key)
            gas_cost, app_fee = relayer.estimate_gas_cost(amount)
            total = amount + gas_cost + app_fee

            # Fee breakdown module
            st.markdown(f"""
            <div style="
                background: rgba(10, 13, 20, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 8px;
                padding: 16px;
                margin-top: 16px;
            ">
                <div style="
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.625rem;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    color: #64748B;
                    margin-bottom: 12px;
                ">Fee Breakdown</div>

                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-family: 'Space Grotesk', sans-serif; font-size: 0.8125rem; color: #94A3B8;">Amount</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8125rem; color: #F0F4F8; font-variant-numeric: tabular-nums;">${amount:.2f}</span>
                </div>

                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-family: 'Space Grotesk', sans-serif; font-size: 0.8125rem; color: #94A3B8;">Network fee</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8125rem; color: #00FF9D; font-variant-numeric: tabular-nums;">${gas_cost:.3f} <span style="color: #475569; font-size: 0.625rem;">COVERED</span></span>
                </div>

                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span style="font-family: 'Space Grotesk', sans-serif; font-size: 0.8125rem; color: #94A3B8;">Service fee</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8125rem; color: #F0F4F8; font-variant-numeric: tabular-nums;">${app_fee:.3f}</span>
                </div>

                <div style="
                    display: flex;
                    justify-content: space-between;
                    padding-top: 12px;
                    border-top: 1px solid rgba(0, 212, 255, 0.15);
                ">
                    <span style="font-family: 'Space Grotesk', sans-serif; font-size: 0.875rem; color: #F0F4F8; font-weight: 500;">Total</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 1rem; color: #00D4FF; font-weight: 600; font-variant-numeric: tabular-nums;">${total:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
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
                    render_warning_banner("Address checksum mismatch. Please verify this is correct.")
            except ValueError:
                recipient_error = "Invalid address format"

    if recipient and not valid_recipient:
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 12px;
            background: rgba(255, 61, 113, 0.08);
            border: 1px solid rgba(255, 61, 113, 0.2);
            border-radius: 6px;
            margin-top: 12px;
        ">
            <span style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.8125rem;
                color: #FF3D71;
            ">{recipient_error}</span>
        </div>
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

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

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
