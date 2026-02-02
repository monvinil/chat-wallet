"""
Wallet API Schemas
Request and response models for wallet operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator
import re


class WalletBalance(BaseModel):
    """Balance for a single chain."""
    chain: str = Field(..., description="Chain identifier (e.g., 'base-mainnet')")
    chain_name: str = Field(..., description="Human-readable chain name")
    usdc_balance: Decimal = Field(..., description="USDC balance")
    usdc_balance_formatted: str = Field(..., description="Formatted USDC balance (e.g., '$50.00')")
    native_balance: Decimal = Field(default=Decimal("0"), description="Native token balance (ETH, SOL)")
    native_symbol: str = Field(default="ETH", description="Native token symbol")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WalletBalances(BaseModel):
    """Aggregated wallet balances across all chains."""
    total_usdc: Decimal = Field(..., description="Total USDC across all chains")
    total_usdc_formatted: str = Field(..., description="Formatted total (e.g., '$150.00')")
    evm_address: str = Field(..., description="EVM wallet address")
    solana_address: Optional[str] = Field(None, description="Solana wallet address")
    balances: List[WalletBalance] = Field(default_factory=list, description="Per-chain balances")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WalletAddress(BaseModel):
    """Wallet address information for deposits."""
    chain: str = Field(..., description="Chain identifier")
    chain_name: str = Field(..., description="Human-readable chain name")
    address: str = Field(..., description="Deposit address")
    address_short: str = Field(..., description="Truncated address for display")
    explorer_url: str = Field(..., description="Block explorer URL")
    usdc_contract: Optional[str] = Field(None, description="USDC contract address on this chain")
    qr_code: Optional[str] = Field(None, description="Base64 encoded QR code image")


class WalletCreateRequest(BaseModel):
    """Request to create a new wallet."""
    email: str = Field(..., min_length=3, max_length=255, description="User email")
    password: str = Field(..., min_length=8, max_length=128, description="Encryption password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class WalletCreateResponse(BaseModel):
    """Response after creating a new wallet."""
    user_id: str = Field(..., description="User ID")
    evm_address: str = Field(..., description="EVM wallet address")
    solana_address: Optional[str] = Field(None, description="Solana wallet address")
    mnemonic: str = Field(..., description="24-word recovery phrase (show once, then discard)")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    message: str = Field(default="Wallet created successfully. Save your recovery phrase!")


class WalletImportRequest(BaseModel):
    """Request to import an existing wallet."""
    email: str = Field(..., min_length=3, max_length=255, description="User email")
    password: str = Field(..., min_length=8, max_length=128, description="Encryption password")
    recovery_phrase: str = Field(..., description="12 or 24 word mnemonic, or private key")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("recovery_phrase")
    @classmethod
    def validate_recovery(cls, v: str) -> str:
        v = v.strip()
        words = v.split()

        # Check if mnemonic (12 or 24 words)
        if len(words) in [12, 24]:
            return v

        # Check if private key (hex string)
        key = v.replace("0x", "")
        if len(key) == 64 and re.match(r"^[0-9a-fA-F]+$", key):
            return v

        raise ValueError("Invalid recovery phrase or private key")


class WalletUnlockRequest(BaseModel):
    """Request to unlock a wallet."""
    password: str = Field(..., min_length=1, description="Wallet password")


class WalletLoginRequest(BaseModel):
    """Request to login to existing wallet."""
    email: str = Field(..., min_length=3, max_length=255, description="User email")
    password: str = Field(..., min_length=1, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.lower().strip()


class WalletLoginResponse(BaseModel):
    """Response after successful login."""
    user_id: str
    email: str
    evm_address: str
    solana_address: Optional[str] = None
    access_token: str
    refresh_token: str
    wallet_locked: bool = True  # Wallet data encrypted, needs password to unlock
    message: str = "Login successful"
