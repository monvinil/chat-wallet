"""API Schema modules - Pydantic models for requests and responses."""

from api.schemas.wallet import (
    WalletBalance,
    WalletBalances,
    WalletAddress,
    WalletCreateRequest,
    WalletCreateResponse,
    WalletImportRequest,
    WalletUnlockRequest,
)
from api.schemas.transaction import (
    TransactionPreview,
    TransactionRequest,
    TransactionResponse,
    TransactionStatus,
)
from api.schemas.common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
)

__all__ = [
    # Wallet
    "WalletBalance",
    "WalletBalances",
    "WalletAddress",
    "WalletCreateRequest",
    "WalletCreateResponse",
    "WalletImportRequest",
    "WalletUnlockRequest",
    # Transaction
    "TransactionPreview",
    "TransactionRequest",
    "TransactionResponse",
    "TransactionStatus",
    # Common
    "APIResponse",
    "ErrorResponse",
    "PaginatedResponse",
]
