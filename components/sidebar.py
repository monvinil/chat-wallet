"""
Sidebar component for Chat Wallet
V3 "Opinionated Luxury" - Cyber-Physical Design System
"""

import streamlit as st
from chain_utils import ChainUtils
from wallet_manager import WalletManager
from session_manager import SessionManager


def _get_solana_address_from_session() -> str:
    """Get Solana address from session state if available"""
    return st.session_state.get("solana_address", "")


def render_sidebar_header():
    """Render V3 workspace header"""
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
                    letter-spacing: 0.15em; color: #52525b; text-transform: uppercase;">
            WORKSPACE
        </div>
        <div style="font-size: 1rem; font-weight: 500; color: #e4e4e7; margin-top: 0.25rem;">
            Personal Wallet
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_card(is_active: bool):
    """Render keystore status card with appropriate styling"""
    if is_active:
        st.markdown("""
        <div style="background: rgba(163, 230, 53, 0.08); border: 1px solid rgba(163, 230, 53, 0.25);
                    border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem;
                    display: flex; align-items: center; gap: 0.6rem;">
            <span style="width: 8px; height: 8px; background: #a3e635; border-radius: 50%;
                         box-shadow: 0 0 12px rgba(163, 230, 53, 0.6);"></span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
                         letter-spacing: 0.1em; color: #a3e635; text-transform: uppercase;">
                KEYSTORE ACTIVE
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25);
                    border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem;
                    display: flex; align-items: center; gap: 0.6rem;">
            <span style="width: 8px; height: 8px; background: #ef4444; border-radius: 50%;
                         box-shadow: 0 0 12px rgba(239, 68, 68, 0.6);"></span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
                         letter-spacing: 0.1em; color: #ef4444; text-transform: uppercase;">
                KEYSTORE LOCKED
            </span>
        </div>
        """, unsafe_allow_html=True)


def render_balance_display(total_usdc: float):
    """Render V3 balance display with large monospace numbers"""
    st.markdown(f"""
    <div style="margin-bottom: 1.25rem;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
                    letter-spacing: 0.15em; color: #52525b; text-transform: uppercase; margin-bottom: 0.5rem;">
            NET EQUITY
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 600;
                    color: #e4e4e7; letter-spacing: -0.02em;">
            ${total_usdc:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_footer():
    """Render V3 footer - trust indicators"""
    st.markdown("""
    <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.06);">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.55rem;
                    letter-spacing: 0.1em; color: #3f3f46; text-transform: uppercase; text-align: center;">
            NON-CUSTODIAL KEYSTORE
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.55rem;
                    letter-spacing: 0.1em; color: #3f3f46; text-transform: uppercase; text-align: center; margin-top: 0.25rem;">
            ENCRYPTED LOCALLY
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_transaction_history():
    """Render V3 transaction history with styled rows"""
    user_id = st.session_state.get("user_id")

    if not user_id or user_id.startswith("guest_"):
        return

    with st.expander("TRANSACTIONS", expanded=False):
        try:
            from supabase_client import get_supabase_client, get_user_transactions

            client = get_supabase_client(use_service_key=True)
            if not client:
                st.caption("Unable to load")
                return

            transactions = get_user_transactions(client, user_id, limit=5)

            if not transactions:
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #52525b;">
                    No transactions yet
                </div>
                """, unsafe_allow_html=True)
                return

            for tx in transactions:
                tx_type = tx.get("type", "unknown")
                amount = float(tx.get("amount", 0))
                currency = tx.get("currency", "USD")
                status = tx.get("status", "pending")
                chain = tx.get("chain", "")

                # Arrow indicators
                arrow = "↓" if tx_type == "deposit" else "↑"
                arrow_color = "#a3e635" if tx_type == "deposit" else "#71717a"

                # Status styling
                status_color = "#a3e635" if status == "confirmed" else "#eab308" if status == "pending" else "#ef4444"

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: {arrow_color}; font-size: 0.875rem;">{arrow}</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #e4e4e7;">
                            ${amount:.2f}
                        </span>
                    </div>
                    <span style="width: 6px; height: 6px; background: {status_color}; border-radius: 50%;"></span>
                </div>
                """, unsafe_allow_html=True)

                tx_hash = tx.get("tx_hash")
                if tx_hash and chain:
                    explorer_url = ChainUtils.get_tx_explorer_url(chain, tx_hash)
                    if explorer_url:
                        st.markdown(f"""
                        <a href="{explorer_url}" target="_blank" style="font-family: 'JetBrains Mono', monospace;
                           font-size: 0.6rem; color: #52525b; text-decoration: none;">
                            VIEW →
                        </a>
                        """, unsafe_allow_html=True)

        except Exception:
            st.caption("Unable to load")


