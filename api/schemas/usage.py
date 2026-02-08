"""
API Key Usage Schemas
Pydantic models for usage statistics endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel


class UsagePeriodStats(BaseModel):
    """Usage statistics for a time period."""
    requests: int = 0
    tokens: int = 0
    cost: float = 0.0


class UsageByModel(BaseModel):
    """Usage breakdown by model."""
    provider: str
    model: str
    requests: int = 0
    tokens: int = 0
    cost: float = 0.0


class UsageDailyEntry(BaseModel):
    """Single day's usage."""
    date: str
    requests: int = 0
    tokens: int = 0
    cost: float = 0.0


class UsageSummaryResponse(BaseModel):
    """Response for usage summary endpoint."""
    today: UsagePeriodStats
    this_week: UsagePeriodStats
    this_month: UsagePeriodStats
    by_model: List[UsageByModel] = []
    daily: List[UsageDailyEntry] = []


class UsageRequestEntry(BaseModel):
    """Single API request entry."""
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    success: bool = True
    created_at: str


class UsageRecentResponse(BaseModel):
    """Response for recent requests endpoint."""
    requests: List[UsageRequestEntry]
    total: int
