"""
Sidebar component for Chat Wallet
V12 "Liquid Silver" - The Spine
"""

import streamlit as st
from chain_utils import ChainUtils
from wallet_manager import WalletManager
from session_manager import SessionManager
from rate_limiter import RateLimiter


# === SKELETON LOADING STATES ===
def _inject_skeleton_css():
    """Inject CSS for skeleton loading animations (call once per page)"""
    st.markdown("""
    <style>
    @keyframes skeleton-shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    .skeleton {
        background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%);
        background-size: 200% 100%;
        animation: skeleton-shimmer 1.5s ease-in-out infinite;
        border-radius: 4px;
    }
    .skeleton-text { height: 14px; margin-bottom: 8px; }
    .skeleton-title { height: 32px; width: 60%; margin-bottom: 12px; }
    .skeleton-block { height: 40px; margin-bottom: 8px; }
    .skeleton-card { height: 96px; border-radius: 14px; }
    </style>
    """, unsafe_allow_html=True)


def render_balance_skeleton():
    """Render skeleton placeholder for balance display"""
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div class="skeleton skeleton-text" style="width: 50px;"></div>
        <div class="skeleton skeleton-title"></div>
    </div>
    """, unsafe_allow_html=True)


def render_transaction_skeleton(count: int = 3):
    """Render skeleton placeholder for transaction history"""
    st.markdown("""
    <div style="margin-bottom: 8px;">
        <div class="skeleton skeleton-text" style="width: 60px;"></div>
    </div>
    """, unsafe_allow_html=True)
    for _ in range(count):
        st.markdown("""
        <div class="skeleton" style="height: 32px; margin-bottom: 8px;"></div>
        """, unsafe_allow_html=True)


def render_address_skeleton():
    """Render skeleton placeholder for address display"""
    st.markdown("""
    <div style="margin-bottom: 12px;">
        <div class="skeleton skeleton-text" style="width: 30px;"></div>
        <div class="skeleton skeleton-block"></div>
    </div>
    """, unsafe_allow_html=True)


def _get_solana_address_from_session() -> str:
    """Get Solana address from wallet data or session state"""
    # First try wallet data (most reliable)
    wallet_data = WalletManager.get_wallet_from_session()
    if wallet_data and wallet_data.get("solana"):
        return wallet_data["solana"].get("address", "")
    # Fallback to session state
    return st.session_state.get("solana_address", "")


def render_sidebar_header():
    """Render sidebar logo: — $ →"""
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: 1.5rem; padding: 1rem 0;">
        <span style="display: inline-block; width: 16px; height: 1.5px; background: white; opacity: 0.85;"></span>
        <span style="font-family: 'Menlo', 'Monaco', monospace; font-size: 28px; font-weight: 700; font-style: italic; color: white; margin: 0 4px;">$</span>
        <span style="font-size: 14px; color: white; font-weight: 300; opacity: 0.8;">→</span>
    </div>
    """, unsafe_allow_html=True)


