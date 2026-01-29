"""
Circle Cross-Chain Transfer Protocol (CCTP) Client

Enables native USDC transfers between chains without wrapped tokens or liquidity pools.

Supported Routes:
- Base ↔ Arbitrum
- Base ↔ Ethereum
- Arbitrum ↔ Ethereum
- (Solana support planned)

Flow:
1. User burns USDC on source chain via depositForBurn()
2. Circle attestation service validates the burn
3. User (or relayer) mints USDC on destination chain via receiveMessage()

Reference: https://developers.circle.com/stablecoins/cctp
"""

import os
import time
import requests
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from eth_account import Account

from utils.logger import logger
from config import get_rpc_url, NETWORKS


# CCTP Contract Addresses (Mainnet)
# Reference: https://developers.circle.com/stablecoins/docs/evm-smart-contracts
CCTP_CONTRACTS = {
    "eth-mainnet": {
        "token_messenger": "0xBd3fa81B58Ba92a82136038B25aDec7066af3155",
        "message_transmitter": "0x0a992d191DEeC32aFe36203Ad87D7d289a738F81",
        "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "domain": 0,
    },
    "base-mainnet": {
        "token_messenger": "0x1682Ae6375C4E4A97e4B583BC394c861A46D8962",
        "message_transmitter": "0xAD09780d193884d503182aD4588450C416D6F9D4",
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "domain": 6,
    },
    "arbitrum-mainnet": {
        "token_messenger": "0x19330d10D9Cc8751218eaf51E8885D058642E08A",
        "message_transmitter": "0xC30362313FBBA5cf9163F0bb16a0e01f01A896ca",
        "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "domain": 3,
    },
}

# Testnet contracts (Sepolia/Base Sepolia)
CCTP_CONTRACTS_TESTNET = {
    "eth-sepolia": {
        "token_messenger": "0x9f3B8679c73C2Fef8b59B4f3444d4e156fb70AA5",
        "message_transmitter": "0x7865fAfC2db2093669d92c0F33AeEF291086BEFD",
        "usdc": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
        "domain": 0,
    },
}

# Supported bridge routes
SUPPORTED_ROUTES = {
    ("base-mainnet", "arbitrum-mainnet"): True,
    ("base-mainnet", "eth-mainnet"): True,
    ("arbitrum-mainnet", "base-mainnet"): True,
    ("arbitrum-mainnet", "eth-mainnet"): True,
    ("eth-mainnet", "base-mainnet"): True,
    ("eth-mainnet", "arbitrum-mainnet"): True,
}

# Circle Attestation API
ATTESTATION_API_URL = "https://iris-api.circle.com/attestations"
ATTESTATION_API_URL_TESTNET = "https://iris-api-sandbox.circle.com/attestations"

