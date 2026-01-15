"""
Centralized encryption utilities for Chat Wallet

This module provides consistent encryption/decryption functionality across:
- Wallet data encryption (password-based)
- Settings encryption (environment key-based)
- OAuth token encryption (environment key-based)
"""

import os
import base64
import hashlib
import bcrypt
import streamlit as st
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, Any


class PasswordEncryption:
    """Password-based encryption for wallet data"""

    # Constants for password-based encryption
    PASSWORD_HASH_ITERATIONS = 100000
    SALT_LENGTH = 32  # bytes

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2

        Args:
            password: User password
            salt: Random salt (32 bytes)

        Returns:
            Derived key (32 bytes) suitable for Fernet
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PasswordEncryption.PASSWORD_HASH_ITERATIONS,
        )
        return kdf.derive(password.encode())

    @staticmethod
    def encrypt(data: str, password: str) -> Dict[str, Any]:
        """
        Encrypt data with password

        Args:
            data: Plain text data to encrypt
            password: User password

        Returns:
            Dictionary with encrypted_data (str), salt (str hex), and key (str base64)
        """
        # Generate random salt
        salt = os.urandom(PasswordEncryption.SALT_LENGTH)

        # Derive encryption key (raw 32 bytes)
        raw_key = PasswordEncryption.derive_key(password, salt)

        # Convert to Fernet key format (base64 encoded)
        fernet_key = base64.urlsafe_b64encode(raw_key)

        # Encrypt data
        cipher = Fernet(fernet_key)
        encrypted = cipher.encrypt(data.encode())

        return {
            "encrypted_data": encrypted.decode(),
            "salt": salt.hex(),  # Store as hex string
            "key": fernet_key.decode()  # Store as base64 string
        }

    @staticmethod
    def decrypt(encrypted_data: str, password: str, salt: str) -> str | None:
        """
        Decrypt data with password

        Args:
            encrypted_data: Encrypted data (base64 string from Fernet)
            password: User password
            salt: Salt used for encryption (hex string)

        Returns:
            Decrypted plain text, or None if decryption fails
        """
        try:
            # Convert salt from hex
            salt_bytes = bytes.fromhex(salt)

            # Derive same encryption key (raw 32 bytes)
            raw_key = PasswordEncryption.derive_key(password, salt_bytes)

            # Convert to Fernet key format (base64 encoded)
            fernet_key = base64.urlsafe_b64encode(raw_key)

            # Decrypt data
            cipher = Fernet(fernet_key)
            decrypted = cipher.decrypt(encrypted_data.encode())

            return decrypted.decode()
        except Exception:
            return None

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password for storage using bcrypt (secure against rainbow tables)

        Args:
            password: User password

        Returns:
            Bcrypt hash string (includes salt, starts with $2b$)
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """
        Verify password against stored hash (supports bcrypt and legacy SHA-256)

        Args:
            password: User-provided password
            stored_hash: Stored password hash (bcrypt or legacy SHA-256)

        Returns:
            True if password matches, False otherwise
        """
        try:
            # Check if it's a bcrypt hash (starts with $2b$ or $2a$)
            if stored_hash.startswith(('$2b$', '$2a$', '$2y$')):
                return bcrypt.checkpw(password.encode(), stored_hash.encode())
            else:
                # Legacy SHA-256 hash (64 char hex string) - for backward compatibility
                legacy_hash = hashlib.sha256(password.encode()).hexdigest()
                return legacy_hash == stored_hash
        except Exception:
            return False


class SettingsEncryption:
    """Environment key-based encryption for settings and OAuth tokens"""

    # Encryption key - MUST be set in environment for production
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    _ENCRYPTION_KEY = None
    _encryption_warning_shown = False

    @classmethod
    def _get_encryption_key(cls) -> bytes:
        """
        Get encryption key from environment (required for production)

        Returns:
            Encryption key bytes

        Raises:
            Warning in Streamlit UI if key not set (development mode)
        """
        if cls._ENCRYPTION_KEY is None:
            key_str = os.getenv("SETTINGS_ENCRYPTION_KEY")
            if key_str:
                cls._ENCRYPTION_KEY = key_str.encode() if isinstance(key_str, str) else key_str
            else:
                # Development fallback - warn but don't crash
                if not cls._encryption_warning_shown:
                    st.warning("⚠️ SETTINGS_ENCRYPTION_KEY not set. Using temporary key - encrypted data will be lost on restart!")
                    cls._encryption_warning_shown = True
                # Generate a session-stable key for development
                cls._ENCRYPTION_KEY = Fernet.generate_key()
        return cls._ENCRYPTION_KEY

    @classmethod
    def _get_cipher(cls):
        """
        Get Fernet cipher for encryption/decryption

        Returns:
            Fernet cipher instance
        """
        return Fernet(cls._get_encryption_key())

    @classmethod
    def encrypt(cls, data: str) -> str:
        """
        Encrypt sensitive data (API keys, OAuth tokens)

        Args:
            data: Plain text data

        Returns:
            Encrypted data (base64 string)
        """
        cipher = cls._get_cipher()
        return cipher.encrypt(data.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_data: str) -> str | None:
        """
        Decrypt sensitive data

        Args:
            encrypted_data: Encrypted data (base64 string)

        Returns:
            Decrypted plain text, or None if decryption fails
        """
        try:
            cipher = cls._get_cipher()
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return None
