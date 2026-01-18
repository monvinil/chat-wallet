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
            encrypted_data: Encrypted wallet data (base64 string from Fernet)
            key: Fernet key used for encryption (base64 encoded)

        Returns:
            Decrypted wallet data, or None if decryption fails
        """
        try:
            from cryptography.fernet import Fernet
            f = Fernet(key.encode())
            # encrypted_data is already base64 from Fernet.encrypt()
            decrypted = f.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt wallet: {e}")
            return None

    @staticmethod
    def _derive_solana_keypair(mnemonic_phrase: str) -> Optional[Dict[str, str]]:
        """
        Derive Solana keypair from mnemonic using BIP44 derivation path.
        Path: m/44'/501'/0'/0' (Solana standard)
        """
        try:
            from bip_utils import (
                Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
            )
            from solders.keypair import Keypair
            import base58

            # Generate seed from mnemonic
            seed = Bip39SeedGenerator(mnemonic_phrase).Generate()

            # Derive Solana key using BIP44
            # Path: m/44'/501'/0'/0'
            bip44_ctx = Bip44.FromSeed(seed, Bip44Coins.SOLANA)
            derived = bip44_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)

            # Get the raw private key bytes (32 bytes)
            private_key_bytes = derived.PrivateKey().Raw().ToBytes()

            # Create Solana keypair from seed
            keypair = Keypair.from_seed(private_key_bytes)

            return {
                "private_key": base58.b58encode(bytes(keypair)).decode(),
                "address": str(keypair.pubkey())
            }
        except ImportError as e:
            logger.warning(f"Solana libraries not installed: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to derive Solana keypair: {e}")
            return None

    @staticmethod
    def create_new_wallet() -> Optional[Dict[str, Any]]:
        """Create a new multi-chain wallet with mnemonic seed phrase"""
        try:
            from eth_account import Account
            from mnemonic import Mnemonic

            # Generate 12-word mnemonic
            mnemo = Mnemonic("english")
            mnemonic_phrase = mnemo.generate(strength=128)  # 12 words

            # Enable HD wallet functionality
            Account.enable_unaudited_hdwallet_features()

            # Derive EVM account from mnemonic (first address: m/44'/60'/0'/0/0)
            account = Account.from_mnemonic(mnemonic_phrase)
            evm_private_key = account.key.hex()
            if not evm_private_key.startswith("0x"):
                evm_private_key = "0x" + evm_private_key
            evm_address = account.address

            # Derive Solana keypair from same mnemonic
            solana_keys = WalletManager._derive_solana_keypair(mnemonic_phrase)

            # Build multi-chain wallet data
            wallet_data = {
                "mnemonic": mnemonic_phrase,
                "evm": {
                    "private_key": evm_private_key,
                    "address": evm_address
                },
                # Legacy fields for backwards compatibility
                "private_key": evm_private_key,
                "address": evm_address,
                "network": "base-sepolia",
                "type": "multi-chain"
            }

            # Add Solana if derivation succeeded
            if solana_keys:
                wallet_data["solana"] = solana_keys

            return {
                "address": evm_address,  # Primary address is EVM
                "solana_address": solana_keys["address"] if solana_keys else None,
                "mnemonic": mnemonic_phrase,
                "wallet_data": json.dumps(wallet_data),
                "network": "base-sepolia",
                "type": "multi-chain"
            }
        except Exception as e:
            st.error(f"Failed to create wallet: {e}")
            return None

    @staticmethod
    def import_wallet(private_key_or_mnemonic: str) -> Optional[Dict[str, Any]]:
        """Import wallet from private key or seed phrase (multi-chain if mnemonic)"""
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

                # Derive EVM account from mnemonic
                account = Account.from_mnemonic(input_str)
                evm_private_key = account.key.hex()
                if not evm_private_key.startswith("0x"):
                    evm_private_key = "0x" + evm_private_key
                evm_address = account.address

                # Derive Solana keypair from same mnemonic
                solana_keys = WalletManager._derive_solana_keypair(input_str)

                # Build multi-chain wallet data
                wallet_data = {
                    "mnemonic": input_str,
                    "evm": {
                        "private_key": evm_private_key,
                        "address": evm_address
                    },
                    # Legacy fields for backwards compatibility
                    "private_key": evm_private_key,
                    "address": evm_address,
                    "network": "base-sepolia",
                    "type": "multi-chain"
                }

                # Add Solana if derivation succeeded
                if solana_keys:
                    wallet_data["solana"] = solana_keys

                return {
                    "address": evm_address,
                    "solana_address": solana_keys["address"] if solana_keys else None,
                    "wallet_data": json.dumps(wallet_data),
                    "network": "base-sepolia",
                    "type": "multi-chain"
                }
            else:
                # Treat as private key (EVM only - can't derive Solana)
                private_key = input_str
                if not private_key.startswith("0x"):
                    private_key = "0x" + private_key

                # Create account from private key
                account = Account.from_key(private_key)
                address = account.address

                # Wallet data to encrypt (EVM only)
                wallet_data = {
                    "evm": {
                        "private_key": private_key,
                        "address": address
                    },
                    # Legacy fields
                    "private_key": private_key,
                    "address": address,
                    "network": "base-sepolia",
                    "type": "evm"
                }

                return {
                    "address": address,
                    "solana_address": None,  # Can't derive Solana from EVM private key
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
        """Lock wallet (clear decryption key from memory and cookie)"""
        if "wallet_key" in st.session_state:
            del st.session_state.wallet_key
        st.session_state.wallet_locked = True

        # Also clear wallet key cookie so it stays locked on refresh
        from session_manager import SessionManager
        SessionManager.clear_wallet_key()

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
        Verify password against stored hash (bcrypt or legacy SHA-256)

        Args:
            password: User-provided password
            stored_hash: Stored password hash

        Returns:
            True if password matches, False otherwise
        """
        try:
            return PasswordEncryption.verify_password(password, stored_hash)
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
            logger.debug("unlock_wallet_with_password: No wallet_encrypted in session")
            return False
        if "wallet_salt" not in st.session_state:
            logger.debug("unlock_wallet_with_password: No wallet_salt in session")
            return False

        try:
            from cryptography.fernet import Fernet
            import base64

            salt_hex = st.session_state.wallet_salt
            encrypted_data = st.session_state.wallet_encrypted

            # Re-derive key from password using stored salt
            salt = bytes.fromhex(salt_hex)
            key = PasswordEncryption.derive_key(password, salt)
            fernet_key = base64.urlsafe_b64encode(key).decode()

            # Try to decrypt wallet data to verify password is correct
            try:
                f = Fernet(fernet_key.encode())
                decrypted = f.decrypt(encrypted_data.encode())
                # Password is correct, store key in session
                st.session_state.wallet_key = fernet_key
                st.session_state.wallet_locked = False
                st.session_state.wallet_data = decrypted.decode()

                # Defer wallet key save to next render cycle (to let JS execute)
                # The JS component needs to render to set the cookie
                st.session_state._pending_wallet_key_save = fernet_key

                return True
            except Exception as e:
                logger.debug(f"Wallet decryption failed: {type(e).__name__}")
                return False

        except Exception as e:
            logger.error(f"unlock_wallet_with_password error: {e}")
            return False
