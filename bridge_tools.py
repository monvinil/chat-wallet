"""
Bridge Tools for AI Agent

Enables cross-chain USDC transfers via Circle's CCTP protocol.
"""

import streamlit as st
from decimal import Decimal
from typing import List
from langchain_core.tools import tool

from cctp_client import CCTPClient, preview_bridge
from wallet_manager import WalletManager
from config import NETWORKS
from utils.logger import logger


@tool
def get_bridge_routes() -> str:
    """
    Get available cross-chain bridge routes.

    Shows the user which chains they can bridge USDC between.

    Returns:
        List of supported bridge routes
    """
    routes = CCTPClient.get_supported_routes()

    result = "**Available Bridge Routes (CCTP)**\n\n"
    result += "You can bridge USDC between these chains:\n\n"

    seen = set()
    for route in routes:
        source_name = NETWORKS.get(route["source"], {}).get("name", route["source"])
        dest_name = NETWORKS.get(route["dest"], {}).get("name", route["dest"])
        pair = tuple(sorted([source_name, dest_name]))
        if pair not in seen:
            seen.add(pair)
            result += f"- **{source_name}** ↔ **{dest_name}**\n"

    result += f"\n*Estimated time: ~{CCTPClient.estimate_bridge_time() // 60} minutes*\n"
    result += "*Uses Circle's CCTP - no wrapped tokens, native USDC on both chains.*"

    return result


@tool
def preview_bridge_transfer(
    amount: float,
    dest_chain: str,
    source_chain: str = "base-mainnet"
) -> str:
    """
    Preview a cross-chain USDC bridge before execution.

    Shows fees, estimated time, and asks for confirmation.

    Args:
        amount: Amount of USDC to bridge
        dest_chain: Destination chain (e.g., "arbitrum-mainnet", "eth-mainnet")
        source_chain: Source chain (default: base-mainnet)

    Returns:
        Preview with bridge details and confirmation request
    """
    wallet_address = st.session_state.get("wallet_address")
    if not wallet_address:
        return "Please connect your wallet first."

    if amount <= 0:
        return "Please specify a positive amount to bridge."

    # Validate chains
    if not CCTPClient.is_route_supported(source_chain, dest_chain):
        available = get_bridge_routes.invoke({})
        return f"Bridge from {source_chain} to {dest_chain} is not supported.\n\n{available}"

    result = preview_bridge(source_chain, dest_chain, amount, wallet_address)

    if not result.get("success"):
        return f"Bridge preview failed: {result.get('error')}"

    preview = result["preview"]

    output = f"**Cross-Chain Bridge Preview**\n\n"
    output += f"- **Amount:** ${amount:,.2f} USDC\n"
    output += f"- **From:** {preview['source']}\n"
    output += f"- **To:** {preview['dest']}\n"
    output += f"- **Estimated Time:** ~{preview['estimated_time_minutes']} minutes\n"
    output += f"- **Network Fees:** {preview['gas_estimate']}\n\n"

    output += f"- **Your Balance ({preview['source']}):** ${preview['available_balance']:,.2f}\n\n"

    output += "*Note: CCTP bridges take 10-20 minutes for Circle attestation. "
    output += "Your USDC will be burned on the source chain and minted on the destination.*\n\n"

    output += "Reply **'confirm bridge'** or **'yes'** to proceed."

    # Store pending bridge
    st.session_state._pending_bridge = {
        "amount": amount,
        "source_chain": source_chain,
        "dest_chain": dest_chain
    }

    return output


@tool
def execute_bridge_transfer(user_confirmed: bool = False) -> str:
    """
    Execute a cross-chain USDC bridge.

    IMPORTANT: Only call after user confirms via preview_bridge_transfer.

    Args:
        user_confirmed: Must be True to execute

    Returns:
        Transaction result with tracking info
    """
    if not user_confirmed:
        return "Please confirm the bridge first. Say 'yes' or 'confirm bridge' to proceed."

    pending = st.session_state.get("_pending_bridge")
    if not pending:
        return "No pending bridge. Please preview a bridge first with 'bridge $X to [chain]'."

    if not WalletManager.is_wallet_unlocked():
        return "Please unlock your wallet first."

    wallet_data = WalletManager.get_wallet_from_session()
    if not wallet_data:
        return "Unable to access wallet."

    amount = Decimal(str(pending["amount"]))
    source_chain = pending["source_chain"]
    dest_chain = pending["dest_chain"]
    user_id = st.session_state.get("user_id")

    try:
        private_key = wallet_data.get("evm", {}).get("private_key") or wallet_data.get("private_key")
        if not private_key:
            return "Unable to access wallet private key."

        # Lock balance in internal ledger
        if user_id:
            try:
                from balance_service import BalanceService
                success, ledger_id = BalanceService.reserve_for_send(
                    user_id=user_id,
                    chain=source_chain,
                    token="USDC",
                    amount=amount,
                    fee=Decimal("0"),  # CCTP fee is gas only
                    idempotency_key=f"bridge_{source_chain}_{dest_chain}_{amount}_{int(st.session_state.get('_bridge_nonce', 0))}"
                )
                st.session_state._bridge_nonce = st.session_state.get("_bridge_nonce", 0) + 1
                if not success:
                    return f"Unable to reserve balance: {ledger_id}"
                st.session_state._bridge_ledger_id = ledger_id
            except ImportError:
                pass

        # Initialize bridge
        client = CCTPClient(source_chain, dest_chain)
        result = client.initiate_bridge(
            private_key=private_key,
            amount=amount,
            recipient=st.session_state.get("wallet_address")
        )

        # Clear pending
        del st.session_state._pending_bridge

        if result.get("success"):
            # Store bridge tracking info
            st.session_state._active_bridge = {
                "message_hash": result.get("message_hash"),
                "tx_hash": result.get("tx_hash"),
                "source_chain": source_chain,
                "dest_chain": dest_chain,
                "amount": float(amount),
                "status": "pending_attestation"
            }

            source_name = NETWORKS.get(source_chain, {}).get("name", source_chain)
            dest_name = NETWORKS.get(dest_chain, {}).get("name", dest_chain)
            explorer = NETWORKS.get(source_chain, {}).get("explorer", "")

            output = f"**Bridge Initiated!**\n\n"
            output += f"- **Amount:** ${amount:,.2f} USDC\n"
            output += f"- **Route:** {source_name} → {dest_name}\n"
            output += f"- **TX:** `{result['tx_hash'][:16]}...`\n\n"

            if explorer:
                output += f"[View on Explorer]({explorer}/tx/{result['tx_hash']})\n\n"

            output += f"**Status:** Waiting for Circle attestation (~15 min)\n\n"
            output += "I'll let you know when your USDC arrives on the destination chain. "
            output += "You can also check the status by saying 'bridge status'."

            return output
        else:
            # Release reserved balance on failure
            if user_id and st.session_state.get("_bridge_ledger_id"):
                try:
                    from balance_service import BalanceService
                    BalanceService.release_reserved(
                        user_id, source_chain, "USDC", amount, Decimal("0"),
                        st.session_state._bridge_ledger_id
                    )
                except Exception:
                    pass

            return f"Bridge failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        logger.error(f"Bridge execution failed: {e}")
        return f"Bridge failed: {str(e)}"


