"""
Direct Transaction Executor
Signs and sends USDC transfers directly from user's wallet.
No relayer needed - user pays gas (works with Arc testnet USDC-as-gas).
"""

import time
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from config import NETWORKS, calculate_fee, get_rpc_url
import streamlit as st

# Balance cache TTL in seconds (matches chain_utils.py)
BALANCE_CACHE_TTL = 60


# Standard ERC20 ABI for transfer
ERC20_ABI = [
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
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


class DirectTransactionExecutor:
    """Execute USDC transfers directly from user's wallet"""

    def __init__(self, network_key: str = "arc-testnet"):
        self.network_key = network_key
        self.network = NETWORKS.get(network_key)
        if not self.network:
            raise ValueError(f"Unknown network: {network_key}")

        # Use RPC with automatic fallback
        rpc_url = get_rpc_url(network_key)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.chain_id = self.network["chain_id"]
        self.usdc_address = Web3.to_checksum_address(self.network["usdc_address"])

    def _get_cached_balance(self, address: str, balance_type: str) -> Optional[Decimal]:
        """Get balance from session cache if not expired"""
        cache_key = f"_direct_tx_balance_{self.network_key}_{address}_{balance_type}"
        cache_time_key = f"{cache_key}_time"

        cached_time = st.session_state.get(cache_time_key)
        if cached_time and (time.time() - cached_time) < BALANCE_CACHE_TTL:
            return st.session_state.get(cache_key)
        return None

    def _set_cached_balance(self, address: str, balance_type: str, balance: Decimal) -> None:
        """Cache balance in session state"""
        cache_key = f"_direct_tx_balance_{self.network_key}_{address}_{balance_type}"
        cache_time_key = f"{cache_key}_time"

        st.session_state[cache_key] = balance
        st.session_state[cache_time_key] = time.time()

    def get_usdc_balance(self, address: str, use_cache: bool = True) -> Decimal:
        """Get USDC balance for an address (with caching)"""
        # Check cache first
        if use_cache:
            cached = self._get_cached_balance(address, "usdc")
            if cached is not None:
                return cached

        try:
            usdc = self.w3.eth.contract(address=self.usdc_address, abi=ERC20_ABI)
            balance_raw = usdc.functions.balanceOf(
                Web3.to_checksum_address(address)
            ).call()
            # USDC has 6 decimals
            balance = Decimal(balance_raw) / Decimal(1e6)

            # Cache the result
            self._set_cached_balance(address, "usdc", balance)
            return balance
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Failed to get USDC balance: {e}")
            return Decimal(0)

    def get_native_balance(self, address: str, use_cache: bool = True) -> Decimal:
        """Get native token balance (ETH/etc) for gas (with caching)"""
        # Check cache first
        if use_cache:
            cached = self._get_cached_balance(address, "native")
            if cached is not None:
                return cached

        try:
            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            balance = Decimal(self.w3.from_wei(balance_wei, 'ether'))

            # Cache the result
            self._set_cached_balance(address, "native", balance)
            return balance
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Failed to get native balance: {e}")
            return Decimal(0)

    def estimate_gas(self, from_address: str, to_address: str, amount_usdc: float) -> Tuple[int, int]:
        """
        Estimate gas for USDC transfer.
        Returns: (gas_limit, gas_price_wei)
        """
        try:
            usdc = self.w3.eth.contract(address=self.usdc_address, abi=ERC20_ABI)
            amount_wei = int(amount_usdc * 1e6)  # USDC has 6 decimals

            # Estimate gas
            gas_estimate = usdc.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).estimate_gas({'from': Web3.to_checksum_address(from_address)})

            # Get current gas price
            gas_price = self.w3.eth.gas_price

            # Add 20% buffer to gas estimate
            gas_limit = int(gas_estimate * 1.2)

            return gas_limit, gas_price

        except Exception as e:
            from utils.logger import logger
            logger.warning(f"Gas estimation failed, using defaults: {e}")
            # Default values if estimation fails
            return 65000, self.w3.eth.gas_price

    def estimate_fee_usd(self, from_address: str, to_address: str, amount_usdc: float) -> Dict[str, float]:
        """
        Estimate total fees for a transfer.
        Returns dict with gas_cost_usd, app_fee, total_fee
        """
        gas_limit, gas_price = self.estimate_gas(from_address, to_address, amount_usdc)
        gas_cost_eth = (gas_limit * gas_price) / 1e18

        # Convert to USD (rough estimate)
        # For testnets, gas is essentially free
        if self.network.get("testnet"):
            gas_cost_usd = 0.0
        else:
            # Assume ~$2000/ETH for mainnet estimation
            gas_cost_usd = gas_cost_eth * 2000

        app_fee = calculate_fee(amount_usdc)

        return {
            "gas_cost_usd": gas_cost_usd,
            "gas_cost_eth": float(gas_cost_eth),
            "app_fee": app_fee,
            "total_fee": gas_cost_usd + app_fee,
            "gas_limit": gas_limit,
            "gas_price_wei": gas_price
        }

    def validate_transfer(
        self,
        from_address: str,
        to_address: str,
        amount_usdc: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a transfer can be executed.
        Returns: (is_valid, error_message)
        """
        # Check USDC balance
        usdc_balance = self.get_usdc_balance(from_address)
        fees = self.estimate_fee_usd(from_address, to_address, amount_usdc)
        total_needed = Decimal(amount_usdc) + Decimal(fees["app_fee"])

        if usdc_balance < total_needed:
            return False, f"Insufficient USDC. Need ${total_needed:.2f}, have ${usdc_balance:.2f}"

        # Check native balance for gas (skip on Arc testnet if USDC-as-gas)
        if not self.network.get("testnet"):
            native_balance = self.get_native_balance(from_address)
            gas_needed_eth = Decimal(fees["gas_cost_eth"])
            if native_balance < gas_needed_eth:
                return False, f"Insufficient gas. Need {gas_needed_eth:.6f} ETH, have {native_balance:.6f}"

        # Validate addresses
        try:
            Web3.to_checksum_address(from_address)
            Web3.to_checksum_address(to_address)
        except ValueError as e:
            return False, f"Invalid address: {e}"

        return True, None

    def execute_transfer(
        self,
        private_key: str,
        to_address: str,
        amount_usdc: float,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a USDC transfer directly from user's wallet.

        Args:
            private_key: User's private key (hex string with 0x prefix)
            to_address: Recipient address
            amount_usdc: Amount in USDC (e.g., 25.00)
            user_id: Optional user ID for spending limit tracking

        Returns:
            Dict with success status, tx_hash, and details
        """
        try:
            # Get sender address from private key
            account = Account.from_key(private_key)
            from_address = account.address

            # Validate the transfer
            is_valid, error = self.validate_transfer(from_address, to_address, amount_usdc)
            if not is_valid:
                return {"success": False, "error": error}

            # Check spending limits if user_id provided
            if user_id:
                try:
                    from spending_limits import check_spending_limit
                    app_fee = calculate_fee(amount_usdc)
                    total = amount_usdc + app_fee
                    can_proceed, limit_msg = check_spending_limit(user_id, total, "USDC transfer")
                    if not can_proceed:
                        return {"success": False, "error": limit_msg}
                except ImportError:
                    pass

            # Build the transaction
            usdc = self.w3.eth.contract(address=self.usdc_address, abi=ERC20_ABI)
            amount_wei = int(amount_usdc * 1e6)  # USDC has 6 decimals

            # Get gas estimates
            gas_limit, gas_price = self.estimate_gas(from_address, to_address, amount_usdc)

            # Build transaction
            tx = usdc.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'from': from_address,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'chainId': self.chain_id
            })

            # Sign transaction with user's private key
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()

            # Record spend if user_id provided
            if user_id:
                try:
                    from spending_limits import SpendingLimits
                    app_fee = calculate_fee(amount_usdc)
                    SpendingLimits.record_spend(user_id, amount_usdc + app_fee)
                except ImportError:
                    pass

            # Calculate actual costs
            fees = self.estimate_fee_usd(from_address, to_address, amount_usdc)

            return {
                "success": True,
                "tx_hash": tx_hash_hex,
                "amount": amount_usdc,
                "to": to_address,
                "from": from_address,
                "gas_cost": fees["gas_cost_usd"],
                "app_fee": fees["app_fee"],
                "total_cost": amount_usdc + fees["total_fee"],
                "network": self.network["name"],
                "explorer_url": f"{self.network['explorer']}/tx/{tx_hash_hex}"
            }

        except Exception as e:
            from utils.logger import logger
            logger.error(f"Direct transfer failed: {e}")
            return {
                "success": False,
                "error": f"Transaction failed: {str(e)}"
            }

    def wait_for_confirmation(self, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        """
        Wait for transaction confirmation.
        Returns receipt info or timeout error.
        """
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            return {
                "confirmed": True,
                "status": "success" if receipt["status"] == 1 else "failed",
                "block_number": receipt["blockNumber"],
                "gas_used": receipt["gasUsed"]
            }
        except Exception as e:
            return {
                "confirmed": False,
                "error": f"Confirmation timeout: {e}"
            }


def get_direct_executor(network_key: str = "arc-testnet") -> DirectTransactionExecutor:
    """Factory function to get a DirectTransactionExecutor instance"""
    return DirectTransactionExecutor(network_key)
