"""
Transaction API Schemas
Request and response models for transaction operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import re


class TransactionType(str, Enum):
    """Transaction types."""
    SEND = "send"
    RECEIVE = "receive"
    BRIDGE = "bridge"
    YIELD_DEPOSIT = "yield_deposit"
    YIELD_WITHDRAW = "yield_withdraw"
    GIFT_CARD = "gift_card"


class TransactionStatus(str, Enum):
    """Transaction status values."""
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransactionPreviewRequest(BaseModel):
    """Request to preview a transaction before execution."""
    to_address: str = Field(..., description="Recipient address")
    amount: Decimal = Field(..., gt=0, description="Amount in USDC")
    chain: str = Field(default="base-mainnet", description="Target chain")

    @field_validator("to_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        v = v.strip()
        # EVM address validation
        if v.startswith("0x"):
            if len(v) != 42 or not re.match(r"^0x[0-9a-fA-F]{40}$", v):
                raise ValueError("Invalid EVM address")
            return v
        # Solana address validation (base58, 32-44 chars)
        if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", v):
            return v
        raise ValueError("Invalid address format")


class TransactionPreview(BaseModel):
    """Transaction preview with fee breakdown."""
    action: str = "Send USDC"
    amount: Decimal = Field(..., description="Send amount")
    amount_formatted: str = Field(..., description="Formatted amount (e.g., '$50.00')")
    to_address: str = Field(..., description="Full recipient address")
    to_address_short: str = Field(..., description="Truncated address for display")
    from_address: str = Field(..., description="Sender address")
    from_address_short: str = Field(..., description="Truncated sender address")
    chain: str = Field(..., description="Chain identifier")
    chain_name: str = Field(..., description="Human-readable chain name")
    fee: Decimal = Field(..., description="Transaction fee")
    fee_formatted: str = Field(..., description="Formatted fee")
    total: Decimal = Field(..., description="Total cost (amount + fee)")
    total_formatted: str = Field(..., description="Formatted total")
    estimated_time: str = Field(default="~5 seconds", description="Estimated confirmation time")
    preview_id: str = Field(..., description="Preview ID for confirmation")
    expires_at: datetime = Field(..., description="Preview expiration time")


class TransactionRequest(BaseModel):
    """Request to execute a transaction."""
    preview_id: str = Field(..., description="Preview ID from preview step")
    user_confirmed: bool = Field(default=False, description="User has confirmed the transaction")

    @field_validator("user_confirmed")
    @classmethod
    def must_confirm(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Transaction must be confirmed by user")
        return v


class TransactionResponse(BaseModel):
    """Response after transaction execution."""
    success: bool = True
    tx_hash: str = Field(..., description="Transaction hash")
    explorer_url: str = Field(..., description="Block explorer URL")
    amount: Decimal
    amount_formatted: str
    to_address: str
    chain: str
    chain_name: str
    status: TransactionStatus = TransactionStatus.CONFIRMING
    message: str = "Transaction submitted successfully"


class TransactionHistoryItem(BaseModel):
    """Single transaction in history."""
    id: str
    type: TransactionType
    amount: Decimal
    amount_formatted: str
    chain: str
    chain_name: str
    tx_hash: Optional[str] = None
    explorer_url: Optional[str] = None
    counterparty: Optional[str] = None  # Address of other party
    counterparty_short: Optional[str] = None
    status: TransactionStatus
    created_at: datetime
    confirmed_at: Optional[datetime] = None


class TransactionHistoryResponse(BaseModel):
    """Transaction history response."""
    transactions: List[TransactionHistoryItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class BridgePreviewRequest(BaseModel):
    """Request to preview a cross-chain bridge."""
    from_chain: str = Field(..., description="Source chain")
    to_chain: str = Field(..., description="Destination chain")
    amount: Decimal = Field(..., gt=0, description="Amount in USDC")


class BridgePreview(BaseModel):
    """Bridge preview with fee and timing breakdown."""
    from_chain: str
    from_chain_name: str
    to_chain: str
    to_chain_name: str
    amount: Decimal
    amount_formatted: str
    bridge_fee: Decimal
    bridge_fee_formatted: str
    estimated_time: str  # e.g., "10-15 minutes"
    protocol: str = "CCTP"  # Circle Cross-Chain Transfer Protocol
    total_received: Decimal
    total_received_formatted: str
    preview_id: str
    expires_at: datetime
