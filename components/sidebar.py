"""
Sidebar component for Chat Wallet
"""

import streamlit as st
from chain_utils import ChainUtils
from wallet_manager import WalletManager
from session_manager import SessionManager


def _get_solana_address_from_session() -> str:
    """Get Solana address from session state if available"""
    return st.session_state.get("solana_address", "")


def render_sidebar_footer():
    """Render footer - transparent, builds trust"""
    st.markdown("---")
    st.caption("You control your wallet")


def render_transaction_history():
    """Render transaction history in sidebar"""
    user_id = st.session_state.get("user_id")

    # Guest users don't have persistent transaction history
    if not user_id or user_id.startswith("guest_"):
        return

    with st.expander("Recent transactions", expanded=False):
        try:
            from supabase_client import get_supabase_client, get_user_transactions

            client = get_supabase_client(use_service_key=True)
            if not client:
                st.caption("Unable to load transactions")
                return

            transactions = get_user_transactions(client, user_id, limit=5)

            if not transactions:
                st.caption("No transactions yet. Try asking me to send USDC or buy a gift card.")
                return

            for tx in transactions:
                tx_type = tx.get("type", "unknown")
                amount = float(tx.get("amount", 0))
                currency = tx.get("currency", "USD")
                status = tx.get("status", "pending")
                chain = tx.get("chain", "")

                # Format type with icon
                type_icons = {
                    "deposit": "+",
                    "withdrawal": "-",
                    "send": "-",
                    "swap": "~",
                    "gift_card_purchase": "-"
                }
                icon = type_icons.get(tx_type, "")

                # Status indicator
                status_indicator = {
                    "confirmed": "",
                    "pending": " (pending)",
                    "failed": " (failed)"
                }.get(status, "")

                # Format display
                if tx_type in ["deposit"]:
                    display = f"{icon}${amount:.2f} {currency}{status_indicator}"
                else:
                    display = f"{icon}${amount:.2f} {currency}{status_indicator}"

                st.caption(f"{display}")

                # Show explorer link if tx_hash exists
                tx_hash = tx.get("tx_hash")
                if tx_hash and chain:
                    explorer_url = ChainUtils.get_tx_explorer_url(chain, tx_hash)
                    if explorer_url:
                        st.caption(f"[View]({explorer_url})")

        except Exception:
            st.caption("Unable to load transactions")


def sidebar():
    """Render sidebar"""
    with st.sidebar:
        # Show login button if no wallet
        if not st.session_state.wallet_address:
            st.caption("Already have an account?")

            if st.button("Sign Up / Sign In", use_container_width=True):
                st.session_state.show_auth_modal = True
                st.rerun()

            render_sidebar_footer()
            return

        if st.session_state.wallet_address and not st.session_state.get("wallet_locked", True):
            # Balance
            if st.session_state.balances:
                total_usdc = ChainUtils.calculate_total_usdc(st.session_state.balances)
                st.metric("Balance", f"${total_usdc:.2f}")
            else:
                st.metric("Balance", "$0.00")

            # Addresses - show both EVM and Solana if available
            solana_addr = _get_solana_address_from_session()

            with st.expander("Addresses", expanded=False):
                st.caption("EVM (Base, Arbitrum, Polygon)")
                st.code(ChainUtils.format_address(st.session_state.wallet_address, 8))
                if solana_addr:
                    st.caption("Solana")
                    st.code(ChainUtils.format_address(solana_addr, 8))

            # Primary actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Deposit", use_container_width=True, type="primary"):
                    st.session_state.show_deposit_modal = True
                    st.rerun()
            with col2:
                if st.button("Send", use_container_width=True):
                    st.session_state.show_send_modal = True
                    st.rerun()

            st.divider()

            # Secondary actions
            if st.button("Settings", use_container_width=True):
                st.session_state.show_settings = True
                st.rerun()

            if st.button("Lock", use_container_width=True):
                WalletManager.lock_wallet()
                st.rerun()

            render_sidebar_footer()

        else:
            # Wallet is locked or doesn't exist
            if "wallet_encrypted" in st.session_state:
                st.caption("Wallet locked")
                st.code(ChainUtils.format_address(st.session_state.wallet_address, 8))
                unlock_password = st.text_input("Password", type="password", key="unlock_pwd")
                if st.button("Unlock", use_container_width=True, type="primary"):
                    if unlock_password:
                        if WalletManager.unlock_wallet_with_password(unlock_password):
                            st.success("Unlocked")
                            st.rerun()
                        else:
                            st.error("Incorrect password")
                            st.caption("Forgot? Use your recovery phrase to restore.")

                st.divider()

                # Allow Settings access even when locked
                if st.button("Settings", use_container_width=True):
                    st.session_state.show_settings = True
                    st.rerun()

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
