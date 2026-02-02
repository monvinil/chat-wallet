"""
Scheduler API Schemas
Pydantic models for DCA/scheduler endpoints.
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ScheduleCreateRequest(BaseModel):
    """Request for creating a new schedule"""
    type: Literal["dca"] = Field(default="dca", description="Schedule type")
    amount: float = Field(..., gt=0, description="Amount in USDC per execution")
    frequency: Literal["daily", "weekly", "biweekly", "monthly"] = Field(..., description="Execution frequency")
    target_token: Literal["ETH", "BTC", "WBTC"] = Field(..., description="Token to buy")
    source_token: str = Field(default="USDC", description="Source token (usually USDC)")
    chain: str = Field(default="base-mainnet", description="Chain for swaps")


class ScheduleResponse(BaseModel):
    """Schedule object response"""
    id: str
    type: str
    amount: float
    amount_formatted: str
    frequency: str
    target_token: str
    source_token: str
    chain: str
    next_execution: Optional[str] = None
    last_execution: Optional[str] = None
    total_executed: int = 0
    total_invested: float = 0.0
    status: Literal["active", "paused", "cancelled", "completed"]
    created_at: str


class ScheduleListResponse(BaseModel):
    """Response for listing schedules"""
    schedules: List[ScheduleResponse]
    total: int


class ScheduleActionResponse(BaseModel):
    """Response for schedule actions (pause, resume, cancel)"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
