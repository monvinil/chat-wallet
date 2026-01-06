"""
Multi-chain utilities for balance fetching and transaction handling
"""

import streamlit as st
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


class ChainUtils:
    """Utilities for interacting with multiple chains"""

    @staticmethod
    def get_evm_balance(network_key: str, address: str) -> Dict[str, float]:
        """Get ETH and USDC balance for an EVM address"""
        network = NETWORKS.get(network_key)

        if not network or network["type"] != "evm":
            return {"eth": 0.0, "usdc": 0.0}

        try:
            # Connect to RPC
            w3 = Web3(Web3.HTTPProvider(network["rpc_url"]))

            if not w3.is_connected():
                st.warning(f"Cannot connect to {network['name']}")
                return {"eth": 0.0, "usdc": 0.0}

            # Get ETH balance
            eth_balance_wei = w3.eth.get_balance(address)
            eth_balance = float(w3.from_wei(eth_balance_wei, 'ether'))

            # Get USDC balance
            usdc_contract = w3.eth.contract(
                address=w3.to_checksum_address(network["usdc_address"]),
                abi=USDC_ABI
            )

            usdc_balance_raw = usdc_contract.functions.balanceOf(
                w3.to_checksum_address(address)
            ).call()

            # USDC has 6 decimals
            usdc_balance = float(usdc_balance_raw) / 1e6

            return {
                "eth": round(eth_balance, 6),
                "usdc": round(usdc_balance, 2)
            }

        except Exception as e:
            st.warning(f"Error fetching {network['name']} balance: {e}")
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
