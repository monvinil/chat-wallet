"""
Yield API Schemas
Pydantic models for yield (Aave) endpoints.
"""

from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


class YieldStatusResponse(BaseModel):
    """Response for yield status endpoint"""
    enabled: bool
    protocol: str = "Aave V3"
    apy: float
    deposited_amount: float
    deposited_amount_formatted: str
    earned_amount: float
    earned_amount_formatted: str
    projected_daily: float
    projected_monthly: float
    projected_yearly: float
    positions: List[dict] = []


class YieldDepositRequest(BaseModel):
    """Request for yield deposit"""
    amount: Optional[float] = Field(None, description="Amount to deposit. If None, deposits all available USDC")
    password: str = Field(..., min_length=8, description="Wallet password for transaction signing")
    chain: str = Field(default="base-mainnet", description="Chain to deposit on")


class YieldWithdrawRequest(BaseModel):
    """Request for yield withdrawal"""
    amount: Optional[float] = Field(None, description="Amount to withdraw. If None, withdraws all")
    password: str = Field(..., min_length=8, description="Wallet password for transaction signing")
    chain: str = Field(default="base-mainnet", description="Chain to withdraw from")


class YieldTransactionResponse(BaseModel):
    """Response for yield deposit/withdraw"""
    success: bool
    tx_hash: Optional[str] = None
    amount: Optional[float] = None
    chain: Optional[str] = None
    error: Optional[str] = None
