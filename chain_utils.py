"""
Multi-chain utilities for balance fetching and transaction handling
"""

import streamlit as st
import time
from typing import Dict, Optional
from decimal import Decimal
from web3 import Web3
from config import NETWORKS

# ERC20 USDC ABI (minimal - just balanceOf)
USDC_ABI = [
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

# Module-level cache for Web3 instances (persists across requests)
_web3_cache: Dict[str, Web3] = {}

# Balance cache TTL in seconds
BALANCE_CACHE_TTL = 30


class ChainUtils:
    """Utilities for interacting with multiple chains"""

    @staticmethod
    def _get_web3(network_key: str) -> Optional[Web3]:
        """Get cached Web3 instance for a network"""
        global _web3_cache

        if network_key in _web3_cache:
            w3 = _web3_cache[network_key]
            # Verify still connected
            try:
                if w3.is_connected():
                    return w3
            except Exception:
                pass
            # Connection lost, remove from cache
            del _web3_cache[network_key]

        # Create new connection
        network = NETWORKS.get(network_key)
        if not network or network["type"] != "evm":
            return None

        try:
            w3 = Web3(Web3.HTTPProvider(network["rpc_url"]))
            if w3.is_connected():
                _web3_cache[network_key] = w3
                return w3
        except Exception:
            pass

        return None

    @staticmethod
    def _retry_rpc_call(func, max_retries: int = 3, backoff_factor: float = 1.5):
        """Retry RPC calls with exponential backoff for reliability"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                wait_time = backoff_factor ** attempt
                time.sleep(wait_time)
        return None

    @staticmethod
    def _get_cached_balance(address: str, network_key: str) -> Optional[Dict[str, float]]:
        """Get balance from session cache if not expired"""
        cache_key = f"_balance_cache_{network_key}_{address}"
        cache_time_key = f"_balance_cache_time_{network_key}_{address}"

        cached_time = st.session_state.get(cache_time_key)
        if cached_time and (time.time() - cached_time) < BALANCE_CACHE_TTL:
            return st.session_state.get(cache_key)
        return None

    @staticmethod
    def _set_cached_balance(address: str, network_key: str, balance: Dict[str, float]) -> None:
        """Cache balance in session state"""
        cache_key = f"_balance_cache_{network_key}_{address}"
        cache_time_key = f"_balance_cache_time_{network_key}_{address}"

        st.session_state[cache_key] = balance
        st.session_state[cache_time_key] = time.time()

    @staticmethod
    def get_evm_balance(network_key: str, address: str, use_cache: bool = True) -> Dict[str, float]:
        """Get ETH and USDC balance for an EVM address"""
        network = NETWORKS.get(network_key)

        if not network or network["type"] != "evm":
            return {"eth": 0.0, "usdc": 0.0}

        # Check cache first
        if use_cache:
            cached = ChainUtils._get_cached_balance(address, network_key)
            if cached is not None:
                return cached

        try:
            # Get cached Web3 instance
            w3 = ChainUtils._get_web3(network_key)
            if not w3:
                # Fallback to creating new connection
                w3 = Web3(Web3.HTTPProvider(network["rpc_url"]))

            def check_connection():
                if not w3.is_connected():
                    raise ConnectionError(f"Cannot connect to {network['name']}")
                return True

            ChainUtils._retry_rpc_call(check_connection)

            # Get ETH balance with retry
            def get_eth_balance():
                return w3.eth.get_balance(address)

            eth_balance_wei = ChainUtils._retry_rpc_call(get_eth_balance)
            eth_balance = float(w3.from_wei(eth_balance_wei, 'ether'))

            # Get USDC balance with retry
            usdc_contract = w3.eth.contract(
                address=w3.to_checksum_address(network["usdc_address"]),
                abi=USDC_ABI
            )

            def get_usdc_balance():
                return usdc_contract.functions.balanceOf(
                    w3.to_checksum_address(address)
                ).call()

            usdc_balance_raw = ChainUtils._retry_rpc_call(get_usdc_balance)

            # USDC has 6 decimals
            usdc_balance = float(usdc_balance_raw) / 1e6

            result = {
                "eth": round(eth_balance, 6),
                "usdc": round(usdc_balance, 2)
            }

            # Cache the result
            ChainUtils._set_cached_balance(address, network_key, result)

            return result

        except Exception as e:
            # Silently return zeros instead of showing warnings (already retried 3x)
            print(f"Error fetching {network['name']} balance after retries: {e}")
            return {"eth": 0.0, "usdc": 0.0}

    @staticmethod
    def get_solana_balance(address: str) -> Dict[str, float]:
        """Get SOL and USDC balance for Solana address (mocked for now)"""
        # TODO: Implement real Solana balance fetching
        # Would use solana-py library
        return {
            "sol": 0.0,
            "usdc": 0.0
        }

    @staticmethod
    def get_all_balances(address: str) -> Dict[str, Dict[str, float]]:
        """Get balances across all supported chains (parallelized for speed)"""
        import concurrent.futures

        balances = {}

        # Prepare list of EVM networks to fetch
        evm_networks = [(key, info) for key, info in NETWORKS.items() if info["type"] == "evm"]

        # Fetch all EVM balances in parallel (4x faster)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_network = {
                executor.submit(ChainUtils.get_evm_balance, network_key, address): network_key
                for network_key, network_info in evm_networks
            }

            for future in concurrent.futures.as_completed(future_to_network, timeout=10):
                network_key = future_to_network[future]
                try:
                    balances[network_key] = future.result(timeout=5)
                except Exception as e:
                    print(f"Balance fetch error for {network_key}: {e}")
                    # Return zero balances on error instead of crashing
                    balances[network_key] = {"eth": 0.0, "usdc": 0.0}

        # Handle Solana (mock for now)
        for network_key, network_info in NETWORKS.items():
            if network_info["type"] == "solana":
                balances[network_key] = {"sol": 0.0, "usdc": 0.0}

        return balances

    @staticmethod
    def calculate_total_usdc(balances: Dict[str, Dict[str, float]]) -> float:
        """Calculate total USDC across all chains"""
        total = 0.0
        for chain_balances in balances.values():
            total += chain_balances.get("usdc", 0.0)
        return round(total, 2)

    @staticmethod
    def format_address(address: str, chars: int = 6) -> str:
        """Format address for display (0x1234...5678)"""
        if len(address) <= chars * 2:
            return address
        return f"{address[:chars]}...{address[-chars:]}"

    @staticmethod
    def get_explorer_url(network_key: str, address: str) -> str:
        """Get block explorer URL for an address"""
        network = NETWORKS.get(network_key)
        if not network:
            return ""
        return f"{network['explorer']}/address/{address}"

    @staticmethod
    def get_tx_explorer_url(network_key: str, tx_hash: str) -> str:
        """Get block explorer URL for a transaction"""
        network = NETWORKS.get(network_key)
        if not network:
            return ""
        return f"{network['explorer']}/tx/{tx_hash}"
