"""
Configuration for Chat Wallet
"""

import os
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Supabase Config (you'll add these after setup)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # For admin operations

# Anthropic API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# RPC Provider API Keys (optional - enables premium endpoints)
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY", "")
INFURA_API_KEY = os.getenv("INFURA_API_KEY", "")

# Supported Networks with fallback RPC URLs
NETWORKS = {
    # === MAINNETS ===
    "eth-mainnet": {
        "name": "Ethereum",
        "chain_id": 1,
        "type": "evm",
        "testnet": False,
        "rpc_url": "https://eth.llamarpc.com",
        "rpc_fallbacks": [
            "https://ethereum.publicnode.com",
            "https://1rpc.io/eth",
            "https://rpc.ankr.com/eth",
        ],
        "explorer": "https://etherscan.io",
        "usdc_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    },
    "base-mainnet": {
        "name": "Base",
        "chain_id": 8453,
        "type": "evm",
        "testnet": False,
        "rpc_url": "https://mainnet.base.org",
        "rpc_fallbacks": [
            "https://base.publicnode.com",
            "https://1rpc.io/base",
            "https://base.meowrpc.com",
        ],
        "explorer": "https://basescan.org",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    },
    "arbitrum-mainnet": {
        "name": "Arbitrum",
        "chain_id": 42161,
        "type": "evm",
        "testnet": False,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "rpc_fallbacks": [
            "https://arbitrum-one.publicnode.com",
            "https://1rpc.io/arb",
            "https://arbitrum.meowrpc.com",
        ],
        "explorer": "https://arbiscan.io",
        "usdc_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    },
    "solana-mainnet": {
        "name": "Solana",
        "type": "solana",
        "testnet": False,
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "rpc_fallbacks": [
            "https://solana-api.projectserum.com",
        ],
        "explorer": "https://explorer.solana.com",
        "usdc_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    },
    # === TESTNETS ===
    "eth-sepolia": {
        "name": "Ethereum Sepolia",
        "chain_id": 11155111,
        "type": "evm",
        "testnet": True,
        "rpc_url": "https://ethereum-sepolia-rpc.publicnode.com",
        "rpc_fallbacks": [
            "https://rpc.sepolia.org",
            "https://sepolia.drpc.org",
        ],
        "explorer": "https://sepolia.etherscan.io",
        "usdc_address": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
    },
    "arc-testnet": {
        "name": "Arc",
        "chain_id": 5042002,
        "type": "evm",
        "testnet": True,
        "rpc_url": "https://rpc.testnet.arc.network",
        "rpc_fallbacks": [],
        "explorer": "https://testnet.arcscan.app",
        "usdc_address": "0x3600000000000000000000000000000000000000"
    }
}

# === RPC Connection Cache ===
# Tracks which RPCs are working and which have failed recently
_rpc_health: Dict[str, Dict[str, Any]] = {}
_RPC_FAILURE_COOLDOWN = 300  # 5 minutes before retrying a failed RPC

# Fee Structure
FEE_FLAT = 0.005  # $0.005 = 0.5 cents
FEE_PERCENTAGE = 0.002  # 0.2%
FEE_MAX = 3.0  # $3 cap

def calculate_fee(amount_usd: float) -> float:
    """Calculate transaction fee based on amount"""
    fee = FEE_FLAT + (amount_usd * FEE_PERCENTAGE)
    return min(fee, FEE_MAX)


def _build_rpc_list(network: str) -> list:
    """Build prioritized list of RPC URLs for a network"""
    if network not in NETWORKS:
        return []

    config = NETWORKS[network]
    rpcs = []

    # Add Alchemy/Infura premium endpoints if keys are available
    if ALCHEMY_API_KEY:
        alchemy_endpoints = {
            "eth-mainnet": f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
            "base-mainnet": f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
            "arbitrum-mainnet": f"https://arb-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
            "eth-sepolia": f"https://eth-sepolia.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
        }
        if network in alchemy_endpoints:
            rpcs.append(alchemy_endpoints[network])

    if INFURA_API_KEY:
        infura_endpoints = {
            "eth-mainnet": f"https://mainnet.infura.io/v3/{INFURA_API_KEY}",
            "arbitrum-mainnet": f"https://arbitrum-mainnet.infura.io/v3/{INFURA_API_KEY}",
            "eth-sepolia": f"https://sepolia.infura.io/v3/{INFURA_API_KEY}",
        }
        if network in infura_endpoints:
            rpcs.append(infura_endpoints[network])

    # Add primary RPC
    if config.get("rpc_url"):
        rpcs.append(config["rpc_url"])

    # Add fallbacks
    rpcs.extend(config.get("rpc_fallbacks", []))

    return rpcs


def _is_rpc_healthy(rpc_url: str) -> bool:
    """Check if an RPC was recently marked as failed"""
    if rpc_url not in _rpc_health:
        return True

    health = _rpc_health[rpc_url]
    if health.get("failed"):
        # Check if cooldown has passed
        if time.time() - health.get("failed_at", 0) > _RPC_FAILURE_COOLDOWN:
            # Reset and try again
            del _rpc_health[rpc_url]
            return True
        return False
    return True


def _mark_rpc_failed(rpc_url: str):
    """Mark an RPC as failed"""
    _rpc_health[rpc_url] = {
        "failed": True,
        "failed_at": time.time()
    }


def _mark_rpc_success(rpc_url: str):
    """Mark an RPC as working"""
    _rpc_health[rpc_url] = {
        "failed": False,
        "last_success": time.time()
    }


def get_rpc_url(network: str, with_fallback: bool = True) -> str:
    """
    Get the best available RPC URL for a network.

    Tries RPCs in priority order:
    1. Alchemy (if API key set)
    2. Infura (if API key set)
    3. Primary public RPC
    4. Fallback public RPCs

    Args:
        network: Network identifier (e.g., "base-mainnet")
        with_fallback: If True, test RPC connectivity and fallback if needed

    Returns:
        Working RPC URL, or primary if fallback is disabled
    """
    if network not in NETWORKS:
        raise ValueError(f"Unknown network: {network}")

    rpcs = _build_rpc_list(network)
    if not rpcs:
        raise ValueError(f"No RPC URLs configured for {network}")

    if not with_fallback:
        return rpcs[0]

    # Try each RPC in order
    for rpc_url in rpcs:
        if not _is_rpc_healthy(rpc_url):
            continue

        try:
            # Quick connectivity test
            if _test_rpc_connection(rpc_url, network):
                _mark_rpc_success(rpc_url)
                return rpc_url
            else:
                _mark_rpc_failed(rpc_url)
        except Exception:
            _mark_rpc_failed(rpc_url)

    # All RPCs failed, return primary and hope for the best
    return rpcs[0]


def _test_rpc_connection(rpc_url: str, network: str) -> bool:
    """Test if an RPC endpoint is responding"""
    import requests

    network_config = NETWORKS.get(network, {})

    try:
        if network_config.get("type") == "solana":
            # Solana RPC test
            response = requests.post(
                rpc_url,
                json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                timeout=3
            )
            return response.status_code == 200
        else:
            # EVM RPC test - get chain ID
            response = requests.post(
                rpc_url,
                json={"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []},
                timeout=3
            )
            if response.status_code == 200:
                data = response.json()
                return "result" in data
            return False
    except Exception:
        return False


def get_all_rpc_urls(network: str) -> list:
    """Get all configured RPC URLs for a network (for debugging/status)"""
    return _build_rpc_list(network)


def get_rpc_health_status() -> Dict[str, Any]:
    """Get current RPC health status for all networks"""
    status = {}
    for network in NETWORKS:
        rpcs = _build_rpc_list(network)
        status[network] = {
            "primary": rpcs[0] if rpcs else None,
            "fallback_count": len(rpcs) - 1 if rpcs else 0,
            "health": {
                rpc: _rpc_health.get(rpc, {"healthy": True})
                for rpc in rpcs
            }
        }
    return status