def render_status_card(is_active: bool):
    """Render V12 floating status text"""
    if is_active:
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                         color: #fff; background: rgba(255,255,255,0.1); padding: 6px 12px;
                         border-radius: 10px; letter-spacing: 0.05em;">ACTIVE</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                         color: #666; background: rgba(255,255,255,0.05); padding: 6px 12px;
                         border-radius: 10px; letter-spacing: 0.05em;">LOCKED</span>
        </div>
        """, unsafe_allow_html=True)


def render_balance_display(total_usdc: float, balances: dict = None):
    """Render V12 balance display with optional breakdown"""
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                    letter-spacing: 0.1em; color: #555; margin-bottom: 8px;">
            EQUITY
        </div>
        <div style="font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 300;
                    color: white; letter-spacing: -0.04em;">
            ${total_usdc:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show breakdown if balances provided and has non-zero values
    if balances:
        # Network display names - distinguish testnet vs mainnet
        network_names = {
            "eth-mainnet": "Ethereum",
            "base-mainnet": "Base",
            "arbitrum-mainnet": "Arbitrum",
            "solana-mainnet": "Solana",
            "eth-sepolia": "Ethereum ᵗ",
            "arc-testnet": "Arc ᵗ",
        }

        # Filter to networks with non-zero USDC
        active_networks = []
        for network_key, amounts in balances.items():
            usdc = amounts.get("usdc", 0.0)
            if usdc > 0:
                name = network_names.get(network_key, network_key)
                active_networks.append((name, usdc))

        if active_networks:
            breakdown_html = "<div style='margin-bottom: 1.5rem;'>"
            for name, usdc in active_networks:
                breakdown_html += f"""
                <div style="display: flex; justify-content: space-between; padding: 6px 0;">
                    <span style="font-family: JetBrains Mono; font-size: 11px; color: #444;">{name}</span>
                    <span style="font-family: JetBrains Mono; font-size: 11px; color: #666;">${usdc:,.2f}</span>
                </div>
                """
            breakdown_html += "</div>"
            st.markdown(breakdown_html, unsafe_allow_html=True)


def render_free_tier_indicator():
    """Show free tier usage if applicable"""
    from settings_manager import SettingsManager

    user_id = st.session_state.get("user_id")
    if not user_id:
        return

    llm_config = SettingsManager.get_llm_config(user_id)
    if llm_config.get("using_free_tier"):
        remaining = llm_config.get("remaining_messages", 0)
        if remaining <= 10:
            st.markdown(f"""
            <div style="font-family: JetBrains Mono; font-size: 11px; color: #a55; text-align: center; margin-bottom: 8px;">
                {remaining} free messages left
            </div>
            """, unsafe_allow_html=True)
        elif remaining <= 25:
            st.markdown(f"""
            <div style="font-family: JetBrains Mono; font-size: 11px; color: #555; text-align: center; margin-bottom: 8px;">
                {remaining} free messages
            </div>
            """, unsafe_allow_html=True)


def render_sidebar_footer():
    """Render V12 footer - minimal"""
    # Show free tier indicator if applicable
    render_free_tier_indicator()

    st.markdown("""
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05);">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                    letter-spacing: 0.05em; color: #333; text-align: center;">
            Encrypted locally
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_transaction_history():
    """Render V12 transaction history - direct display, no expander"""
    user_id = st.session_state.get("user_id")

    if not user_id or user_id.startswith("guest_"):
        return

    # Section header
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;
                letter-spacing: 0.1em; color: #444; margin-bottom: 8px;">RECENT</div>
    """, unsafe_allow_html=True)

    try:
        from supabase_client import get_supabase_client, get_user_transactions

        client = get_supabase_client(use_service_key=True)
        if not client:
            st.markdown("""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #333;
                        padding: 12px 0;">—</div>
            """, unsafe_allow_html=True)
            return

        transactions = get_user_transactions(client, user_id, limit=3)

        if not transactions:
            st.markdown("""
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #333;
                        padding: 12px 0;">No activity</div>
            """, unsafe_allow_html=True)
            return

        for tx in transactions:
            tx_type = tx.get("type", "unknown")
            amount = float(tx.get("amount", 0))
            status = tx.get("status", "pending")
            chain = tx.get("chain", "")
            tx_hash = tx.get("tx_hash")

            # V12 minimal indicators
            direction = "+" if tx_type == "deposit" else "−"
            status_color = "#888" if status == "confirmed" else "#444"

            # Build explorer link if available
            explorer_url = None
            if tx_hash and chain:
                explorer_url = ChainUtils.get_tx_explorer_url(chain, tx_hash)

            if explorer_url:
                st.markdown(f"""
                <a href="{explorer_url}" target="_blank" style="
                    display: flex; justify-content: space-between; align-items: center;
                    padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.03);
                    text-decoration: none;">
                    <span style="font-family: 'Inter', sans-serif; font-size: 14px; color: {status_color}; font-weight: 300;">
                        {direction}${amount:.2f}
                    </span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #333;">→</span>
                </a>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.03);">
                    <span style="font-family: 'Inter', sans-serif; font-size: 14px; color: {status_color}; font-weight: 300;">
                        {direction}${amount:.2f}
                    </span>
                </div>
                """, unsafe_allow_html=True)

    except Exception:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #333;
                    padding: 12px 0;">—</div>
        """, unsafe_allow_html=True)


