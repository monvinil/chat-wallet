"""
Circle Programmable Wallets Client

Integration with Circle's Web3 Services:
- Programmable Wallets (user-controlled and developer-controlled)
- Gas Station (gasless transactions)
- CCTP (cross-chain transfers)

Docs: https://developers.circle.com/w3s
"""

import os
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime

from utils.logger import logger


class CircleClient:
    """
    Client for Circle Programmable Wallets API

    Environment variables required:
    - CIRCLE_API_KEY: Your Circle API key
    - CIRCLE_ENTITY_SECRET: Entity secret for wallet operations
    """

    BASE_URL = "https://api.circle.com/v1/w3s"

    def __init__(self):
        self.api_key = os.getenv("CIRCLE_API_KEY")
        self.entity_secret = os.getenv("CIRCLE_ENTITY_SECRET")

        if not self.api_key:
            logger.warning("CIRCLE_API_KEY not set - Circle features disabled")

    @property
    def is_configured(self) -> bool:
        """Check if Circle API is configured"""
        return bool(self.api_key and self.entity_secret)

    def _headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, data: dict = None) -> Dict[str, Any]:
        """Make API request"""
        url = f"{self.BASE_URL}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self._headers(), params=data)
            elif method == "POST":
                response = requests.post(url, headers=self._headers(), json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self._headers(), json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self._headers())
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"Circle API error: {e}")
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            logger.error(f"Circle API request failed: {e}")
            return {"error": str(e)}

    # === Wallet Set Management ===

    def create_wallet_set(self, name: str) -> Dict[str, Any]:
        """
        Create a new wallet set.

        A wallet set is a collection of wallets that share the same encryption.
        """
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("POST", "/developer/walletSets", {
            "name": name,
            "entitySecretCiphertext": self.entity_secret
        })

    def list_wallet_sets(self) -> List[Dict[str, Any]]:
        """List all wallet sets"""
        if not self.is_configured:
            return []

        result = self._request("GET", "/developer/walletSets")
        return result.get("data", {}).get("walletSets", [])

    # === Wallet Management ===

    def create_wallet(
        self,
        wallet_set_id: str,
        blockchain: str = "ETH-BASE",
        count: int = 1
    ) -> Dict[str, Any]:
        """
        Create a new wallet in a wallet set.

        Args:
            wallet_set_id: ID of the wallet set
            blockchain: Blockchain identifier (ETH-BASE, ETH-ARB, SOL, etc.)
            count: Number of wallets to create

        Returns:
            Wallet creation response with wallet IDs
        """
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("POST", "/developer/wallets", {
            "walletSetId": wallet_set_id,
            "blockchains": [blockchain],
            "count": count,
            "entitySecretCiphertext": self.entity_secret
        })

    def get_wallet(self, wallet_id: str) -> Dict[str, Any]:
        """Get wallet details by ID"""
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("GET", f"/wallets/{wallet_id}")

    def get_wallet_balance(self, wallet_id: str) -> Dict[str, Any]:
        """Get wallet token balances"""
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("GET", f"/wallets/{wallet_id}/balances")

    # === Transaction Management ===

    def create_transfer(
        self,
        wallet_id: str,
        token_id: str,
        destination_address: str,
        amount: str,
        fee_level: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Create an outbound transfer.

        Args:
            wallet_id: Source wallet ID
            token_id: Token to transfer (e.g., USDC token ID)
            destination_address: Recipient address
            amount: Amount to send (as string for precision)
            fee_level: Gas fee level (LOW, MEDIUM, HIGH)

        Returns:
            Transfer response with transaction ID
        """
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("POST", "/developer/transactions/transfer", {
            "walletId": wallet_id,
            "tokenId": token_id,
            "destinationAddress": destination_address,
            "amounts": [amount],
            "feeLevel": fee_level,
            "entitySecretCiphertext": self.entity_secret
        })

    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Get transaction status and details"""
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("GET", f"/transactions/{transaction_id}")

    def list_transactions(
        self,
        wallet_id: str = None,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """List transactions, optionally filtered by wallet"""
        if not self.is_configured:
            return []

        params = {"pageSize": page_size}
        if wallet_id:
            params["walletIds"] = wallet_id

        result = self._request("GET", "/transactions", params)
        return result.get("data", {}).get("transactions", [])

    # === Gas Station (Gasless Transactions) ===

    def get_gas_station_config(self) -> Dict[str, Any]:
        """Get Gas Station configuration"""
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("GET", "/gasStation/config")

    def sponsor_transaction(
        self,
        wallet_id: str,
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit a transaction for gas sponsorship.

        The transaction will be executed with gas fees paid by your Gas Station balance.
        """
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("POST", "/gasStation/sponsor", {
            "walletId": wallet_id,
            "transaction": transaction_data,
            "entitySecretCiphertext": self.entity_secret
        })

    # === CCTP (Cross-Chain Transfer Protocol) ===

    def create_cctp_transfer(
        self,
        source_wallet_id: str,
        destination_address: str,
        destination_chain: str,
        amount: str
    ) -> Dict[str, Any]:
        """
        Create a cross-chain USDC transfer using CCTP.

        Args:
            source_wallet_id: Source wallet ID
            destination_address: Recipient address on destination chain
            destination_chain: Target chain (e.g., "ETH-ARB", "ETH-BASE")
            amount: Amount to transfer

        Returns:
            CCTP transfer response
        """
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("POST", "/developer/cctp/transfers", {
            "walletId": source_wallet_id,
            "destinationAddress": destination_address,
            "destinationChain": destination_chain,
            "amount": amount,
            "entitySecretCiphertext": self.entity_secret
        })

    def get_cctp_transfer(self, transfer_id: str) -> Dict[str, Any]:
        """Get CCTP transfer status"""
        if not self.is_configured:
            return {"error": "Circle API not configured"}

        return self._request("GET", f"/cctp/transfers/{transfer_id}")


# === Singleton instance ===
_client: Optional[CircleClient] = None


def get_circle_client() -> CircleClient:
    """Get or create Circle client instance"""
    global _client
    if _client is None:
        _client = CircleClient()
    return _client


def is_circle_available() -> bool:
    """Check if Circle integration is available"""
    return get_circle_client().is_configured


# === Helper Functions ===

def get_usdc_token_id(chain: str) -> str:
    """Get USDC token ID for a chain"""
    # These are Circle's internal token IDs
    # You'll need to fetch these from Circle's API or docs
    token_ids = {
        "ETH-BASE": "usdc-base",
        "ETH-ARB": "usdc-arbitrum",
        "ETH": "usdc-ethereum",
        "SOL": "usdc-solana"
    }
    return token_ids.get(chain, "usdc-base")


def map_network_to_circle_chain(network: str) -> str:
    """Map our network names to Circle chain identifiers"""
    mapping = {
        "base-mainnet": "ETH-BASE",
        "arbitrum-mainnet": "ETH-ARB",
        "eth-mainnet": "ETH",
        "solana-mainnet": "SOL"
    }
    return mapping.get(network, "ETH-BASE")
