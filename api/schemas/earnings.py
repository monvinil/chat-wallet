"""
Earnings API Schemas
Pydantic models for earnings tracking endpoints.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class EarningsBreakdown(BaseModel):
    """Earnings breakdown by source"""
    source: Literal["yield", "dca_gains", "referral"]
    amount: float
    amount_formatted: str
    percentage: float


class EarningsSummaryResponse(BaseModel):
    """Response for earnings summary"""
    today: float
    today_formatted: str
    this_week: float
    this_week_formatted: str
    this_month: float
    this_month_formatted: str
    all_time: float
    all_time_formatted: str
    breakdown: List[EarningsBreakdown] = []


class EarningsHistoryItem(BaseModel):
    """Single earnings history item"""
    date: str
    amount: float
    source: Literal["yield", "dca_gains", "referral"]


class EarningsHistoryResponse(BaseModel):
    """Response for earnings history"""
    items: List[EarningsHistoryItem]
    period: Literal["daily", "weekly", "monthly"]
    total_items: int