# Minimal ABIs
TOKEN_MESSENGER_ABI = [
    {
        "inputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "destinationDomain", "type": "uint32"},
            {"name": "mintRecipient", "type": "bytes32"},
            {"name": "burnToken", "type": "address"}
        ],
        "name": "depositForBurn",
        "outputs": [{"name": "nonce", "type": "uint64"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

MESSAGE_TRANSMITTER_ABI = [
    {
        "inputs": [
            {"name": "message", "type": "bytes"},
            {"name": "attestation", "type": "bytes"}
        ],
        "name": "receiveMessage",
        "outputs": [{"name": "success", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

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


class CCTPClient:
    """
    Client for Circle Cross-Chain Transfer Protocol.

    Handles USDC bridging between supported EVM chains.
    """

    def __init__(self, source_chain: str, dest_chain: str, testnet: bool = False):
        """
        Initialize CCTP client for a specific bridge route.

        Args:
            source_chain: Source chain identifier (e.g., "base-mainnet")
            dest_chain: Destination chain identifier (e.g., "arbitrum-mainnet")
            testnet: Use testnet contracts (for testing)
        """
        self.source_chain = source_chain
        self.dest_chain = dest_chain
        self.testnet = testnet

        # Validate route
        if not self.is_route_supported(source_chain, dest_chain):
            raise ValueError(f"Bridge route {source_chain} → {dest_chain} not supported")

        # Get contract addresses
        contracts = CCTP_CONTRACTS_TESTNET if testnet else CCTP_CONTRACTS
        self.source_contracts = contracts.get(source_chain)
        self.dest_contracts = contracts.get(dest_chain)

        if not self.source_contracts or not self.dest_contracts:
            raise ValueError(f"CCTP contracts not found for {source_chain} or {dest_chain}")

        # Initialize Web3 connections
        self.source_w3 = Web3(Web3.HTTPProvider(get_rpc_url(source_chain)))
        self.dest_w3 = Web3(Web3.HTTPProvider(get_rpc_url(dest_chain)))

        # Initialize contracts
        self.token_messenger = self.source_w3.eth.contract(
            address=Web3.to_checksum_address(self.source_contracts["token_messenger"]),
            abi=TOKEN_MESSENGER_ABI
        )
        self.usdc_contract = self.source_w3.eth.contract(
            address=Web3.to_checksum_address(self.source_contracts["usdc"]),
            abi=ERC20_ABI
        )
        self.message_transmitter = self.dest_w3.eth.contract(
            address=Web3.to_checksum_address(self.dest_contracts["message_transmitter"]),
            abi=MESSAGE_TRANSMITTER_ABI
        )

        # Attestation API
        self.attestation_url = ATTESTATION_API_URL_TESTNET if testnet else ATTESTATION_API_URL

    @staticmethod
    def is_route_supported(source: str, dest: str) -> bool:
        """Check if a bridge route is supported."""
        return (source, dest) in SUPPORTED_ROUTES

    @staticmethod
    def get_supported_routes() -> list:
        """Get list of supported bridge routes."""
        return [
            {"source": s, "dest": d}
            for (s, d) in SUPPORTED_ROUTES.keys()
        ]

    @staticmethod
    def estimate_bridge_time() -> int:
        """
        Estimate bridge completion time in seconds.
        CCTP typically takes 10-20 minutes for attestation.
        """
        return 900  # 15 minutes average

    def get_usdc_balance(self, address: str) -> Decimal:
        """Get USDC balance on source chain."""
        balance = self.usdc_contract.functions.balanceOf(
            Web3.to_checksum_address(address)
        ).call()
        return Decimal(balance) / Decimal(10**6)

    def check_allowance(self, owner: str) -> Decimal:
        """Check USDC allowance for TokenMessenger."""
        allowance = self.usdc_contract.functions.allowance(
            Web3.to_checksum_address(owner),
            Web3.to_checksum_address(self.source_contracts["token_messenger"])
        ).call()
        return Decimal(allowance) / Decimal(10**6)

    def _address_to_bytes32(self, address: str) -> bytes:
        """Convert address to bytes32 for CCTP recipient format."""
        addr = Web3.to_checksum_address(address)
        return bytes.fromhex(addr[2:].zfill(64))

    def approve_usdc(self, private_key: str, amount: Decimal) -> Dict[str, Any]:
        """
        Approve TokenMessenger to spend USDC.

        Args:
            private_key: Sender's private key
            amount: Amount to approve (in USDC, not wei)

        Returns:
            Transaction result
        """
        try:
            account = Account.from_key(private_key)
            amount_wei = int(amount * Decimal(10**6))

            # Build approval transaction
            tx = self.usdc_contract.functions.approve(
                Web3.to_checksum_address(self.source_contracts["token_messenger"]),
                amount_wei
            ).build_transaction({
                "from": account.address,
                "nonce": self.source_w3.eth.get_transaction_count(account.address),
                "gas": 100000,
                "gasPrice": self.source_w3.eth.gas_price,
                "chainId": self.source_w3.eth.chain_id
            })

            # Sign and send
            signed = account.sign_transaction(tx)
            tx_hash = self.source_w3.eth.send_raw_transaction(signed.raw_transaction)

            # Wait for confirmation
            receipt = self.source_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            return {
                "success": receipt["status"] == 1,
                "tx_hash": tx_hash.hex(),
                "type": "approval"
            }

        except Exception as e:
            logger.error(f"CCTP approval failed: {e}")
            return {"success": False, "error": str(e)}

    def initiate_bridge(
        self,
        private_key: str,
        amount: Decimal,
        recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate a cross-chain USDC transfer.

        Step 1 of the CCTP flow: Burns USDC on source chain.

        Args:
            private_key: Sender's private key
            amount: Amount to bridge (in USDC)
            recipient: Recipient address on destination chain (defaults to sender)

        Returns:
            Dict with tx_hash, message_hash, and nonce for tracking
        """
        try:
            account = Account.from_key(private_key)
            recipient = recipient or account.address
            amount_wei = int(amount * Decimal(10**6))

            # Check balance
            balance = self.get_usdc_balance(account.address)
            if balance < amount:
                return {
                    "success": False,
                    "error": f"Insufficient balance. Have ${balance:.2f}, need ${amount:.2f}"
                }

            # Check and handle allowance
            allowance = self.check_allowance(account.address)
            if allowance < amount:
                logger.info(f"Approving USDC for CCTP bridge...")
                approval = self.approve_usdc(private_key, amount * 2)  # Approve 2x
                if not approval.get("success"):
                    return {"success": False, "error": f"Approval failed: {approval.get('error')}"}

            # Build depositForBurn transaction
            dest_domain = self.dest_contracts["domain"]
            mint_recipient = self._address_to_bytes32(recipient)

            tx = self.token_messenger.functions.depositForBurn(
                amount_wei,
                dest_domain,
                mint_recipient,
                Web3.to_checksum_address(self.source_contracts["usdc"])
            ).build_transaction({
                "from": account.address,
                "nonce": self.source_w3.eth.get_transaction_count(account.address),
                "gas": 300000,
                "gasPrice": self.source_w3.eth.gas_price,
                "chainId": self.source_w3.eth.chain_id
            })

            # Sign and send
            signed = account.sign_transaction(tx)
            tx_hash = self.source_w3.eth.send_raw_transaction(signed.raw_transaction)

            # Wait for confirmation
            receipt = self.source_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt["status"] != 1:
                return {"success": False, "error": "Bridge transaction failed on-chain"}

            # Extract message hash from logs
            message_hash = self._extract_message_hash(receipt)

            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "message_hash": message_hash,
                "source_chain": self.source_chain,
                "dest_chain": self.dest_chain,
                "amount": float(amount),
                "recipient": recipient,
                "status": "pending_attestation",
                "estimated_completion": self.estimate_bridge_time()
            }

        except Exception as e:
            logger.error(f"CCTP bridge initiation failed: {e}")
            return {"success": False, "error": str(e)}

    def _extract_message_hash(self, receipt: Dict) -> Optional[str]:
        """Extract message hash from transaction receipt logs."""
        # MessageSent event topic
        message_sent_topic = Web3.keccak(text="MessageSent(bytes)")

        for log in receipt.get("logs", []):
            if log["topics"][0] == message_sent_topic:
                # Message is in the data field
                message = log["data"]
                return Web3.keccak(hexstr=message).hex()

        return None

    def check_attestation(self, message_hash: str) -> Tuple[bool, Optional[str]]:
        """
        Check if attestation is ready from Circle's API.

        Args:
            message_hash: The message hash from initiate_bridge

        Returns:
            (is_ready, attestation_signature)
        """
        try:
            response = requests.get(
                f"{self.attestation_url}/{message_hash}",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                if status == "complete":
                    return True, data.get("attestation")
                else:
                    return False, None

            elif response.status_code == 404:
                # Attestation not yet available
                return False, None
            else:
                logger.warning(f"Attestation API error: {response.status_code}")
                return False, None

        except Exception as e:
            logger.error(f"Attestation check failed: {e}")
            return False, None

    def complete_bridge(
        self,
        private_key: str,
        message: bytes,
        attestation: str
    ) -> Dict[str, Any]:
        """
        Complete the bridge on destination chain.

        Step 2 of CCTP flow: Mints USDC on destination chain.

        Args:
            private_key: Private key for gas on destination chain
            message: The original message from source chain
            attestation: The attestation signature from Circle

        Returns:
            Transaction result
        """
        try:
            account = Account.from_key(private_key)
            attestation_bytes = bytes.fromhex(attestation.replace("0x", ""))

            tx = self.message_transmitter.functions.receiveMessage(
                message,
                attestation_bytes
            ).build_transaction({
                "from": account.address,
                "nonce": self.dest_w3.eth.get_transaction_count(account.address),
                "gas": 300000,
                "gasPrice": self.dest_w3.eth.gas_price,
                "chainId": self.dest_w3.eth.chain_id
            })

            signed = account.sign_transaction(tx)
            tx_hash = self.dest_w3.eth.send_raw_transaction(signed.raw_transaction)

            receipt = self.dest_w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            return {
                "success": receipt["status"] == 1,
                "tx_hash": tx_hash.hex(),
                "chain": self.dest_chain,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"CCTP bridge completion failed: {e}")
            return {"success": False, "error": str(e)}

    def poll_and_complete(
        self,
        private_key: str,
        message_hash: str,
        message: bytes,
        max_wait_seconds: int = 1800,
        poll_interval: int = 30
    ) -> Dict[str, Any]:
        """
        Poll for attestation and complete bridge automatically.

        Convenience method that combines check_attestation + complete_bridge.

        Args:
            private_key: Private key for completing on destination
            message_hash: Message hash from initiate_bridge
            message: Original message bytes
            max_wait_seconds: Maximum wait time (default 30 min)
            poll_interval: Seconds between polls

        Returns:
            Final transaction result
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_seconds:
            is_ready, attestation = self.check_attestation(message_hash)

            if is_ready and attestation:
                logger.info(f"Attestation ready, completing bridge...")
                return self.complete_bridge(private_key, message, attestation)

            logger.info(f"Waiting for attestation... ({int(time.time() - start_time)}s)")
            time.sleep(poll_interval)

        return {
            "success": False,
            "error": "Attestation timeout",
            "message_hash": message_hash
        }


def get_cctp_client(source: str, dest: str) -> CCTPClient:
    """Factory function to create CCTP client."""
    return CCTPClient(source, dest)


def preview_bridge(
    source_chain: str,
    dest_chain: str,
    amount: float,
    wallet_address: str
) -> Dict[str, Any]:
    """
    Preview a cross-chain bridge operation.

    Used by AI agent to show user what will happen.
    """
    if not CCTPClient.is_route_supported(source_chain, dest_chain):
        return {
            "success": False,
            "error": f"Route {source_chain} → {dest_chain} not supported"
        }

    try:
        client = CCTPClient(source_chain, dest_chain)

        # Check balance
        balance = client.get_usdc_balance(wallet_address)

        source_name = NETWORKS.get(source_chain, {}).get("name", source_chain)
        dest_name = NETWORKS.get(dest_chain, {}).get("name", dest_chain)

        if balance < Decimal(str(amount)):
            return {
                "success": False,
                "error": f"Insufficient balance on {source_name}. Have ${balance:.2f}"
            }

        return {
            "success": True,
            "preview": {
                "source": source_name,
                "dest": dest_name,
                "amount": amount,
                "estimated_time_minutes": client.estimate_bridge_time() // 60,
                "gas_estimate": "~$0.50",  # Rough estimate
                "available_balance": float(balance)
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
