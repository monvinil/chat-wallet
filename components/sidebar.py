"""
Sidebar component for Chat Wallet
2026 Cyber-Physical Design - HUD Style
"""

import streamlit as st
from chain_utils import ChainUtils
from wallet_manager import WalletManager
from session_manager import SessionManager


def _get_solana_address_from_session() -> str:
    """Get Solana address from session state if available"""
    return st.session_state.get("solana_address", "")


def render_hud_status():
    """Render HUD-style system status indicator"""
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: rgba(0, 255, 157, 0.05);
        border: 1px solid rgba(0, 255, 157, 0.15);
        border-radius: 100px;
        margin-bottom: 16px;
    ">
        <div style="
            width: 6px;
            height: 6px;
            background: #00FF9D;
            border-radius: 50%;
            box-shadow: 0 0 8px #00FF9D;
            animation: pulse 2s ease-in-out infinite;
        "></div>
        <span style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.6875rem;
            color: #00FF9D;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        ">System Online</span>
    </div>
    <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
    """, unsafe_allow_html=True)


def render_balance_module(total_usdc: float):
    """Render balance as a HUD module"""
    # Format balance with proper decimals
    if total_usdc >= 1000:
        balance_display = f"{total_usdc:,.2f}"
    else:
        balance_display = f"{total_usdc:.2f}"

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(20, 25, 32, 0.9) 0%, rgba(15, 19, 24, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
    ">
        <!-- Top accent line -->
        <div style="
            position: absolute;
            top: 0;
            left: 20px;
            right: 20px;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.5), transparent);
        "></div>

        <!-- Label -->
        <div style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.6875rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #64748B;
            margin-bottom: 8px;
        ">Total Balance</div>

        <!-- Value -->
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 2rem;
            font-weight: 600;
            color: #F0F4F8;
            letter-spacing: -0.02em;
            font-variant-numeric: tabular-nums;
        ">
            <span style="color: #64748B; font-size: 1.5rem;">$</span>{balance_display}
        </div>

        <!-- Currency indicator -->
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            padding: 4px 10px;
            background: rgba(0, 212, 255, 0.08);
            border-radius: 100px;
        ">
            <span style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.6875rem;
                color: #00D4FF;
                letter-spacing: 0.05em;
            ">USDC</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_address_module(evm_address: str, solana_address: str = None):
    """Render addresses as a HUD module"""
    evm_short = ChainUtils.format_address(evm_address, 6)
    solana_short = ChainUtils.format_address(solana_address, 6) if solana_address else None

    with st.expander("Wallet Addresses", expanded=False):
        # EVM Address
        st.markdown("""
        <div style="
            font-size: 0.6875rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #64748B;
            margin-bottom: 6px;
        ">EVM Networks</div>
        """, unsafe_allow_html=True)
        st.code(evm_short, language=None)
        st.caption("Base, Arbitrum, Polygon")

        # Solana Address (if available)
        if solana_short:
            st.markdown("""
            <div style="
                font-size: 0.6875rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #64748B;
                margin-top: 12px;
                margin-bottom: 6px;
            ">Solana</div>
            """, unsafe_allow_html=True)
            st.code(solana_short, language=None)


def render_sidebar_footer():
    """Render footer with system info"""
    st.markdown("""
    <div style="
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.04);
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 8px;
        ">
            <div style="
                width: 4px;
                height: 4px;
                background: #00FF9D;
                border-radius: 50%;
            "></div>
            <span style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.6875rem;
                color: #475569;
            ">Non-custodial</span>
        </div>
        <span style="
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.6875rem;
            color: #334155;
        ">You control your keys</span>
    </div>
    """, unsafe_allow_html=True)


def render_transaction_history():
    """Render transaction history in sidebar"""
    user_id = st.session_state.get("user_id")

    # Guest users don't have persistent transaction history
    if not user_id or user_id.startswith("guest_"):
        return

    with st.expander("Recent Activity", expanded=False):
        try:
            from supabase_client import get_supabase_client, get_user_transactions

            client = get_supabase_client(use_service_key=True)
            if not client:
                st.caption("Unable to load")
                return

            transactions = get_user_transactions(client, user_id, limit=5)

            if not transactions:
                st.markdown("""
                <div style="
                    text-align: center;
                    padding: 20px 0;
                    color: #475569;
                    font-size: 0.75rem;
                ">No transactions yet</div>
                """, unsafe_allow_html=True)
                return

            for tx in transactions:
                tx_type = tx.get("type", "unknown")
                amount = float(tx.get("amount", 0))
                currency = tx.get("currency", "USD")
                status = tx.get("status", "pending")
                chain = tx.get("chain", "")
                tx_hash = tx.get("tx_hash")

                # Type styling
                is_incoming = tx_type == "deposit"
                color = "#00FF9D" if is_incoming else "#FF3D71"
                sign = "+" if is_incoming else "-"

                # Status indicator
                status_color = {
                    "confirmed": "#00FF9D",
                    "pending": "#FFB800",
                    "failed": "#FF3D71"
                }.get(status, "#64748B")

                st.markdown(f"""
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
                ">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="
                            width: 6px;
                            height: 6px;
                            background: {status_color};
                            border-radius: 50%;
                        "></div>
                        <span style="
                            font-family: 'JetBrains Mono', monospace;
                            font-size: 0.8125rem;
                            color: {color};
                            font-variant-numeric: tabular-nums;
                        ">{sign}${amount:.2f}</span>
                    </div>
                    <span style="
                        font-size: 0.6875rem;
                        color: #475569;
                        text-transform: uppercase;
                    ">{currency}</span>
                </div>
                """, unsafe_allow_html=True)

                # Explorer link
                if tx_hash and chain:
                    explorer_url = ChainUtils.get_tx_explorer_url(chain, tx_hash)
                    if explorer_url:
                        st.caption(f"[View on Explorer]({explorer_url})")

        except Exception:
            st.caption("Unable to load")


def sidebar():
    """Render sidebar with 2026 Cyber-Physical design"""
    with st.sidebar:
        # Show login prompt if no wallet
        if not st.session_state.wallet_address:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 32px 0;
            ">
                <div style="
                    font-family: 'Space Grotesk', sans-serif;
                    font-size: 0.8125rem;
                    color: #64748B;
                    margin-bottom: 16px;
                ">Already have an account?</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Sign Up / Sign In", use_container_width=True, type="primary"):
                st.session_state.show_auth_modal = True
                st.rerun()

            render_sidebar_footer()
            return

        # Wallet is connected and unlocked
        if st.session_state.wallet_address and not st.session_state.get("wallet_locked", True):
            # System status
            render_hud_status()

            # Balance module
            if st.session_state.balances:
                total_usdc = ChainUtils.calculate_total_usdc(st.session_state.balances)
                render_balance_module(total_usdc)
            else:
                render_balance_module(0.00)

            # Address module
            solana_addr = _get_solana_address_from_session()
            render_address_module(st.session_state.wallet_address, solana_addr)

            # Primary action buttons
            st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Deposit", use_container_width=True, type="primary"):
                    st.session_state.show_deposit_modal = True
                    st.rerun()
            with col2:
                if st.button("Send", use_container_width=True):
                    st.session_state.show_send_modal = True
                    st.rerun()

            # Transaction history
            st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
            render_transaction_history()

            # Secondary actions
            st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Settings", use_container_width=True):
                    st.session_state.show_settings = True
                    st.rerun()
            with col2:
                if st.button("Lock", use_container_width=True):
                    WalletManager.lock_wallet()
                    st.rerun()

            render_sidebar_footer()

        else:
            # Wallet is locked
            if "wallet_encrypted" in st.session_state:
                # Locked state indicator
                st.markdown("""
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 12px;
                    background: rgba(255, 184, 0, 0.08);
                    border: 1px solid rgba(255, 184, 0, 0.2);
                    border-radius: 100px;
                    margin-bottom: 16px;
                ">
                    <div style="
                        width: 6px;
                        height: 6px;
                        background: #FFB800;
                        border-radius: 50%;
                    "></div>
                    <span style="
                        font-family: 'JetBrains Mono', monospace;
                        font-size: 0.6875rem;
                        color: #FFB800;
                        text-transform: uppercase;
                        letter-spacing: 0.1em;
                    ">Locked</span>
                </div>
                """, unsafe_allow_html=True)

                # Address display
                st.markdown("""
                <div style="
                    font-size: 0.6875rem;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    color: #475569;
                    margin-bottom: 6px;
                ">Wallet</div>
                """, unsafe_allow_html=True)
                st.code(ChainUtils.format_address(st.session_state.wallet_address, 8))

                # Unlock form
                st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
                unlock_password = st.text_input("Password", type="password", key="unlock_pwd", placeholder="Enter password")

                if st.button("Unlock", use_container_width=True, type="primary"):
                    if unlock_password:
                        if WalletManager.unlock_wallet_with_password(unlock_password):
                            st.success("Unlocked")
                            st.rerun()
                        else:
                            st.error("Incorrect password")
                            st.caption("Forgot? Use your recovery phrase to restore.")

                st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

                # Secondary actions when locked
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Settings", use_container_width=True):
                        st.session_state.show_settings = True
                        st.rerun()
                with col2:
                    if st.button("Log out", use_container_width=True):
                        SessionManager.logout()
                        st.rerun()

                render_sidebar_footer()

            elif st.session_state.get("wallet_address"):
                st.caption("Import your wallet to continue")
                st.code(ChainUtils.format_address(st.session_state.wallet_address))

                if st.button("Import Wallet", use_container_width=True, type="primary"):
                    st.session_state.show_auth_modal = True
                    st.rerun()

                render_sidebar_footer()
