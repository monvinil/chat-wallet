"""
Unit tests for MetaTransaction
"""

import pytest
import time
from eth_account import Account

from meta_tx import MetaTransaction


class TestMetaTransactionMessage:
    """Test meta-transaction message creation"""

    def test_create_message_structure(self):
        """Test message has correct structure"""
        message = MetaTransaction.create_message(
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x0987654321098765432109876543210987654321",
            amount=100.0,
            currency="USDC",
            nonce=12345
        )

        assert "from" in message
        assert "to" in message
        assert "amount" in message
        assert "currency" in message
        assert "nonce" in message
        assert "deadline" in message

    def test_create_message_amount_conversion(self):
        """Test that amount is converted to wei (6 decimals for USDC)"""
        message = MetaTransaction.create_message(
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x0987654321098765432109876543210987654321",
            amount=100.0
        )

        # 100 USDC = 100 * 10^6 = 100000000
        assert message["amount"] == 100000000

    def test_create_message_checksums_addresses(self):
        """Test that addresses are checksummed"""
        message = MetaTransaction.create_message(
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x0987654321098765432109876543210987654321",
            amount=10.0
        )

        # Addresses should be checksummed (mixed case)
        assert message["from"] == "0x1234567890123456789012345678901234567890"
        assert message["to"] == "0x0987654321098765432109876543210987654321"


class TestMetaTransactionSigning:
    """Test meta-transaction signing and verification"""

    @pytest.fixture
    def test_account(self):
        """Create a test account for signing"""
        return Account.create()

    def test_sign_message(self, test_account):
        """Test signing a message"""
        message = MetaTransaction.create_message(
            from_address=test_account.address,
            to_address="0x0987654321098765432109876543210987654321",
            amount=50.0,
            nonce=1
        )

        signature = MetaTransaction.sign_message(
            message,
            test_account.key.hex(),
            chain_id=84532
        )

        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_verify_signature_valid(self, test_account):
        """Test signature verification with valid signature"""
        message = MetaTransaction.create_message(
            from_address=test_account.address,
            to_address="0x0987654321098765432109876543210987654321",
            amount=50.0,
            nonce=1
        )

        signature = MetaTransaction.sign_message(
            message,
            test_account.key.hex(),
            chain_id=84532
        )

        is_valid = MetaTransaction.verify_signature(
            message,
            signature,
            test_account.address,
            chain_id=84532
        )

        assert is_valid is True

    def test_verify_signature_wrong_signer(self, test_account):
        """Test verification fails with wrong signer"""
        other_account = Account.create()

        message = MetaTransaction.create_message(
            from_address=test_account.address,
            to_address="0x0987654321098765432109876543210987654321",
            amount=50.0,
            nonce=1
        )

        signature = MetaTransaction.sign_message(
            message,
            test_account.key.hex(),
            chain_id=84532
        )

        # Verify with different address
        is_valid = MetaTransaction.verify_signature(
            message,
            signature,
            other_account.address,  # Wrong signer
            chain_id=84532
        )

        assert is_valid is False

    def test_verify_signature_wrong_chain_id(self, test_account):
        """Test verification fails with wrong chain ID"""
        message = MetaTransaction.create_message(
            from_address=test_account.address,
            to_address="0x0987654321098765432109876543210987654321",
            amount=50.0,
            nonce=1
        )

        signature = MetaTransaction.sign_message(
            message,
            test_account.key.hex(),
            chain_id=84532  # Signed with Base Sepolia
        )

        # Verify with different chain ID
        is_valid = MetaTransaction.verify_signature(
            message,
            signature,
            test_account.address,
            chain_id=1  # Ethereum mainnet
        )

        assert is_valid is False


class TestMetaTransactionExpiry:
    """Test message expiry checking"""

    def test_is_expired_future_deadline(self):
        """Test message with future deadline is not expired"""
        message = MetaTransaction.create_message(
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x0987654321098765432109876543210987654321",
            amount=10.0,
            deadline_seconds=3600  # 1 hour from now
        )

        assert MetaTransaction.is_expired(message) is False

    def test_is_expired_past_deadline(self):
        """Test message with past deadline is expired"""
        message = {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "amount": 10000000,
            "currency": "USDC",
            "nonce": 1,
            "deadline": int(time.time()) - 100  # 100 seconds ago
        }

        assert MetaTransaction.is_expired(message) is True


class TestMetaTransactionDomain:
    """Test EIP-712 domain configuration"""

    def test_get_domain_default_chain(self):
        """Test default chain ID"""
        domain = MetaTransaction.get_domain()

        assert domain["name"] == "ChatWallet"
        assert domain["version"] == "1"
        assert domain["chainId"] == 84532  # Base Sepolia default

    def test_get_domain_custom_chain(self):
        """Test custom chain ID"""
        domain = MetaTransaction.get_domain(chain_id=1)  # Ethereum mainnet

        assert domain["chainId"] == 1

    def test_get_domain_arbitrum(self):
        """Test Arbitrum chain ID"""
        domain = MetaTransaction.get_domain(chain_id=421614)  # Arbitrum Sepolia

        assert domain["chainId"] == 421614


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
