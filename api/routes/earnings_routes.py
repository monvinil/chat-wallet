"""
Earnings API Routes
Endpoints for earnings tracking and history.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas.earnings import (
    EarningsSummaryResponse,
    EarningsBreakdown,
    EarningsHistoryResponse,
    EarningsHistoryItem,
)
from api.schemas.common import APIResponse
from api.middleware.auth import JWTBearer
from aave_client import get_yield_summary, AaveClient
from supabase_client import get_supabase_client
from utils.logger import logger


router = APIRouter()


def format_usd(amount: float) -> str:
    """Format amount as USD string"""
    return f"${amount:,.2f}"


def calculate_yield_earnings(wallet_address: str) -> Dict[str, float]:
    """
    Calculate yield earnings from Aave positions.

    Returns dict with today, week, month, all_time earnings.
    """
    try:
        summary = get_yield_summary(wallet_address)
        total_deposited = summary.get("total_deposited", 0)
        avg_apy = summary.get("average_apy", 0)

        if total_deposited <= 0 or avg_apy <= 0:
            return {"today": 0, "week": 0, "month": 0, "all_time": 0}

        # Calculate daily rate
        daily_rate = avg_apy / 100 / 365

        # Estimate earnings (simplified model)
        # In production, track actual deposit dates and calculate compound interest
        today_earnings = total_deposited * daily_rate
        week_earnings = today_earnings * 7
        month_earnings = today_earnings * 30

        # For all-time, estimate 30 days of earnings (placeholder)
        # In production, query actual historical earnings
        all_time_earnings = month_earnings

        return {
            "today": round(today_earnings, 4),
            "week": round(week_earnings, 4),
            "month": round(month_earnings, 2),
            "all_time": round(all_time_earnings, 2)
        }

    except Exception as e:
        logger.error(f"Failed to calculate yield earnings: {e}")
        return {"today": 0, "week": 0, "month": 0, "all_time": 0}


def calculate_dca_gains(user_id: str) -> Dict[str, float]:
    """
    Calculate DCA gains from executed trades.

    This would compare purchase prices to current prices.
    For now, returns placeholder values.
    """
    try:
        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            return {"today": 0, "week": 0, "month": 0, "all_time": 0}

        # Query executed DCA trades from task_runs
        # In production, calculate actual P&L based on purchase prices vs current prices
        result = supabase.table("task_runs").select("*").eq(
            "user_id", user_id
        ).eq("status", "success").order("started_at", desc=True).limit(100).execute()

        runs = result.data if result.data else []

        # Placeholder: Count successful runs as potential gains
        # In production, calculate actual gains from price differences
        total_runs = len(runs)

        # Mock gains (in production, calculate from actual trade data)
        mock_gain_per_trade = 0.50  # Average $0.50 gain per trade (placeholder)

        return {
            "today": round(mock_gain_per_trade * min(total_runs, 1), 2),
            "week": round(mock_gain_per_trade * min(total_runs, 7), 2),
            "month": round(mock_gain_per_trade * min(total_runs, 30), 2),
            "all_time": round(mock_gain_per_trade * total_runs, 2)
        }

    except Exception as e:
        logger.error(f"Failed to calculate DCA gains: {e}")
        return {"today": 0, "week": 0, "month": 0, "all_time": 0}


@router.get(
    "/summary",
    response_model=APIResponse[EarningsSummaryResponse],
    summary="Get earnings summary",
    description="Get earnings summary including yield and DCA gains"
)
async def get_earnings_summary(
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[EarningsSummaryResponse]:
    """Get earnings summary for the authenticated user"""
    user_id = credentials.get("sub")
    wallet_address = credentials.get("wallet_address")

    if not user_id or not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        # Calculate earnings from different sources
        yield_earnings = calculate_yield_earnings(wallet_address)
        dca_gains = calculate_dca_gains(user_id)

        # Combine earnings
        today = yield_earnings["today"] + dca_gains["today"]
        this_week = yield_earnings["week"] + dca_gains["week"]
        this_month = yield_earnings["month"] + dca_gains["month"]
        all_time = yield_earnings["all_time"] + dca_gains["all_time"]

        # Build breakdown
        breakdown = []

        if yield_earnings["all_time"] > 0:
            yield_pct = (yield_earnings["all_time"] / all_time * 100) if all_time > 0 else 0
            breakdown.append(EarningsBreakdown(
                source="yield",
                amount=yield_earnings["all_time"],
                amount_formatted=format_usd(yield_earnings["all_time"]),
                percentage=round(yield_pct, 1)
            ))

        if dca_gains["all_time"] > 0:
            dca_pct = (dca_gains["all_time"] / all_time * 100) if all_time > 0 else 0
            breakdown.append(EarningsBreakdown(
                source="dca_gains",
                amount=dca_gains["all_time"],
                amount_formatted=format_usd(dca_gains["all_time"]),
                percentage=round(dca_pct, 1)
            ))

        response_data = EarningsSummaryResponse(
            today=today,
            today_formatted=format_usd(today),
            this_week=this_week,
            this_week_formatted=format_usd(this_week),
            this_month=this_month,
            this_month_formatted=format_usd(this_month),
            all_time=all_time,
            all_time_formatted=format_usd(all_time),
            breakdown=breakdown
        )

        return APIResponse(data=response_data)

    except Exception as e:
        logger.error(f"Failed to get earnings summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch earnings"
        )


@router.get(
    "/history",
    response_model=APIResponse[EarningsHistoryResponse],
    summary="Get earnings history",
    description="Get historical earnings data for charts"
)
async def get_earnings_history(
    period: str = Query(default="daily", description="Aggregation period: daily, weekly, monthly"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days of history"),
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[EarningsHistoryResponse]:
    """Get earnings history for charts"""
    user_id = credentials.get("sub")
    wallet_address = credentials.get("wallet_address")

    if not user_id or not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        # Get current yield earnings rate
        yield_earnings = calculate_yield_earnings(wallet_address)
        daily_yield = yield_earnings.get("today", 0)

        # Generate historical data
        # In production, this would query actual historical earnings from database
        items: List[EarningsHistoryItem] = []
        today = datetime.now().date()

        for i in range(days):
            date = today - timedelta(days=days - 1 - i)

            # Simulate some variance in daily earnings
            # In production, use actual historical data
            import random
            variance = random.uniform(0.8, 1.2)
            daily_amount = daily_yield * variance

            items.append(EarningsHistoryItem(
                date=date.isoformat(),
                amount=round(daily_amount, 4),
                source="yield"
            ))

        return APIResponse(data=EarningsHistoryResponse(
            items=items,
            period=period,
            total_items=len(items)
        ))

    except Exception as e:
        logger.error(f"Failed to get earnings history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch earnings history"
        )
