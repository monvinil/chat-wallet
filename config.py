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

# CDP Config
CDP_API_KEY_NAME = os.getenv("CDP_API_KEY_NAME", "")
CDP_API_KEY_PRIVATE_KEY = os.getenv("CDP_API_KEY_PRIVATE_KEY", "")

# Supported Networks
NETWORKS = {
    "base-sepolia": {
        "name": "Base Sepolia",
        "chain_id": 84532,
        "type": "evm",
        "testnet": True,
        "rpc_url": "https://sepolia.base.org",
        "explorer": "https://sepolia.basescan.org",
        "usdc_address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
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
    "arbitrum-sepolia": {
        "name": "Arbitrum Sepolia",
        "chain_id": 421614,
        "type": "evm",
        "testnet": True,
        "rpc_url": "https://sepolia-rollup.arbitrum.io/rpc",
        "explorer": "https://sepolia.arbiscan.io",
        "usdc_address": "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"
    },
    "polygon-amoy": {
        "name": "Polygon Amoy",
        "chain_id": 80002,
        "type": "evm",
        "testnet": True,
        "rpc_url": "https://rpc-amoy.polygon.technology",
        "explorer": "https://www.oklink.com/amoy",
        "usdc_address": "0x41E94Eb019C0762f9Bfcf9Fb1E58725BfB0e7582"
    },
    "solana-devnet": {
        "name": "Solana Devnet",
        "type": "solana",
        "testnet": True,
        "rpc_url": "https://api.devnet.solana.com",
        "explorer": "https://explorer.solana.com/?cluster=devnet",
        "usdc_address": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    },
    "solana-mainnet": {
        "name": "Solana",
        "type": "solana",
        "testnet": False,
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "explorer": "https://explorer.solana.com",
        "usdc_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
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
