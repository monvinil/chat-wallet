"""
Sidebar component for Chat02
V10 "Brutalist Fintech" - Control Spire Design
Chrome gradients, cobalt accent, 0px brutalist corners.
"""

import streamlit as st
from chain_utils import ChainUtils
from wallet_manager import WalletManager
from session_manager import SessionManager


# --- CALLBACKS (avoid double-render from explicit st.rerun) ---
def _on_show_auth():
    st.session_state.show_auth_modal = True


def _on_show_deposit():
    st.session_state.show_deposit_modal = True


def _on_show_send():
    st.session_state.show_send_modal = True


def _on_show_settings():
    st.session_state.show_settings = True


def _on_lock_wallet():
    WalletManager.lock_wallet()


def _on_logout():
    SessionManager.logout()


def _get_solana_address_from_session() -> str:
    """Get Solana address from session state if available"""
    return st.session_state.get("solana_address", "")


def render_sidebar_header():
    """Render V10 brand mark - white circle + CHAT02"""
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid #1a1a1a;
    ">
        <div style="
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
        "></div>
        <div style="font-family: 'Inter', sans-serif; font-size: 14px;
                    letter-spacing: 0.15em; color: white;">
            <span style="font-weight: 300;">CHAT</span><span style="font-weight: 800;">02</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_indicator(is_active: bool):
    """Render V10 minimal status indicator"""
    if is_active:
        st.markdown("""
        <div style="
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 1.25rem;
        ">
            <div style="width: 6px; height: 6px; background: #3b82f6; border-radius: 50%;"></div>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                         letter-spacing: 0.15em; color: #525252;">SYSTEM_ACTIVE</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 1.25rem;
        ">
            <div style="width: 6px; height: 6px; background: #ef4444; border-radius: 50%;"></div>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                         letter-spacing: 0.15em; color: #525252;">CONSOLE_LOCKED</span>
        </div>
        """, unsafe_allow_html=True)


def render_balance_display(total_usdc: float):
    """Render V10 balance display with split typography"""
    balance_main = f"{int(total_usdc):,}"
    balance_dec = f"{int((total_usdc % 1)*100):02d}"

    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                    letter-spacing: 0.15em; color: #525252; margin-bottom: 8px;">
            TOTAL_EQUITY
        </div>
        <div style="display: flex; align-items: baseline;">
            <span style="font-family: 'Inter', sans-serif; font-size: 42px; font-weight: 300;
                        color: white; letter-spacing: -0.02em;">
                ${balance_main}
            </span>
            <span style="font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 300;
                        color: #525252;">.{balance_dec}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_transaction_history():
    """Render V10 transaction history"""
    user_id = st.session_state.get("user_id")

    if not user_id or user_id.startswith("guest_"):
        return

    with st.expander("RECENT_ACTIVITY", expanded=False):
        try:
            from supabase_client import get_supabase_client, get_user_transactions

            client = get_supabase_client(use_service_key=True)
            if not client:
                st.caption("UNABLE_TO_LOAD")
                return

            transactions = get_user_transactions(client, user_id, limit=5)

            if not transactions:
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #525252; letter-spacing: 0.1em;">
                    NO_TRANSACTIONS
                </div>
                """, unsafe_allow_html=True)
                return

            for tx in transactions:
                tx_type = tx.get("type", "unknown")
                amount = float(tx.get("amount", 0))
                status = tx.get("status", "pending")
                chain = tx.get("chain", "")

                # V10 brutalist badges
                if tx_type == "deposit":
                    badge = '<span style="background: #3b82f6; color: white; font-size: 9px; padding: 3px 8px; font-family: JetBrains Mono, monospace; letter-spacing: 0.1em;">IN</span>'
                else:
                    badge = '<span style="background: #262626; color: #a3a3a3; font-size: 9px; padding: 3px 8px; font-family: JetBrains Mono, monospace; letter-spacing: 0.1em;">OUT</span>'

                # Status indicator
                status_color = "#3b82f6" if status == "confirmed" else "#fbbf24" if status == "pending" else "#ef4444"

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 10px 0; border-bottom: 1px solid #1a1a1a;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        {badge}
                        <span style="font-family: 'Inter', sans-serif; font-size: 14px; color: white; font-weight: 400;">
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
                           font-size: 9px; color: #3b82f6; text-decoration: none; letter-spacing: 0.1em;">
                            VIEW_TX &rarr;
                        </a>
                        """, unsafe_allow_html=True)

        except Exception:
            st.caption("UNABLE_TO_LOAD")