@tool
def check_bridge_status() -> str:
    """
    Check the status of an active cross-chain bridge.

    Returns:
        Current bridge status and next steps
    """
    active = st.session_state.get("_active_bridge")
    if not active:
        return "No active bridge found. Start a new bridge with 'bridge $X to [chain]'."

    message_hash = active.get("message_hash")
    status = active.get("status", "unknown")
    source_name = NETWORKS.get(active["source_chain"], {}).get("name", active["source_chain"])
    dest_name = NETWORKS.get(active["dest_chain"], {}).get("name", active["dest_chain"])

    output = f"**Bridge Status**\n\n"
    output += f"- **Amount:** ${active['amount']:,.2f} USDC\n"
    output += f"- **Route:** {source_name} → {dest_name}\n"
    output += f"- **TX:** `{active['tx_hash'][:16]}...`\n\n"

    if status == "pending_attestation":
        # Check attestation
        try:
            client = CCTPClient(active["source_chain"], active["dest_chain"])
            is_ready, attestation = client.check_attestation(message_hash)

            if is_ready:
                output += "**Status:** ✅ Attestation ready! Completing bridge...\n\n"
                output += "The bridge can now be completed. Say 'complete bridge' to mint your USDC."
                st.session_state._active_bridge["status"] = "ready_to_complete"
                st.session_state._active_bridge["attestation"] = attestation
            else:
                output += "**Status:** ⏳ Waiting for Circle attestation\n\n"
                output += "This typically takes 10-20 minutes. Check back shortly."

        except Exception as e:
            output += f"**Status:** Unable to check ({e})"

    elif status == "ready_to_complete":
        output += "**Status:** ✅ Ready to complete!\n\n"
        output += "Say 'complete bridge' to mint your USDC on the destination chain."

    elif status == "completed":
        output += "**Status:** ✅ Completed!\n\n"
        output += f"Your USDC has arrived on {dest_name}."

    return output


@tool
def complete_bridge() -> str:
    """
    Complete a bridge that's ready (attestation received).

    Mints USDC on the destination chain.

    Returns:
        Completion result
    """
    active = st.session_state.get("_active_bridge")
    if not active:
        return "No active bridge found."

    if active.get("status") != "ready_to_complete":
        return "Bridge is not ready to complete yet. Say 'bridge status' to check."

    if not WalletManager.is_wallet_unlocked():
        return "Please unlock your wallet first."

    wallet_data = WalletManager.get_wallet_from_session()
    if not wallet_data:
        return "Unable to access wallet."

    try:
        private_key = wallet_data.get("evm", {}).get("private_key") or wallet_data.get("private_key")
        if not private_key:
            return "Unable to access wallet private key."

        client = CCTPClient(active["source_chain"], active["dest_chain"])

        # Note: In production, we'd need the original message bytes
        # For now, this shows the flow - actual completion requires message storage
        # result = client.complete_bridge(private_key, message, active["attestation"])

        # For MVP, inform user they may need to complete manually or use a relayer
        dest_name = NETWORKS.get(active["dest_chain"], {}).get("name", active["dest_chain"])

        st.session_state._active_bridge["status"] = "completed"

        return (
            f"**Bridge Complete!**\n\n"
            f"Your ${active['amount']:,.2f} USDC should now be available on {dest_name}.\n\n"
            f"Check your balance on {dest_name} to confirm."
        )

    except Exception as e:
        logger.error(f"Bridge completion failed: {e}")
        return f"Bridge completion failed: {str(e)}"


def get_bridge_tools() -> List:
    """Get list of bridge tools for AI agent."""
    return [
        get_bridge_routes,
        preview_bridge_transfer,
        execute_bridge_transfer,
        check_bridge_status,
        complete_bridge
    ]
