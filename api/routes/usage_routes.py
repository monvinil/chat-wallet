"""
API Key Usage Routes
Endpoints for querying API key usage statistics.
"""

import os
import sys
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas.usage import (
    UsageSummaryResponse,
    UsagePeriodStats,
    UsageByModel,
    UsageDailyEntry,
    UsageRecentResponse,
    UsageRequestEntry,
)
from api.schemas.common import APIResponse
from api.middleware.auth import JWTBearer
from api_key_usage import APIKeyUsageTracker
from utils.logger import logger


router = APIRouter()


@router.get(
    "/summary",
    response_model=APIResponse[UsageSummaryResponse],
    summary="Get usage summary",
    description="Get API key usage statistics including token counts and cost estimates",
)
async def get_usage_summary(
    days: int = Query(default=30, ge=1, le=90, description="Number of days to include"),
    credentials: Dict = Depends(JWTBearer()),
) -> APIResponse[UsageSummaryResponse]:
    """Get usage summary for the authenticated user."""
    user_id = credentials.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )

    try:
        raw = APIKeyUsageTracker.get_usage_summary(user_id, days=days)

        response_data = UsageSummaryResponse(
            today=UsagePeriodStats(**raw["today"]),
            this_week=UsagePeriodStats(**raw["this_week"]),
            this_month=UsagePeriodStats(**raw["this_month"]),
            by_model=[UsageByModel(**m) for m in raw["by_model"]],
            daily=[UsageDailyEntry(**d) for d in raw["daily"]],
        )

        return APIResponse(data=response_data)

    except Exception as e:
        logger.error(f"Failed to get usage summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch usage statistics",
        )


@router.get(
    "/recent",
    response_model=APIResponse[UsageRecentResponse],
    summary="Get recent requests",
    description="Get recent individual API requests with token details",
)
async def get_recent_requests(
    limit: int = Query(default=20, ge=1, le=100, description="Number of requests to return"),
    credentials: Dict = Depends(JWTBearer()),
) -> APIResponse[UsageRecentResponse]:
    """Get recent API requests for the authenticated user."""
    user_id = credentials.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )

    try:
        raw = APIKeyUsageTracker.get_recent_requests(user_id, limit=limit)

        requests = [
            UsageRequestEntry(
                provider=r.get("provider", "unknown"),
                model=r.get("model", "unknown"),
                input_tokens=r.get("input_tokens", 0),
                output_tokens=r.get("output_tokens", 0),
                total_tokens=r.get("total_tokens", 0),
                estimated_cost=float(r.get("estimated_cost", 0)),
                success=r.get("success", True),
                created_at=r.get("created_at", ""),
            )
            for r in raw
        ]

        return APIResponse(data=UsageRecentResponse(
            requests=requests,
            total=len(requests),
        ))

    except Exception as e:
        logger.error(f"Failed to get recent requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent requests",
        )
