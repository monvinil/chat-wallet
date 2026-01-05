"""
Unit tests for WalletManager
"""

import pytest
import json
from unittest.mock import patch, MagicMock

# Mock streamlit before importing
import sys
sys.modules['streamlit'] = MagicMock()

from wallet_manager import WalletManager


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a non-empty string"""
        password = "testpassword123"
        hashed = WalletManager.hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should not be plaintext

    def test_hash_password_different_for_same_password(self):
        """Test that hashing same password twice gives different results (random salt)"""
        password = "testpassword123"
        hash1 = WalletManager.hash_password(password)
        hash2 = WalletManager.hash_password(password)

        assert hash1 != hash2  # Different salt = different hash

    def test_verify_password_correct(self):
        """Test that correct password verifies successfully"""
        password = "mysecurepassword"
        hashed = WalletManager.hash_password(password)

        assert WalletManager.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that incorrect password fails verification"""
        password = "mysecurepassword"
        wrong_password = "wrongpassword"
        hashed = WalletManager.hash_password(password)

        assert WalletManager.verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test that empty password fails verification"""
        password = "mysecurepassword"
        hashed = WalletManager.hash_password(password)

        assert WalletManager.verify_password("", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test that invalid hash returns False, not exception"""
        result = WalletManager.verify_password("password", "invalidhash")
        assert result is False


class TestWalletEncryption:
    """Test wallet encryption and decryption"""

    def test_encrypt_wallet_data(self):
        """Test wallet data encryption"""
        wallet_data = json.dumps({"private_key": "0x123", "address": "0xabc"})
        password = "securepassword"

        encrypted = WalletManager.encrypt_wallet_data(wallet_data, password)

        assert "encrypted_data" in encrypted
        assert "salt" in encrypted
        assert "key" in encrypted
        assert encrypted["encrypted_data"] != wallet_data

    def test_decrypt_wallet_data(self):
        """Test wallet data decryption"""
        wallet_data = json.dumps({"private_key": "0x123", "address": "0xabc"})
        password = "securepassword"

        encrypted = WalletManager.encrypt_wallet_data(wallet_data, password)
        decrypted = WalletManager.decrypt_wallet_data(
            encrypted["encrypted_data"],
            encrypted["key"]
        )

        assert decrypted == wallet_data

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails gracefully"""
        wallet_data = json.dumps({"private_key": "0x123"})
        password = "securepassword"

        encrypted = WalletManager.encrypt_wallet_data(wallet_data, password)

        # Try to decrypt with wrong key
        result = WalletManager.decrypt_wallet_data(
            encrypted["encrypted_data"],
            "wrongkey12345678901234567890123456789012"  # Invalid key format
        )

        assert result is None


class TestWalletCreation:
    """Test wallet creation"""

    def test_create_new_wallet_returns_dict(self):
        """Test that create_new_wallet returns proper structure"""
        wallet = WalletManager.create_new_wallet()

        assert wallet is not None
        assert "address" in wallet
        assert "mnemonic" in wallet
        assert "wallet_data" in wallet
        assert wallet["address"].startswith("0x")
        assert len(wallet["mnemonic"].split()) == 12  # 12-word mnemonic

    def test_create_new_wallet_unique_addresses(self):
        """Test that each wallet has unique address"""
        wallet1 = WalletManager.create_new_wallet()
        wallet2 = WalletManager.create_new_wallet()

        assert wallet1["address"] != wallet2["address"]
        assert wallet1["mnemonic"] != wallet2["mnemonic"]


class TestWalletImport:
    """Test wallet import functionality"""

    def test_import_wallet_from_private_key(self):
        """Test importing wallet from private key"""
        # Create a wallet first to get a valid private key
        new_wallet = WalletManager.create_new_wallet()
        wallet_data = json.loads(new_wallet["wallet_data"])
        private_key = wallet_data["private_key"]

        # Import using the private key
        imported = WalletManager.import_wallet(private_key)

        assert imported is not None
        assert imported["address"] == new_wallet["address"]

    def test_import_wallet_from_mnemonic(self):
        """Test importing wallet from seed phrase"""
        # Create a wallet first
        new_wallet = WalletManager.create_new_wallet()
        mnemonic = new_wallet["mnemonic"]

        # Import using mnemonic
        imported = WalletManager.import_wallet(mnemonic)

        assert imported is not None
        assert imported["address"] == new_wallet["address"]

    def test_import_wallet_invalid_input(self):
        """Test that invalid input returns None"""
        result = WalletManager.import_wallet("invalid input here")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
