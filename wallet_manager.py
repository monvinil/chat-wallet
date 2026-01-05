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
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

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
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return Fernet.generate_key()

    @staticmethod
    def encrypt_wallet_data(wallet_data: str, password: str) -> Dict[str, str]:
        """Encrypt wallet private key with password"""
        # Generate a random salt
        salt = os.urandom(16)

        # Derive key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = Fernet.generate_key()

        # Encrypt the wallet data
        f = Fernet(key)
        encrypted_data = f.encrypt(wallet_data.encode())

        return {
            "encrypted_data": encrypted_data.hex(),
            "salt": salt.hex(),
            "key": key.decode()  # In production, store this securely!
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
        """Create a new CDP wallet (EVM)"""
        if not CDP_AVAILABLE:
            st.error("CDP SDK not available")
            return None

        try:
            # Create new wallet
            wallet = Wallet.create(network_id="base-sepolia")

            # Export wallet data (contains private key)
            wallet_data = wallet.export_data()

            # Get address
            address = wallet.default_address.address_id

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
    def import_wallet(seed_phrase: str) -> Optional[Dict[str, Any]]:
        """Import wallet from seed phrase"""
        if not CDP_AVAILABLE:
            st.error("CDP SDK not available")
            return None

        try:
            # Import wallet using seed
            wallet_data = {
                "seed": seed_phrase,
                "network_id": "base-sepolia"
            }

            wallet = Wallet.import_data(wallet_data)
            address = wallet.default_address.address_id

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
    def get_wallet_from_session() -> Optional[Any]:
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

        if not CDP_AVAILABLE:
            return None

        try:
            wallet_data = json.loads(wallet_data_str)
            wallet = Wallet.import_data(wallet_data)
            return wallet
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
