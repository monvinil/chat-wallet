"""
Common API Schemas
Shared response structures used across endpoints.
"""

from datetime import datetime
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper.
    All successful responses use this structure.
    """
    success: bool = True
    data: T
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """
    Standard error response.
    All error responses use this structure.
    """
    success: bool = False
    error: str
    details: Optional[Any] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response wrapper.
    Used for list endpoints with pagination.
    """
    success: bool = True
    data: List[T]
    total: int
    page: int
    page_size: int
    has_more: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChainInfo(BaseModel):
    """Blockchain network information."""
    chain_id: str
    name: str
    symbol: str
    explorer_url: str
    usdc_address: Optional[str] = None
    is_testnet: bool = False


class SuccessResponse(BaseModel):
    """Simple success response."""
    success: bool = True
    message: str
