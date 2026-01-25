"""
Sidebar component for Chat Wallet
V8 "The Drop" - High-End Streetwear Aesthetic
"""

import streamlit as st
from chain_utils import ChainUtils
from wallet_manager import WalletManager
from session_manager import SessionManager


def _get_solana_address_from_session() -> str:
    """Get Solana address from session state if available"""
    return st.session_state.get("solana_address", "")


def render_sidebar_header():
    """Render V8 brand header with volt accent"""
    st.markdown("""
    <div style="
        border-left: 3px solid #ccff00;
        padding-left: 12px;
        margin-bottom: 1.5rem;
    ">
        <div style="font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 800;
                    letter-spacing: 0.05em; color: white;">
            CW_SYSTEMS<span style="color: #ccff00;">&reg;</span>
        </div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                    color: #525252; margin-top: 2px; letter-spacing: 0.1em;">
            PERSONAL_EDITION
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_card(is_active: bool):
    """Render V8 status card with floating label"""
    if is_active:
        st.markdown("""
        <div style="position: relative; margin-bottom: 1.25rem;">
            <div style="
                position: absolute;
                top: -8px;
                left: 10px;
                background: #000;
                padding: 0 6px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 8px;
                color: #525252;
                letter-spacing: 0.1em;
            ">STATUS</div>
            <div style="
                border: 1px solid #ccff00;
                padding: 12px 14px;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <span style="width: 6px; height: 6px; background: #ccff00; border-radius: 50%;"></span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px;
                             letter-spacing: 0.1em; color: #ccff00;">ACTIVE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="position: relative; margin-bottom: 1.25rem;">
            <div style="
                position: absolute;
                top: -8px;
                left: 10px;
                background: #000;
                padding: 0 6px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 8px;
                color: #525252;
                letter-spacing: 0.1em;
            ">STATUS</div>
            <div style="
                border: 1px solid #333;
                padding: 12px 14px;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <span style="width: 6px; height: 6px; background: #ef4444; border-radius: 50%;"></span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px;
                             letter-spacing: 0.1em; color: #999;">LOCKED</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_balance_display(total_usdc: float):
    """Render V8 balance display with large typography"""
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                    letter-spacing: 0.1em; color: #525252; margin-bottom: 6px;">
            TOTAL_EQUITY
        </div>
        <div style="font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 600;
                    color: white; letter-spacing: -0.02em;">
            ${total_usdc:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_footer():
    """Render V8 footer - industrial trust indicators"""
    st.markdown("""
    <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #1a1a1a;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                    letter-spacing: 0.05em; color: #333; text-align: center;">
            ENCRYPTED LOCALLY / NO_CLOUD_LEAKS
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_transaction_history():
    """Render V8 transaction history ticker"""
    user_id = st.session_state.get("user_id")

    if not user_id or user_id.startswith("guest_"):
        return

    with st.expander("LATEST_OPS", expanded=False):
        try:
            from supabase_client import get_supabase_client, get_user_transactions

            client = get_supabase_client(use_service_key=True)
            if not client:
                st.caption("Unable to load")
                return

            transactions = get_user_transactions(client, user_id, limit=5)

            if not transactions:
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #525252;">
                    NO_TRANSACTIONS_YET
                </div>
                """, unsafe_allow_html=True)
                return

            for tx in transactions:
                tx_type = tx.get("type", "unknown")
                amount = float(tx.get("amount", 0))
                status = tx.get("status", "pending")
                chain = tx.get("chain", "")

                # V8 style badges
                if tx_type == "deposit":
                    badge = '<span style="background: #ccff00; color: black; font-size: 8px; padding: 2px 4px; font-family: JetBrains Mono; font-weight: 600;">IN</span>'
                else:
                    badge = '<span style="background: #333; color: white; font-size: 8px; padding: 2px 4px; font-family: JetBrains Mono;">OUT</span>'

                # Status indicator
                status_color = "#ccff00" if status == "confirmed" else "#fbbf24" if status == "pending" else "#ef4444"

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 8px 0; border-bottom: 1px solid #1a1a1a;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        {badge}
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: white;">
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
                           font-size: 9px; color: #ccff00; text-decoration: none; letter-spacing: 0.05em;">
                            VIEW_TX &rarr;
                        </a>
                        """, unsafe_allow_html=True)

        except Exception:
            st.caption("Unable to load")


def sidebar():
    """Render V8 sidebar"""
    with st.sidebar:
        render_sidebar_header()

        # No wallet - show login
        if not st.session_state.wallet_address:
            st.markdown("""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px;
                        color: #525252; margin-bottom: 1rem; letter-spacing: 0.05em;">
                INITIALIZE_SESSION_TO_PROCEED
            </div>
            """, unsafe_allow_html=True)

            if st.button("AUTHENTICATE", use_container_width=True, type="primary"):
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
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                            letter-spacing: 0.1em; color: #525252; margin-bottom: 4px;">
                    EVM_ADDR
                </div>
                """, unsafe_allow_html=True)
                st.code(ChainUtils.format_address(st.session_state.wallet_address, 8))
                if solana_addr:
                    st.markdown("""
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                                letter-spacing: 0.1em; color: #525252; margin-bottom: 4px; margin-top: 8px;">
                        SOL_ADDR
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

            if st.button("LOCK_SESSION", use_container_width=True):
                WalletManager.lock_wallet()
                st.rerun()

            render_sidebar_footer()

        else:
            # Wallet is locked
            if "wallet_encrypted" in st.session_state:
                render_status_card(is_active=False)

                st.markdown(f"""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                            color: #666; margin-bottom: 0.75rem;">
                    {ChainUtils.format_address(st.session_state.wallet_address, 8)}
                </div>
                """, unsafe_allow_html=True)

                unlock_password = st.text_input("Password", type="password", key="unlock_pwd",
                                                 label_visibility="collapsed", placeholder="Enter password")

                if st.button("DECRYPT", use_container_width=True, type="primary"):
                    if unlock_password:
                        if WalletManager.unlock_wallet_with_password(unlock_password):
                            st.rerun()
                        else:
                            st.error("INVALID_CREDENTIALS")

                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

                if st.button("SETTINGS", use_container_width=True):
                    st.session_state.show_settings = True
                    st.rerun()

                if st.button("TERMINATE", use_container_width=True):
                    SessionManager.logout()
                    st.rerun()

                render_sidebar_footer()

            elif st.session_state.get("wallet_address"):
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px;
                            color: #525252; margin-bottom: 1rem; letter-spacing: 0.05em;">
                    IMPORT_WALLET_TO_CONTINUE
                </div>
                """, unsafe_allow_html=True)
                st.code(ChainUtils.format_address(st.session_state.wallet_address))

                if st.button("IMPORT_WALLET", use_container_width=True, type="primary"):
                    st.session_state.show_auth_modal = True
                    st.rerun()

                render_sidebar_footer()