def sidebar():
    """Render V3 sidebar"""
    with st.sidebar:
        render_sidebar_header()

        # No wallet - show login
        if not st.session_state.wallet_address:
            st.markdown("""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
                        color: #71717a; margin-bottom: 1rem;">
                Connect to initialize session
            </div>
            """, unsafe_allow_html=True)

            if st.button("SIGN IN", use_container_width=True, type="primary"):
                st.session_state.show_auth_modal = True
                st.rerun()

            render_sidebar_footer()
            return

        # Wallet exists and unlocked
        if st.session_state.wallet_address and not st.session_state.get("wallet_locked", True):
            render_status_card(is_active=True)

            # Balance display
            if st.session_state.balances:
                total_usdc = ChainUtils.calculate_total_usdc(st.session_state.balances)
            else:
                total_usdc = 0.0
            render_balance_display(total_usdc)

            # Addresses
            solana_addr = _get_solana_address_from_session()

            with st.expander("ADDRESSES", expanded=False):
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
                            letter-spacing: 0.1em; color: #52525b; margin-bottom: 0.25rem;">
                    EVM
                </div>
                """, unsafe_allow_html=True)
                st.code(ChainUtils.format_address(st.session_state.wallet_address, 8))
                if solana_addr:
                    st.markdown("""
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
                                letter-spacing: 0.1em; color: #52525b; margin-bottom: 0.25rem; margin-top: 0.5rem;">
                        SOLANA
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(ChainUtils.format_address(solana_addr, 8))

            # Primary actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("DEPOSIT", use_container_width=True, type="primary"):
                    st.session_state.show_deposit_modal = True
                    st.rerun()
            with col2:
                if st.button("SEND", use_container_width=True):
                    st.session_state.show_send_modal = True
                    st.rerun()

            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

            # Transaction history
            render_transaction_history()

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

            # Secondary actions
            if st.button("SETTINGS", use_container_width=True):
                st.session_state.show_settings = True
                st.rerun()

            if st.button("LOCK SESSION", use_container_width=True):
                WalletManager.lock_wallet()
                st.rerun()

            render_sidebar_footer()

        else:
            # Wallet is locked
            if "wallet_encrypted" in st.session_state:
                render_status_card(is_active=False)

                st.markdown(f"""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
                            color: #71717a; margin-bottom: 0.5rem;">
                    {ChainUtils.format_address(st.session_state.wallet_address, 8)}
                </div>
                """, unsafe_allow_html=True)

                unlock_password = st.text_input("Password", type="password", key="unlock_pwd",
                                                 label_visibility="collapsed", placeholder="Enter password")

                if st.button("UNLOCK", use_container_width=True, type="primary"):
                    if unlock_password:
                        if WalletManager.unlock_wallet_with_password(unlock_password):
                            st.rerun()
                        else:
                            st.error("Incorrect password")

                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

                if st.button("SETTINGS", use_container_width=True):
                    st.session_state.show_settings = True
                    st.rerun()

                if st.button("TERMINATE SESSION", use_container_width=True):
                    SessionManager.logout()
                    st.rerun()

                render_sidebar_footer()

            elif st.session_state.get("wallet_address"):
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
                            color: #71717a; margin-bottom: 1rem;">
                    Import wallet to continue
                </div>
                """, unsafe_allow_html=True)
                st.code(ChainUtils.format_address(st.session_state.wallet_address))

                if st.button("IMPORT WALLET", use_container_width=True, type="primary"):
                    st.session_state.show_auth_modal = True
                    st.rerun()

                render_sidebar_footer()