def sidebar():
    """Render V12 sidebar - The Spine"""
    with st.sidebar:
        # Inject skeleton CSS once
        _inject_skeleton_css()

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

            if st.button("LOG IN / SIGN UP", use_container_width=True, type="primary"):
                st.session_state.show_auth_modal = True
                st.rerun()

            render_sidebar_footer()
            return

        # Wallet exists and unlocked
        if st.session_state.wallet_address and not st.session_state.get("wallet_locked", True):
            render_status_card(is_active=True)

            # Balance display (with skeleton loading state)
            is_loading_balance = st.session_state.get("_balance_loading", False)
            balances = st.session_state.balances if st.session_state.balances else {}

            if is_loading_balance and not balances:
                render_balance_skeleton()
            else:
                total_usdc = ChainUtils.calculate_total_usdc(balances) if balances else 0.0
                render_balance_display(total_usdc, balances)

            # Addresses - responsive middle-ellipsis with copy button
            solana_addr = _get_solana_address_from_session()
            evm_addr = st.session_state.wallet_address

            # CSS for responsive middle-truncation (first 6 fixed, last 4 fixed)
            st.markdown("""
            <style>
            .addr-section { margin-bottom: 12px; }
            .addr-label { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.1em; color: #444; margin-bottom: 4px; }
            .addr-box {
                display: flex; align-items: center; gap: 8px;
                background: rgba(255,255,255,0.05); padding: 10px 12px; border-radius: 4px;
            }
            .addr-text {
                flex: 1; min-width: 0; display: flex; overflow: hidden;
                font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #888;
            }
            .addr-start { flex-shrink: 0; white-space: nowrap; }
            .addr-mid { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            .addr-end { flex-shrink: 0; white-space: nowrap; }
            .addr-copy {
                flex-shrink: 0; cursor: pointer; opacity: 0.6; font-size: 11px;
                padding: 8px 12px; border-radius: 4px; transition: all 0.15s;
                background: rgba(255,255,255,0.08); color: #888;
                font-family: 'JetBrains Mono', monospace;
            }
            .addr-copy:hover { opacity: 1; background: rgba(255,255,255,0.15); color: #fff; }
            </style>
            """, unsafe_allow_html=True)

            # EVM Address (first 6 fixed, last 4 fixed) - e.g. 0x1234...cdef
            st.markdown(f"""
            <div class="addr-section">
                <div class="addr-label">EVM</div>
                <div class="addr-box">
                    <div class="addr-text">
                        <span class="addr-start">{evm_addr[:6]}</span>
                        <span class="addr-mid">{evm_addr[6:-4]}</span>
                        <span class="addr-end">{evm_addr[-4:]}</span>
                    </div>
                    <span class="addr-copy" onclick="navigator.clipboard.writeText('{evm_addr}')" title="Copy address">Copy</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Solana Address (if available) - first 6 fixed, last 4 fixed
            if solana_addr:
                st.markdown(f"""
                <div class="addr-section">
                    <div class="addr-label">SOL</div>
                    <div class="addr-box">
                        <div class="addr-text">
                            <span class="addr-start">{solana_addr[:6]}</span>
                            <span class="addr-mid">{solana_addr[6:-4]}</span>
                            <span class="addr-end">{solana_addr[-4:]}</span>
                        </div>
                        <span class="addr-copy" onclick="navigator.clipboard.writeText('{solana_addr}')" title="Copy address">Copy</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

            # Primary actions
            if st.button("DEPOSIT", use_container_width=True, type="primary"):
                RateLimiter.update_activity()  # Reset timeout on user action
                st.session_state.show_deposit_modal = True
                st.rerun()

            if st.button("SEND", use_container_width=True):
                RateLimiter.update_activity()  # Reset timeout on user action
                st.session_state.show_send_modal = True
                st.rerun()

            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

            # Transaction history
            render_transaction_history()

            st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

            # Secondary actions
            if st.button("SETTINGS", use_container_width=True):
                RateLimiter.update_activity()  # Reset timeout on user action
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

                with st.form("unlock_form", clear_on_submit=False, border=False):
                    unlock_password = st.text_input("Password", type="password", key="unlock_pwd",
                                                     label_visibility="collapsed", placeholder="Enter password")
                    submitted = st.form_submit_button("UNLOCK", use_container_width=True, type="primary")
                    if submitted and unlock_password:
                        if WalletManager.unlock_wallet_with_password(unlock_password):
                            # Update session with Solana address after unlock
                            wallet_data = WalletManager.get_wallet_from_session()
                            if wallet_data and wallet_data.get("solana"):
                                sol_addr = wallet_data["solana"].get("address")
                                if sol_addr:
                                    SessionManager.update_session_solana_address(sol_addr)
                                    # Also save to wallets table for persistence across refreshes
                                    user_id = st.session_state.get("user_id")
                                    if user_id:
                                        from supabase_client import save_wallet_address
                                        save_wallet_address(user_id, sol_addr, chain="solana")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")

                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

                if st.button("SETTINGS", use_container_width=True):
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
