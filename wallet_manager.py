"""
Non-custodial wallet management
Handles wallet creation, import, and encrypted storage
"""

import os
import json
import streamlit as st
from typing import Optional, Dict, Any

# Import centralized encryption utilities
from utils.encryption import PasswordEncryption
from utils.logger import logger

try:
    from cdp import Wallet
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False


class WalletManager:
    """Manages non-custodial wallet operations"""

    @staticmethod
    def encrypt_wallet_data(wallet_data: str, password: str) -> Dict[str, str]:
        """
        Encrypt wallet private key with password

        Args:
            wallet_data: Plain text wallet data (private key or seed)
            password: User password

        Returns:
            Dictionary with encrypted_data, salt, and key
        """
        return PasswordEncryption.encrypt(wallet_data, password)

    @staticmethod
    def decrypt_wallet_data(encrypted_data: str, key: str) -> Optional[str]:
        """
        Decrypt wallet data using stored key

        Args:
            encrypted_data: Encrypted wallet data (hex string)
            key: Fernet key used for encryption

        Returns:
            Decrypted wallet data, or None if decryption fails
        """
        try:
            from cryptography.fernet import Fernet
            f = Fernet(key.encode())
            decrypted = f.decrypt(bytes.fromhex(encrypted_data))
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt wallet: {e}")
            st.error(f"Failed to decrypt wallet: {e}")
            return None

    @staticmethod
    def create_new_wallet() -> Optional[Dict[str, Any]]:
        """Create a new EVM wallet with mnemonic seed phrase"""
        try:
            from eth_account import Account
            from mnemonic import Mnemonic

            # Generate 12-word mnemonic
            mnemo = Mnemonic("english")
            mnemonic_phrase = mnemo.generate(strength=128)  # 12 words

            # Enable HD wallet functionality
            Account.enable_unaudited_hdwallet_features()

            # Derive account from mnemonic (first address: m/44'/60'/0'/0/0)
            account = Account.from_mnemonic(mnemonic_phrase)
            private_key = account.key.hex()
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
            address = account.address

            # Wallet data to encrypt
            wallet_data = {
                "private_key": private_key,
                "mnemonic": mnemonic_phrase,
                "address": address,
                "network": "base-sepolia",
                "type": "evm"
            }

            return {
                "address": address,
                "mnemonic": mnemonic_phrase,
                "wallet_data": json.dumps(wallet_data),
                "network": "base-sepolia",
                "type": "evm"
            }
        except Exception as e:
            st.error(f"Failed to create wallet: {e}")
            return None

    @staticmethod
    def import_wallet(private_key_or_mnemonic: str) -> Optional[Dict[str, Any]]:
        """Import wallet from private key or seed phrase"""
        try:
            from eth_account import Account
            from mnemonic import Mnemonic

            input_str = private_key_or_mnemonic.strip()

            # Check if input is a mnemonic (12 or 24 words)
            words = input_str.split()
            is_mnemonic = len(words) in [12, 24]

            if is_mnemonic:
                # Validate mnemonic
                mnemo = Mnemonic("english")
                if not mnemo.check(input_str):
                    st.error("Invalid seed phrase")
                    return None

                # Enable HD wallet functionality
                Account.enable_unaudited_hdwallet_features()

                # Derive account from mnemonic
                account = Account.from_mnemonic(input_str)
                private_key = account.key.hex()
                if not private_key.startswith("0x"):
                    private_key = "0x" + private_key
                address = account.address

                # Wallet data to encrypt
                wallet_data = {
                    "private_key": private_key,
                    "mnemonic": input_str,
                    "address": address,
                    "network": "base-sepolia",
                    "type": "evm"
                }
            else:
                # Treat as private key
                private_key = input_str
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
        st.session_state.wallet_salt = encrypted["salt"]  # Store salt for password re-derivation
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

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password for secure storage (separate from encryption)

        Args:
            password: User password

        Returns:
            SHA-256 hash (hex string)
        """
        return PasswordEncryption.hash_password(password)

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """
        Verify password against stored hash

        Args:
            password: User-provided password
            stored_hash: Stored password hash (SHA-256 hex)

        Returns:
            True if password matches, False otherwise
        """
        try:
            password_hash = PasswordEncryption.hash_password(password)
            return password_hash == stored_hash
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def unlock_wallet_with_password(password: str) -> bool:
        """
        Unlock wallet using password to re-derive the encryption key.
        Returns: True if successful, False otherwise
        """
        if "wallet_encrypted" not in st.session_state:
            return False
        if "wallet_salt" not in st.session_state:
            return False

        try:
            # Re-derive key from password using stored salt
            salt = bytes.fromhex(st.session_state.wallet_salt)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(password.encode())
            fernet_key = base64.urlsafe_b64encode(key).decode()

            # Try to decrypt wallet data to verify password is correct
            try:
                f = Fernet(fernet_key.encode())
                decrypted = f.decrypt(bytes.fromhex(st.session_state.wallet_encrypted))
                # Password is correct, store key in session
                st.session_state.wallet_key = fernet_key
                st.session_state.wallet_locked = False
                return True
            except Exception:
                return False

        except Exception:
            return False
