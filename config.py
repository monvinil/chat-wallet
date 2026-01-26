"""
Configuration for Chat Wallet
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Config (you'll add these after setup)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # For admin operations

# Anthropic API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Supported Networks
NETWORKS = {
    # === MAINNETS ===
    "eth-mainnet": {
        "name": "Ethereum",
        "chain_id": 1,
        "type": "evm",
        "testnet": False,
        "rpc_url": "https://eth.llamarpc.com",
        "explorer": "https://etherscan.io",
        "usdc_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    },
    "base-mainnet": {
        "name": "Base",
        "chain_id": 8453,
        "type": "evm",
        "testnet": False,
        "rpc_url": "https://mainnet.base.org",
        "explorer": "https://basescan.org",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    },
    "arbitrum-mainnet": {
        "name": "Arbitrum",
        "chain_id": 42161,
        "type": "evm",
        "testnet": False,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "explorer": "https://arbiscan.io",
        "usdc_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    },
    "solana-mainnet": {
        "name": "Solana",
        "type": "solana",
        "testnet": False,
        "rpc_url": "https://api.mainnet-beta.solana.com",
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
        "explorer": "https://sepolia.etherscan.io",
        "usdc_address": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
    },
    "arc-testnet": {
        "name": "Arc",
        "chain_id": 5042002,
        "type": "evm",
        "testnet": True,
        "rpc_url": "https://rpc.testnet.arc.network",
        "explorer": "https://testnet.arcscan.app",
        "usdc_address": "0x3600000000000000000000000000000000000000"
    }
}

# Fee Structure
FEE_FLAT = 0.005  # $0.005 = 0.5 cents
FEE_PERCENTAGE = 0.002  # 0.2%
FEE_MAX = 3.0  # $3 cap

def calculate_fee(amount_usd: float) -> float:
    """Calculate transaction fee based on amount"""
    fee = FEE_FLAT + (amount_usd * FEE_PERCENTAGE)
    return min(fee, FEE_MAX)
