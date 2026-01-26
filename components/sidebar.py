"""
Sidebar component for Chat Wallet
V12 "Liquid Silver" - The Spine
"""

import streamlit as st
from chain_utils import ChainUtils
from wallet_manager import WalletManager
from session_manager import SessionManager


def _get_solana_address_from_session() -> str:
    """Get Solana address from session state if available"""
    return st.session_state.get("solana_address", "")


def render_sidebar_header():
    """Render V12 minimal header"""
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <div style="font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 300;
                    letter-spacing: -0.02em; color: white;">
            Chat02
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_card(is_active: bool):
    """Render V12 floating status text"""
    if is_active:
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px;
                         color: #fff; background: rgba(255,255,255,0.1); padding: 4px 10px;
                         border-radius: 10px; letter-spacing: 0.05em;">ACTIVE</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px;
                         color: #666; background: rgba(255,255,255,0.05); padding: 4px 10px;
                         border-radius: 10px; letter-spacing: 0.05em;">LOCKED</span>
        </div>
        """, unsafe_allow_html=True)


def render_balance_display(total_usdc: float):
    """Render V12 balance display - pure floating text"""
    st.markdown(f"""
    <div style="margin-bottom: 2.5rem;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                    letter-spacing: 0.1em; color: #555; margin-bottom: 8px;">
            EQUITY
        </div>
        <div style="font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 300;
                    color: white; letter-spacing: -0.04em;">
            ${total_usdc:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_footer():
    """Render V12 footer - minimal"""
    st.markdown("""
    <div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05);">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                    letter-spacing: 0.05em; color: #333; text-align: center;">
            Encrypted locally
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_transaction_history():
    """Render V12 transaction history - minimal list"""
    user_id = st.session_state.get("user_id")

    if not user_id or user_id.startswith("guest_"):
        return

    with st.expander("Recent", expanded=False):
        try:
            from supabase_client import get_supabase_client, get_user_transactions

            client = get_supabase_client(use_service_key=True)
            if not client:
                st.markdown("<div style='font-family: JetBrains Mono; font-size: 11px; color: #444;'>Unable to load</div>", unsafe_allow_html=True)
                return

            transactions = get_user_transactions(client, user_id, limit=5)

            if not transactions:
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #444;">
                    No transactions yet
                </div>
                """, unsafe_allow_html=True)
                return

            for tx in transactions:
                tx_type = tx.get("type", "unknown")
                amount = float(tx.get("amount", 0))
                status = tx.get("status", "pending")
                chain = tx.get("chain", "")

                # V12 minimal indicators
                direction = "+" if tx_type == "deposit" else "-"
                status_dot = "●" if status == "confirmed" else "○"

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <span style="font-family: 'Inter', sans-serif; font-size: 14px; color: white; font-weight: 300;">
                        {direction}${amount:.2f}
                    </span>
                    <span style="font-size: 8px; color: {'#fff' if status == 'confirmed' else '#444'};">{status_dot}</span>
                </div>
                """, unsafe_allow_html=True)

                tx_hash = tx.get("tx_hash")
                if tx_hash and chain:
                    explorer_url = ChainUtils.get_tx_explorer_url(chain, tx_hash)
                    if explorer_url:
                        st.markdown(f"""
                        <a href="{explorer_url}" target="_blank" style="font-family: 'JetBrains Mono', monospace;
                           font-size: 9px; color: #666; text-decoration: none; letter-spacing: 0.05em;">
                            View →
                        </a>
                        """, unsafe_allow_html=True)

        except Exception:
            st.markdown("<div style='font-family: JetBrains Mono; font-size: 11px; color: #444;'>Unable to load</div>", unsafe_allow_html=True)


def sidebar():
    """Render V12 sidebar - The Spine"""
    with st.sidebar:
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        render_sidebar_header()

        # No wallet - show login
        if not st.session_state.wallet_address:
            st.markdown("""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                        color: #444; margin-bottom: 1.5rem;">
                Initialize session to proceed
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

            with st.expander("Addresses", expanded=False):
                st.markdown(f"""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #888; margin-bottom: 8px;">
                    {ChainUtils.format_address(st.session_state.wallet_address, 8)}
                </div>
                """, unsafe_allow_html=True)
                if solana_addr:
                    st.markdown(f"""
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #666; margin-top: 8px;">
                        {ChainUtils.format_address(solana_addr, 8)}
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

            # Primary actions
            if st.button("DEPOSIT", use_container_width=True, type="primary"):
                st.session_state.show_deposit_modal = True
                st.rerun()

            if st.button("SEND", use_container_width=True):
                st.session_state.show_send_modal = True
                st.rerun()

            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

            # Transaction history
            render_transaction_history()

            st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

            # Secondary actions
            if st.button("SYSTEM", use_container_width=True):
                st.session_state.show_settings = True
                st.rerun()

            if st.button("LOCK", use_container_width=True):
                WalletManager.lock_wallet()
                st.rerun()

            render_sidebar_footer()

        else:
            # Wallet is locked
            if "wallet_encrypted" in st.session_state:
                render_status_card(is_active=False)

                st.markdown(f"""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                            color: #555; margin-bottom: 1rem;">
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
                            st.error("Invalid credentials")

                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

                if st.button("SYSTEM", use_container_width=True):
                    st.session_state.show_settings = True
                    st.rerun()

                if st.button("SIGN OUT", use_container_width=True):
                    SessionManager.logout()
                    st.rerun()

                render_sidebar_footer()

            elif st.session_state.get("wallet_address"):
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                            color: #444; margin-bottom: 1.5rem;">
                    Import wallet to continue
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #555;">
                    {ChainUtils.format_address(st.session_state.wallet_address)}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

                if st.button("IMPORT", use_container_width=True, type="primary"):
                    st.session_state.show_auth_modal = True
                    st.rerun()

                render_sidebar_footer()
