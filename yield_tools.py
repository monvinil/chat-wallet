"""
Yield Management Tools for AI Agent

Provides tools for depositing to and withdrawing from yield protocols.
Currently supports Aave V3 on Base and Arbitrum.
"""

import streamlit as st
from typing import List
from langchain_core.tools import tool

from aave_client import AaveClient, get_yield_summary
from wallet_manager import WalletManager
from utils.logger import logger


@tool
def get_yield_status() -> str:
    """
    Get the current yield status for the user's wallet.

    Shows:
    - Total USDC deposited in yield protocols
    - Current APY being earned
    - Estimated monthly earnings
    - Breakdown by network/protocol

    Returns:
        Summary of yield positions and earnings
    """
    wallet_address = st.session_state.get("wallet_address")
    if not wallet_address:
        return "Please connect your wallet first to see yield status."

    try:
        summary = get_yield_summary(wallet_address)

        if summary["total_deposited"] == 0:
            return (
                "You don't have any USDC deposited in yield protocols yet.\n\n"
                "Say **'deposit to Aave'** or **'start earning yield'** to deposit your idle USDC "
                "and start earning ~3-5% APY."
            )

        result = f"**Your Yield Summary**\n\n"
        result += f"- **Total Deposited:** ${summary['total_deposited']:,.2f}\n"
        result += f"- **Average APY:** {summary['average_apy']:.2f}%\n"
        result += f"- **Est. Monthly Earnings:** ${summary['estimated_monthly_earnings']:.2f}\n\n"

        if summary["positions"]:
            result += "**Positions:**\n"
            for pos in summary["positions"]:
                result += f"- {pos['protocol']} ({pos['network']}): ${pos['deposited']:,.2f} @ {pos['apy']:.2f}% APY\n"

        return result

    except Exception as e:
        logger.error(f"Failed to get yield status: {e}")
        return "Unable to fetch yield status. Please try again later."


@tool
def get_current_apy(network: str = "base-mainnet") -> str:
    """
    Get the current USDC yield APY on Aave.

    Args:
        network: Network to check ("base-mainnet" or "arbitrum-mainnet")

    Returns:
        Current APY information
    """
    try:
        client = AaveClient(network)
        apy = client.get_current_apy()

        network_name = "Base" if "base" in network else "Arbitrum"
        return f"Current USDC APY on Aave ({network_name}): **{apy:.2f}%**"

    except Exception as e:
        logger.error(f"Failed to get APY: {e}")
        return "Unable to fetch current APY. Please try again later."


@tool
def preview_yield_deposit(amount: float, network: str = "base-mainnet") -> str:
    """
    Preview a yield deposit before execution.

    Shows the user what will happen if they deposit to Aave.

    Args:
        amount: Amount of USDC to deposit
        network: Network to deposit on

    Returns:
        Preview with estimated earnings and confirmation request
    """
    wallet_address = st.session_state.get("wallet_address")
    if not wallet_address:
        return "Please connect your wallet first."

    if amount <= 0:
        return "Please specify a positive amount to deposit."

    try:
        client = AaveClient(network)

        # Check USDC balance
        usdc_balance = client.get_usdc_balance(wallet_address)
        if usdc_balance < amount:
            return f"Insufficient USDC balance. You have ${usdc_balance:.2f} available on {network}."

        apy = client.get_current_apy()
        network_name = "Base" if "base" in network else "Arbitrum"

        # Calculate projections
        daily_earnings = amount * (apy / 100) / 365
        monthly_earnings = amount * (apy / 100) / 12
        yearly_earnings = amount * (apy / 100)

        result = f"**Yield Deposit Preview**\n\n"
        result += f"- **Amount:** ${amount:,.2f} USDC\n"
        result += f"- **Protocol:** Aave V3\n"
        result += f"- **Network:** {network_name}\n"
        result += f"- **Current APY:** {apy:.2f}%\n\n"

        result += f"**Projected Earnings:**\n"
        result += f"- Daily: ${daily_earnings:.4f}\n"
        result += f"- Monthly: ${monthly_earnings:.2f}\n"
        result += f"- Yearly: ${yearly_earnings:.2f}\n\n"

        result += f"- **Liquidity:** Instant withdrawal anytime\n"
        result += f"- **Risk:** Low (Aave is audited, $5B+ TVL)\n\n"

        result += "Reply **'confirm deposit'** or **'yes'** to proceed."

        # Store pending deposit in session
        st.session_state._pending_yield_deposit = {
            "amount": amount,
            "network": network,
            "apy": apy
        }

        return result

    except Exception as e:
        logger.error(f"Failed to preview deposit: {e}")
        return "Unable to preview deposit. Please try again later."


