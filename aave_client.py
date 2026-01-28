"""
Aave V3 Integration for Yield on USDC

Supports Base and Arbitrum mainnets.
Provides deposit, withdraw, and APY tracking.
"""

import time
from typing import Optional, Dict, Any
from decimal import Decimal
from web3 import Web3
from eth_account import Account

from utils.logger import logger
from config import get_rpc_url

# Balance cache TTL in seconds
BALANCE_CACHE_TTL = 60

# Module-level cache for Aave balances
_aave_balance_cache: Dict[str, Dict[str, Any]] = {}


# Aave V3 Pool addresses by network
AAVE_POOLS = {
    "base-mainnet": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
    "arbitrum-mainnet": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "eth-mainnet": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
}

# USDC addresses by network
USDC_ADDRESSES = {
    "base-mainnet": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "arbitrum-mainnet": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "eth-mainnet": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
}

# aUSDC (Aave USDC token) addresses by network
AUSDC_ADDRESSES = {
    "base-mainnet": "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB",
    "arbitrum-mainnet": "0x724dc807b04555b71ed48a6896b6F41593b8C637",
    "eth-mainnet": "0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c",
}

# Minimal Aave Pool ABI for supply/withdraw
AAVE_POOL_ABI = [
    {
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "onBehalfOf", "type": "address"},
            {"name": "referralCode", "type": "uint16"}
        ],
        "name": "supply",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "asset", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "to", "type": "address"}
        ],
        "name": "withdraw",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {"name": "configuration", "type": "uint256"},
            {"name": "liquidityIndex", "type": "uint128"},
            {"name": "currentLiquidityRate", "type": "uint128"},
            {"name": "variableBorrowIndex", "type": "uint128"},
            {"name": "currentVariableBorrowRate", "type": "uint128"},
            {"name": "currentStableBorrowRate", "type": "uint128"},
            {"name": "lastUpdateTimestamp", "type": "uint40"},
            {"name": "id", "type": "uint16"},
            {"name": "aTokenAddress", "type": "address"},
            {"name": "stableDebtTokenAddress", "type": "address"},
            {"name": "variableDebtTokenAddress", "type": "address"},
            {"name": "interestRateStrategyAddress", "type": "address"},
            {"name": "accruedToTreasury", "type": "uint128"},
            {"name": "unbacked", "type": "uint128"},
            {"name": "isolationModeTotalDebt", "type": "uint128"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# ERC20 ABI for approve and balanceOf
ERC20_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class AaveClient:
    """Client for interacting with Aave V3 protocol"""

    def __init__(self, network: str = "base-mainnet"):
        self.network = network
        self.rpc_url = get_rpc_url(network)
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if network not in AAVE_POOLS:
            raise ValueError(f"Aave not supported on {network}")

        self.pool_address = Web3.to_checksum_address(AAVE_POOLS[network])
        self.usdc_address = Web3.to_checksum_address(USDC_ADDRESSES[network])
        self.ausdc_address = Web3.to_checksum_address(AUSDC_ADDRESSES[network])

        self.pool_contract = self.w3.eth.contract(
            address=self.pool_address,
            abi=AAVE_POOL_ABI
        )
        self.usdc_contract = self.w3.eth.contract(
            address=self.usdc_address,
            abi=ERC20_ABI
        )
        self.ausdc_contract = self.w3.eth.contract(
            address=self.ausdc_address,
            abi=ERC20_ABI
        )

    def get_current_apy(self) -> float:
        """Get current USDC supply APY from Aave"""
        try:
            reserve_data = self.pool_contract.functions.getReserveData(
                self.usdc_address
            ).call()

            # currentLiquidityRate is in RAY (1e27) and represents APR
            # Index 2 is currentLiquidityRate
            liquidity_rate = reserve_data[2]

            # Convert from RAY to percentage APY
            # APY = (1 + APR/secondsPerYear)^secondsPerYear - 1
            # For simplicity, we approximate: APY ≈ APR for low rates
            apy = (liquidity_rate / 1e27) * 100

            return round(apy, 2)

        except Exception as e:
            logger.error(f"Failed to get Aave APY: {e}")
            return 0.0

    def _get_cached_balance(self, wallet_address: str, balance_type: str) -> Optional[float]:
        """Get balance from cache if not expired"""
        cache_key = f"{self.network}_{wallet_address}_{balance_type}"
        if cache_key in _aave_balance_cache:
            cached = _aave_balance_cache[cache_key]
            if time.time() - cached["time"] < BALANCE_CACHE_TTL:
                return cached["value"]
        return None

    def _set_cached_balance(self, wallet_address: str, balance_type: str, value: float) -> None:
        """Cache balance value"""
        cache_key = f"{self.network}_{wallet_address}_{balance_type}"
        _aave_balance_cache[cache_key] = {
            "value": value,
            "time": time.time()
        }

    def get_ausdc_balance(self, wallet_address: str, use_cache: bool = True) -> float:
        """Get user's aUSDC balance (deposited USDC + accrued interest)"""
        # Check cache first
        if use_cache:
            cached = self._get_cached_balance(wallet_address, "ausdc")
            if cached is not None:
                return cached

        try:
            address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.ausdc_contract.functions.balanceOf(address).call()
            # USDC has 6 decimals
            balance = balance_wei / 1e6

            # Cache the result
            self._set_cached_balance(wallet_address, "ausdc", balance)
            return balance

        except Exception as e:
            logger.error(f"Failed to get aUSDC balance: {e}")
            return 0.0

    def get_usdc_balance(self, wallet_address: str, use_cache: bool = True) -> float:
        """Get user's USDC balance (not deposited)"""
        # Check cache first
        if use_cache:
            cached = self._get_cached_balance(wallet_address, "usdc")
            if cached is not None:
                return cached

        try:
            address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.usdc_contract.functions.balanceOf(address).call()
            balance = balance_wei / 1e6

            # Cache the result
            self._set_cached_balance(wallet_address, "usdc", balance)
            return balance

        except Exception as e:
            logger.error(f"Failed to get USDC balance: {e}")
            return 0.0

    def check_allowance(self, wallet_address: str) -> float:
        """Check USDC allowance for Aave pool"""
        try:
            address = Web3.to_checksum_address(wallet_address)
            allowance = self.usdc_contract.functions.allowance(
                address, self.pool_address
            ).call()
            return allowance / 1e6

        except Exception as e:
            logger.error(f"Failed to check allowance: {e}")
            return 0.0

    def build_approve_tx(self, wallet_address: str, amount: float) -> Dict[str, Any]:
        """Build approval transaction for Aave pool to spend USDC"""
        address = Web3.to_checksum_address(wallet_address)
        amount_wei = int(amount * 1e6)

        tx = self.usdc_contract.functions.approve(
            self.pool_address,
            amount_wei
        ).build_transaction({
            "from": address,
            "nonce": self.w3.eth.get_transaction_count(address),
            "gas": 100000,
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.w3.eth.chain_id
        })

        return tx

    def build_supply_tx(self, wallet_address: str, amount: float) -> Dict[str, Any]:
        """Build transaction to supply USDC to Aave"""
        address = Web3.to_checksum_address(wallet_address)
        amount_wei = int(amount * 1e6)

        tx = self.pool_contract.functions.supply(
            self.usdc_address,
            amount_wei,
            address,
            0  # referral code
        ).build_transaction({
            "from": address,
            "nonce": self.w3.eth.get_transaction_count(address),
            "gas": 300000,
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.w3.eth.chain_id
        })

        return tx

    def build_withdraw_tx(self, wallet_address: str, amount: float) -> Dict[str, Any]:
        """Build transaction to withdraw USDC from Aave"""
        address = Web3.to_checksum_address(wallet_address)

        # Use max uint256 to withdraw all if amount is -1
        if amount == -1:
            amount_wei = 2**256 - 1
        else:
            amount_wei = int(amount * 1e6)

        tx = self.pool_contract.functions.withdraw(
            self.usdc_address,
            amount_wei,
            address
        ).build_transaction({
            "from": address,
            "nonce": self.w3.eth.get_transaction_count(address),
            "gas": 300000,
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.w3.eth.chain_id
        })

        return tx

    def deposit(self, private_key: str, amount: float) -> Dict[str, Any]:
        """
        Deposit USDC to Aave (full flow: approve if needed, then supply)

        Returns: {"success": bool, "tx_hash": str, "error": str}
        """
        try:
            account = Account.from_key(private_key)
            wallet_address = account.address

            # Check current allowance
            current_allowance = self.check_allowance(wallet_address)

            if current_allowance < amount:
                # Need to approve first
                approve_tx = self.build_approve_tx(wallet_address, amount * 2)  # Approve 2x for buffer
                signed_approve = account.sign_transaction(approve_tx)
                approve_hash = self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)

                # Wait for approval
                self.w3.eth.wait_for_transaction_receipt(approve_hash, timeout=120)
                logger.info(f"Approval tx confirmed: {approve_hash.hex()}")

            # Now supply
            supply_tx = self.build_supply_tx(wallet_address, amount)
            # Update nonce after approval
            supply_tx["nonce"] = self.w3.eth.get_transaction_count(wallet_address)

            signed_supply = account.sign_transaction(supply_tx)
            supply_hash = self.w3.eth.send_raw_transaction(signed_supply.raw_transaction)

            # Wait for supply confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(supply_hash, timeout=120)

            return {
                "success": receipt["status"] == 1,
                "tx_hash": supply_hash.hex(),
                "amount": amount,
                "network": self.network
            }

        except Exception as e:
            logger.error(f"Aave deposit failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def withdraw(self, private_key: str, amount: float = -1) -> Dict[str, Any]:
        """
        Withdraw USDC from Aave

        Args:
            private_key: Wallet private key
            amount: Amount to withdraw, or -1 for max withdrawal

        Returns: {"success": bool, "tx_hash": str, "error": str}
        """
        try:
            account = Account.from_key(private_key)
            wallet_address = account.address

            # Build and sign withdraw tx
            withdraw_tx = self.build_withdraw_tx(wallet_address, amount)
            signed_tx = account.sign_transaction(withdraw_tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            return {
                "success": receipt["status"] == 1,
                "tx_hash": tx_hash.hex(),
                "network": self.network
            }

        except Exception as e:
            logger.error(f"Aave withdraw failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def get_yield_summary(wallet_address: str, networks: list = None) -> Dict[str, Any]:
    """
    Get yield summary across all supported networks

    Returns:
        {
            "total_deposited": float,
            "total_earned": float,
            "current_apy": float,
            "positions": [...]
        }
    """
    if networks is None:
        networks = ["base-mainnet", "arbitrum-mainnet"]

    positions = []
    total_deposited = 0.0
    weighted_apy = 0.0

    for network in networks:
        try:
            client = AaveClient(network)
            balance = client.get_ausdc_balance(wallet_address)
            apy = client.get_current_apy()

            if balance > 0:
                positions.append({
                    "network": network,
                    "deposited": balance,
                    "apy": apy,
                    "protocol": "Aave V3"
                })
                total_deposited += balance
                weighted_apy += balance * apy

        except Exception as e:
            logger.debug(f"Failed to get yield for {network}: {e}")

    avg_apy = weighted_apy / total_deposited if total_deposited > 0 else 0.0

    # Estimate earnings (simplified: assume deposited for 30 days at current APY)
    # In production, track actual deposit times
    estimated_monthly_earnings = total_deposited * (avg_apy / 100) / 12

    return {
        "total_deposited": round(total_deposited, 2),
        "estimated_monthly_earnings": round(estimated_monthly_earnings, 2),
        "average_apy": round(avg_apy, 2),
        "positions": positions
    }
