"""
Meta-transaction utilities for gasless transfers
Users sign messages (free), backend executes transactions
"""

import json
import time
from typing import Dict, Any, Optional
from eth_account import Account
from eth_account.messages import encode_structured_data
from web3 import Web3


class MetaTransaction:
    """Handle meta-transactions (gasless transactions)"""

    # EIP-712 Domain
    DOMAIN = {
        "name": "ChatWallet",
        "version": "1",
        "chainId": 84532,  # Base Sepolia
        "verifyingContract": "0x0000000000000000000000000000000000000000"
    }

    # EIP-712 Types
    TYPES = {
        "MetaTx": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "currency", "type": "string"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"}
        ]
    }

    @staticmethod
    def create_message(
        from_address: str,
        to_address: str,
        amount: float,
        currency: str = "USDC",
        nonce: int = 0,
        deadline_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Create a meta-transaction message"""

        # Convert amount to wei (USDC has 6 decimals)
        amount_wei = int(amount * 1e6)

        # Deadline timestamp
        deadline = int(time.time()) + deadline_seconds

        message = {
            "from": Web3.to_checksum_address(from_address),
            "to": Web3.to_checksum_address(to_address),
            "amount": amount_wei,
            "currency": currency,
            "nonce": nonce,
            "deadline": deadline
        }

        return message

    @staticmethod
    def sign_message(message: Dict[str, Any], private_key: str) -> str:
        """Sign a meta-transaction message"""

        # Create EIP-712 structured data
        structured_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "MetaTx": MetaTransaction.TYPES["MetaTx"]
            },
            "primaryType": "MetaTx",
            "domain": MetaTransaction.DOMAIN,
            "message": message
        }

        # Sign the structured data
        encoded_data = encode_structured_data(structured_data)
        account = Account.from_key(private_key)
        signed = account.sign_message(encoded_data)

        return signed.signature.hex()

    @staticmethod
    def verify_signature(
        message: Dict[str, Any],
        signature: str,
        expected_signer: str
    ) -> bool:
        """Verify a meta-transaction signature"""

        try:
            # Create EIP-712 structured data
            structured_data = {
                "types": {
                    "EIP712Domain": [
                        {"name": "name", "type": "string"},
                        {"name": "version", "type": "string"},
                        {"name": "chainId", "type": "uint256"},
                        {"name": "verifyingContract", "type": "address"}
                    ],
                    "MetaTx": MetaTransaction.TYPES["MetaTx"]
                },
                "primaryType": "MetaTx",
                "domain": MetaTransaction.DOMAIN,
                "message": message
            }

            # Recover signer from signature
            encoded_data = encode_structured_data(structured_data)
            recovered_address = Account.recover_message(
                encoded_data,
                signature=bytes.fromhex(signature.replace("0x", ""))
            )

            # Check if signer matches
            return recovered_address.lower() == expected_signer.lower()

        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False

    @staticmethod
    def is_expired(message: Dict[str, Any]) -> bool:
        """Check if message deadline has passed"""
        current_time = int(time.time())
        deadline = message.get("deadline", 0)
        return current_time > deadline

    @staticmethod
    def serialize_for_storage(message: Dict[str, Any], signature: str) -> str:
        """Serialize meta-tx for storage"""
        data = {
            "message": message,
            "signature": signature,
            "timestamp": int(time.time())
        }
        return json.dumps(data)

    @staticmethod
    def deserialize(data: str) -> tuple:
        """Deserialize stored meta-tx"""
        parsed = json.loads(data)
        return parsed["message"], parsed["signature"]
