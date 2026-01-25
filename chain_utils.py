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

# Balance cache TTL in seconds (60s reduces RPC calls while keeping data reasonably fresh)
BALANCE_CACHE_TTL = 60


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
    def invalidate_balance_cache(address: Optional[str] = None) -> None:
        """Invalidate balance cache - call after transactions"""
        keys_to_delete = []
        for key in list(st.session_state.keys()):
            if key.startswith("_balance_cache"):
                if address is None or address in key:
                    keys_to_delete.append(key)
        for key in keys_to_delete:
            del st.session_state[key]
        # Also clear the main balances
        if "balances" in st.session_state:
            st.session_state.balances = {}

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
    def get_solana_balance(address: str, network_key: str = "solana-mainnet") -> Dict[str, float]:
        """Get SOL and USDC balance for Solana address"""
        try:
            from solana.rpc.api import Client
            from solders.pubkey import Pubkey

            network = NETWORKS.get(network_key)
            if not network or network["type"] != "solana":
                return {"sol": 0.0, "usdc": 0.0}

            client = Client(network["rpc_url"])

            # Get SOL balance
            pubkey = Pubkey.from_string(address)
            sol_balance_resp = client.get_balance(pubkey)

            if sol_balance_resp.value is not None:
                sol_balance = sol_balance_resp.value / 1e9  # Lamports to SOL
            else:
                sol_balance = 0.0

            # Get USDC balance (SPL token)
            usdc_balance = 0.0
            usdc_mint = network.get("usdc_address")

            if usdc_mint:
                try:
                    from solana.rpc.types import TokenAccountOpts
                    usdc_pubkey = Pubkey.from_string(usdc_mint)

                    # Get token accounts for USDC
                    token_accounts = client.get_token_accounts_by_owner(
                        pubkey,
                        TokenAccountOpts(mint=usdc_pubkey)
                    )

                    if token_accounts.value:
                        for account in token_accounts.value:
                            # Parse token account data
                            account_info = client.get_token_account_balance(account.pubkey)
                            if account_info.value:
                                usdc_balance += float(account_info.value.ui_amount or 0)
                except Exception as e:
                    print(f"Error fetching USDC balance: {e}")

            return {
                "sol": round(sol_balance, 6),
                "usdc": round(usdc_balance, 2)
            }

        except ImportError as e:
            print(f"Solana libraries not installed: {e}")
            return {"sol": 0.0, "usdc": 0.0}
        except Exception as e:
            print(f"Error fetching Solana balance: {e}")
            return {"sol": 0.0, "usdc": 0.0}

    @staticmethod
    def get_all_balances(address: str, solana_address: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """Get balances across all supported chains (parallelized for speed)"""
        import concurrent.futures

        balances = {}

        # Prepare list of EVM networks to fetch
        evm_networks = [(key, info) for key, info in NETWORKS.items() if info["type"] == "evm"]

        # Prepare list of Solana networks if address provided
        solana_networks = []
        if solana_address:
            solana_networks = [(key, info) for key, info in NETWORKS.items() if info["type"] == "solana"]

        # Fetch all balances in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Submit EVM balance fetches
            future_to_network = {
                executor.submit(ChainUtils.get_evm_balance, network_key, address): (network_key, "evm")
                for network_key, network_info in evm_networks
            }

            # Submit Solana balance fetches
            for network_key, network_info in solana_networks:
                future = executor.submit(ChainUtils.get_solana_balance, solana_address, network_key)
                future_to_network[future] = (network_key, "solana")

            for future in concurrent.futures.as_completed(future_to_network, timeout=5):
                network_key, chain_type = future_to_network[future]
                try:
                    balances[network_key] = future.result(timeout=3)
                except Exception as e:
                    print(f"Balance fetch error for {network_key}: {e}")
                    # Return zero balances on error
                    if chain_type == "solana":
                        balances[network_key] = {"sol": 0.0, "usdc": 0.0}
                    else:
                        balances[network_key] = {"eth": 0.0, "usdc": 0.0}

        # Add placeholder for Solana networks without address
        if not solana_address:
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
