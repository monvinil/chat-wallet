"""
Transaction Relayer - Executes gasless transactions
Backend service that pays gas fees and executes user-signed transactions
"""

import os
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from config import NETWORKS, calculate_fee
from meta_tx import MetaTransaction
from utils.logger import logger
import streamlit as st


# USDC ABI for transfer
USDC_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]


class TransactionRelayer:
    """Relayer service for gasless transactions"""

    def __init__(self, network_key: str = "base-sepolia"):
        self.network_key = network_key
        self.network = NETWORKS[network_key]
        self.w3 = Web3(Web3.HTTPProvider(self.network["rpc_url"]))

        # Relayer wallet (your hot wallet that pays gas)
        relayer_key = os.getenv("RELAYER_PRIVATE_KEY")
        if not relayer_key:
            # Generate a temporary relayer for testing
            self.relayer_account = Account.create()
            st.warning(f"⚠️ Using temporary relayer. Add RELAYER_PRIVATE_KEY to .env for production.")
        else:
            self.relayer_account = Account.from_key(relayer_key)

        self.relayer_address = self.relayer_account.address

    def get_internal_balance(self, user_address: str, currency: str = "USDC") -> Decimal:
        """
        Get user's internal balance (what they've deposited minus what they've spent)
        TODO: Replace with actual database query
        """
        # For now, return on-chain balance as placeholder
        if currency == "USDC":
            try:
                usdc_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.network["usdc_address"]),
                    abi=USDC_ABI
                )
                balance_raw = usdc_contract.functions.balanceOf(
                    Web3.to_checksum_address(user_address)
                ).call()
                return Decimal(balance_raw) / Decimal(1e6)
            except Exception as e:
                logger.warning(f"Failed to fetch USDC balance for {user_address[:10]}...: {e}")
                return Decimal(0)
        return Decimal(0)

    def estimate_gas_cost(self, amount_usd: float) -> Tuple[float, float]:
        """
        Estimate gas cost in USD and calculate total fee
        Returns: (gas_cost_usd, app_fee_usd)
        """
        # Estimate gas price
        try:
            gas_price_wei = self.w3.eth.gas_price
            gas_limit = 65000  # Typical USDC transfer
            gas_cost_eth = (gas_price_wei * gas_limit) / 1e18

            # Convert ETH to USD (rough estimate: $2000/ETH for testnet, adjust for mainnet)
            eth_price_usd = 2000 if not self.network["testnet"] else 0
            gas_cost_usd = gas_cost_eth * eth_price_usd

            # On testnet, gas is "free" but we still track it
            if self.network["testnet"]:
                gas_cost_usd = 0.02  # Simulate $0.02 gas cost

        except Exception as e:
            logger.warning(f"Gas estimation failed, using default: {e}")
            gas_cost_usd = 0.02  # Default estimate

        # Calculate app fee
        app_fee = calculate_fee(amount_usd)

        return gas_cost_usd, app_fee

    def validate_transaction(
        self,
        message: Dict[str, Any],
        signature: str,
        user_address: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate meta-transaction including spending limits"""

        # Verify signature with correct chain ID
        chain_id = self.network["chain_id"]
        if not MetaTransaction.verify_signature(message, signature, user_address, chain_id=chain_id):
            return False, "Invalid signature"

        # Check if expired
        if MetaTransaction.is_expired(message):
            return False, "Transaction expired"

        # Check if from address matches
        if message["from"].lower() != user_address.lower():
            return False, "From address mismatch"

        # Check internal balance
        amount_usd = float(message["amount"]) / 1e6  # Convert from wei
        gas_cost, app_fee = self.estimate_gas_cost(amount_usd)
        total_needed = Decimal(amount_usd) + Decimal(gas_cost) + Decimal(app_fee)

        internal_balance = self.get_internal_balance(user_address, message["currency"])

        if internal_balance < total_needed:
            return False, f"Insufficient balance. Need ${total_needed:.2f}, have ${internal_balance:.2f}"

        # Check spending limits if user_id provided
        if user_id:
            try:
                from spending_limits import check_spending_limit
                can_proceed, limit_msg = check_spending_limit(
                    user_id, float(total_needed), "USDC transfer"
                )
                if not can_proceed:
                    return False, limit_msg
            except ImportError:
                logger.debug("Spending limits module not available, skipping check")

        return True, None

    def execute_transfer(
        self,
        message: Dict[str, Any],
        signature: str,
        user_address: str
    ) -> Dict[str, Any]:
        """
        Execute a gasless USDC transfer
        Returns transaction result with hash and status
        """

        # Validate transaction
        valid, error = self.validate_transaction(message, signature, user_address)
        if not valid:
            return {
                "success": False,
                "error": error
            }

        try:
            # Get USDC contract
            usdc_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.network["usdc_address"]),
                abi=USDC_ABI
            )

            # Build transaction
            to_address = Web3.to_checksum_address(message["to"])
            amount_wei = int(message["amount"])

            # Build the transfer call
            transfer_fn = usdc_contract.functions.transfer(to_address, amount_wei)

            # Estimate gas
            gas_estimate = transfer_fn.estimate_gas({
                'from': self.relayer_address
            })

            # Build transaction
            tx = transfer_fn.build_transaction({
                'from': self.relayer_address,
                'gas': gas_estimate + 10000,  # Add buffer
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.relayer_address)
            })

            # Sign with relayer account (we pay gas!)
            signed_tx = self.relayer_account.sign_transaction(tx)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Wait for receipt (optional, can be async)
            # receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            # Calculate costs
            amount_usd = float(amount_wei) / 1e6
            gas_cost, app_fee = self.estimate_gas_cost(amount_usd)
            total_cost = amount_usd + gas_cost + app_fee

            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "amount": amount_usd,
                "gas_cost": gas_cost,
                "app_fee": app_fee,
                "total_cost": total_cost,
                "network": self.network["name"],
                "explorer_url": f"{self.network['explorer']}/tx/{tx_hash.hex()}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Transaction failed: {str(e)}"
            }

    def get_relayer_balance(self) -> Dict[str, float]:
        """Get relayer wallet balances (for monitoring)"""
        try:
            eth_balance_wei = self.w3.eth.get_balance(self.relayer_address)
            eth_balance = float(self.w3.from_wei(eth_balance_wei, 'ether'))

            usdc_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.network["usdc_address"]),
                abi=USDC_ABI
            )
            usdc_balance_raw = usdc_contract.functions.balanceOf(
                Web3.to_checksum_address(self.relayer_address)
            ).call()
            usdc_balance = float(usdc_balance_raw) / 1e6

            return {
                "eth": eth_balance,
                "usdc": usdc_balance,
                "address": self.relayer_address
            }
        except Exception as e:
            logger.warning(f"Failed to get relayer balance: {e}")
            return {"eth": 0, "usdc": 0, "address": self.relayer_address}
