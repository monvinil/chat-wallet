"""
Non-custodial wallet management
Handles wallet creation, import, and encrypted storage
"""

import os
import json
import hashlib
import streamlit as st
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

try:
    from cdp import Wallet
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False


class WalletManager:
    """Manages non-custodial wallet operations"""

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key

    @staticmethod
    def encrypt_wallet_data(wallet_data: str, password: str) -> Dict[str, str]:
        """Encrypt wallet private key with password"""
        # Generate a random salt
        salt = os.urandom(16)

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())

        # Convert to Fernet key format (base64 encoded)
        import base64
        fernet_key = base64.urlsafe_b64encode(key)

        # Encrypt the wallet data
        f = Fernet(fernet_key)
        encrypted_data = f.encrypt(wallet_data.encode())

        return {
            "encrypted_data": encrypted_data.hex(),
            "salt": salt.hex(),
            "key": fernet_key.decode()  # Store this for decryption
        }

    @staticmethod
    def decrypt_wallet_data(encrypted_data: str, key: str) -> Optional[str]:
        """Decrypt wallet data"""
        try:
            f = Fernet(key.encode())
            decrypted = f.decrypt(bytes.fromhex(encrypted_data))
            return decrypted.decode()
        except Exception as e:
            st.error(f"Failed to decrypt wallet: {e}")
            return None

    @staticmethod
    def create_new_wallet() -> Optional[Dict[str, Any]]:
        """Create a new EVM wallet"""
        try:
            # Use web3 to create a new wallet (doesn't require CDP)
            from eth_account import Account
            import secrets

            # Generate a new private key
            private_key = "0x" + secrets.token_hex(32)

            # Create account from private key
            account = Account.from_key(private_key)
            address = account.address

            # Wallet data to encrypt
            wallet_data = {
                "private_key": private_key,
                "address": address,
                "network": "base-sepolia",
                "type": "evm"
            }

            return {
                "address": address,
                "wallet_data": json.dumps(wallet_data),
                "network": "base-sepolia",
                "type": "evm"
            }
        except Exception as e:
            st.error(f"Failed to create wallet: {e}")
            return None

    @staticmethod
    def import_wallet(private_key: str) -> Optional[Dict[str, Any]]:
        """Import wallet from private key"""
        try:
            from eth_account import Account

            # Clean up private key format
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key

            # Create account from private key
            account = Account.from_key(private_key)
            address = account.address

            # Wallet data to encrypt
            wallet_data = {
                "private_key": private_key,
                "address": address,
                "network": "base-sepolia",
                "type": "evm"
            }

            return {
                "address": address,
                "wallet_data": json.dumps(wallet_data),
                "network": "base-sepolia",
                "type": "evm"
            }
        except Exception as e:
            st.error(f"Failed to import wallet: {e}")
            return None

    @staticmethod
    def get_wallet_from_session() -> Optional[Dict[str, Any]]:
        """Load wallet from session state"""
        if "wallet_encrypted" not in st.session_state:
            return None

        if "wallet_key" not in st.session_state:
            return None

        # Decrypt wallet data
        wallet_data_str = WalletManager.decrypt_wallet_data(
            st.session_state.wallet_encrypted,
            st.session_state.wallet_key
        )

        if not wallet_data_str:
            return None

        try:
            wallet_data = json.loads(wallet_data_str)
            return wallet_data
        except Exception as e:
            st.error(f"Failed to load wallet: {e}")
            return None

    @staticmethod
    def save_wallet_to_session(wallet_data: str, password: str):
        """Encrypt and save wallet to session state"""
        encrypted = WalletManager.encrypt_wallet_data(wallet_data, password)

        # Store in session state (in browser memory only)
        st.session_state.wallet_encrypted = encrypted["encrypted_data"]
        st.session_state.wallet_key = encrypted["key"]
        st.session_state.wallet_locked = False

    @staticmethod
    def lock_wallet():
        """Lock wallet (clear decryption key from memory)"""
        if "wallet_key" in st.session_state:
            del st.session_state.wallet_key
        st.session_state.wallet_locked = True

    @staticmethod
    def is_wallet_unlocked() -> bool:
        """Check if wallet is unlocked"""
        return (
            "wallet_encrypted" in st.session_state and
            "wallet_key" in st.session_state and
            not st.session_state.get("wallet_locked", True)
        )