@tool
def execute_yield_deposit(user_confirmed: bool = False) -> str:
    """
    Execute a yield deposit to Aave.

    IMPORTANT: Only call this after the user has confirmed via preview_yield_deposit.

    Args:
        user_confirmed: Must be True to execute. The user must explicitly confirm.

    Returns:
        Transaction result
    """
    if not user_confirmed:
        return "Please confirm the deposit first. Say 'yes' or 'confirm' to proceed."

    pending = st.session_state.get("_pending_yield_deposit")
    if not pending:
        return "No pending deposit. Please preview a deposit first with 'deposit $X to Aave'."

    # Check wallet is unlocked
    if not WalletManager.is_wallet_unlocked():
        return "Please unlock your wallet first to execute the deposit."

    wallet_data = WalletManager.get_wallet_from_session()
    if not wallet_data:
        return "Unable to access wallet. Please unlock your wallet."

    amount = pending["amount"]
    network = pending["network"]

    try:
        # Get private key
        private_key = wallet_data.get("evm", {}).get("private_key") or wallet_data.get("private_key")
        if not private_key:
            return "Unable to access wallet private key."

        client = AaveClient(network)
        result = client.deposit(private_key, amount)

        # Clear pending deposit
        del st.session_state._pending_yield_deposit

        if result.get("success"):
            network_name = "Base" if "base" in network else "Arbitrum"
            return (
                f"**Deposit Successful!**\n\n"
                f"- **Amount:** ${amount:,.2f} USDC\n"
                f"- **Protocol:** Aave V3 ({network_name})\n"
                f"- **TX:** `{result['tx_hash'][:16]}...`\n\n"
                f"Your USDC is now earning yield. Check status anytime with 'yield status'."
            )
        else:
            return f"Deposit failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        logger.error(f"Yield deposit failed: {e}")
        return f"Deposit failed: {str(e)}"


@tool
def preview_yield_withdrawal(amount: float = -1, network: str = "base-mainnet") -> str:
    """
    Preview a yield withdrawal before execution.

    Args:
        amount: Amount to withdraw, or -1 to withdraw all
        network: Network to withdraw from

    Returns:
        Preview with withdrawal details
    """
    wallet_address = st.session_state.get("wallet_address")
    if not wallet_address:
        return "Please connect your wallet first."

    try:
        client = AaveClient(network)
        deposited = client.get_ausdc_balance(wallet_address)

        if deposited == 0:
            return f"You don't have any USDC deposited on {network}."

        withdraw_amount = deposited if amount == -1 else min(amount, deposited)
        network_name = "Base" if "base" in network else "Arbitrum"

        result = f"**Yield Withdrawal Preview**\n\n"
        result += f"- **Amount:** ${withdraw_amount:,.2f} USDC\n"
        result += f"- **From:** Aave V3 ({network_name})\n"
        result += f"- **Your Total Deposited:** ${deposited:,.2f}\n\n"

        if amount == -1:
            result += "*Withdrawing full balance including accrued interest.*\n\n"

        result += "Reply **'confirm withdrawal'** or **'yes'** to proceed."

        # Store pending withdrawal
        st.session_state._pending_yield_withdrawal = {
            "amount": amount,
            "network": network,
            "actual_amount": withdraw_amount
        }

        return result

    except Exception as e:
        logger.error(f"Failed to preview withdrawal: {e}")
        return "Unable to preview withdrawal. Please try again later."


@tool
def execute_yield_withdrawal(user_confirmed: bool = False) -> str:
    """
    Execute a yield withdrawal from Aave.

    IMPORTANT: Only call this after the user has confirmed via preview_yield_withdrawal.

    Args:
        user_confirmed: Must be True to execute

    Returns:
        Transaction result
    """
    if not user_confirmed:
        return "Please confirm the withdrawal first. Say 'yes' or 'confirm' to proceed."

    pending = st.session_state.get("_pending_yield_withdrawal")
    if not pending:
        return "No pending withdrawal. Please preview a withdrawal first."

    if not WalletManager.is_wallet_unlocked():
        return "Please unlock your wallet first."

    wallet_data = WalletManager.get_wallet_from_session()
    if not wallet_data:
        return "Unable to access wallet."

    amount = pending["amount"]
    network = pending["network"]

    try:
        private_key = wallet_data.get("evm", {}).get("private_key") or wallet_data.get("private_key")
        if not private_key:
            return "Unable to access wallet private key."

        client = AaveClient(network)
        result = client.withdraw(private_key, amount)

        # Clear pending withdrawal
        del st.session_state._pending_yield_withdrawal

        if result.get("success"):
            network_name = "Base" if "base" in network else "Arbitrum"
            return (
                f"**Withdrawal Successful!**\n\n"
                f"- **Protocol:** Aave V3 ({network_name})\n"
                f"- **TX:** `{result['tx_hash'][:16]}...`\n\n"
                f"Your USDC has been returned to your wallet."
            )
        else:
            return f"Withdrawal failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        logger.error(f"Yield withdrawal failed: {e}")
        return f"Withdrawal failed: {str(e)}"


def get_yield_tools() -> List:
    """Get list of yield tools for AI agent"""
    return [
        get_yield_status,
        get_current_apy,
        preview_yield_deposit,
        execute_yield_deposit,
        preview_yield_withdrawal,
        execute_yield_withdrawal
    ]