def sidebar():
    """Render V10 sidebar - Control Spire"""
    with st.sidebar:
        render_sidebar_header()

        # No wallet - show login
        if not st.session_state.wallet_address:
            st.markdown("""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px;
                        color: #525252; letter-spacing: 0.1em; margin-bottom: 1.5rem;">
                AUTHENTICATE TO CONTINUE
            </div>
            """, unsafe_allow_html=True)

            st.button("INITIALIZE", use_container_width=True, type="primary",
                       on_click=_on_show_auth)
            return

        # Wallet exists and unlocked
        if st.session_state.wallet_address and not st.session_state.get("wallet_locked", True):
            render_status_indicator(is_active=True)

            # Balance display
            if st.session_state.balances:
                total_usdc = ChainUtils.calculate_total_usdc(st.session_state.balances)
            else:
                total_usdc = 0.0
            render_balance_display(total_usdc)

            # Wallet ID
            st.markdown(f"""
            <div style="margin-bottom: 1.5rem;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                            letter-spacing: 0.15em; color: #525252; margin-bottom: 4px;">
                    WALLET_ID
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #a3a3a3;">
                    {ChainUtils.format_address(st.session_state.wallet_address, 8)}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Solana address if available
            solana_addr = _get_solana_address_from_session()
            if solana_addr:
                st.markdown(f"""
                <div style="margin-bottom: 1.5rem;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                                letter-spacing: 0.15em; color: #525252; margin-bottom: 4px;">
                        SOLANA_ID
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #a3a3a3;">
                        {ChainUtils.format_address(solana_addr, 8)}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Primary navigation
            st.button("DEPOSIT ASSETS", use_container_width=True, type="primary",
                      on_click=_on_show_deposit)

            st.button("SEND FUNDS", use_container_width=True,
                      on_click=_on_show_send)

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

            # Transaction history
            render_transaction_history()

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

            # System expander
            with st.expander("SYSTEM", expanded=False):
                st.button("CONFIGURATION", use_container_width=True,
                          on_click=_on_show_settings)

                st.button("LOCK CONSOLE", use_container_width=True,
                          on_click=_on_lock_wallet)

        else:
            # Wallet is locked
            if "wallet_encrypted" in st.session_state:
                render_status_indicator(is_active=False)

                st.markdown(f"""
                <div style="margin-bottom: 1.5rem;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                                letter-spacing: 0.15em; color: #525252; margin-bottom: 4px;">
                        WALLET_ID
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #525252;">
                        {ChainUtils.format_address(st.session_state.wallet_address, 8)}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px;
                            letter-spacing: 0.15em; color: #525252; margin-bottom: 8px;">
                    ACCESS_KEY
                </div>
                """, unsafe_allow_html=True)

                unlock_password = st.text_input("Password", type="password", key="unlock_pwd",
                                                 label_visibility="collapsed", placeholder="ENTER KEY_")

                if st.button("UNLOCK", use_container_width=True, type="primary"):
                    if unlock_password:
                        if WalletManager.unlock_wallet_with_password(unlock_password):
                            st.rerun()
                        else:
                            st.error("INVALID_KEY")

                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

                with st.expander("SYSTEM", expanded=False):
                    st.button("CONFIGURATION", use_container_width=True,
                              on_click=_on_show_settings, key="locked_settings")

                    st.button("TERMINATE SESSION", use_container_width=True,
                              on_click=_on_logout)

            elif st.session_state.get("wallet_address"):
                st.markdown("""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px;
                            color: #525252; letter-spacing: 0.1em; margin-bottom: 1rem;">
                    IMPORT_REQUIRED
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #525252;
                            margin-bottom: 1rem;">
                    {ChainUtils.format_address(st.session_state.wallet_address)}
                </div>
                """, unsafe_allow_html=True)

                st.button("IMPORT WALLET", use_container_width=True, type="primary",
                          on_click=_on_show_auth)
