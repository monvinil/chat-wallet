"""
Scheduler API Routes
Endpoints for DCA and scheduled task management.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from croniter import croniter

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas.scheduler import (
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleListResponse,
    ScheduleActionResponse,
)
from api.schemas.common import APIResponse
from api.middleware.auth import JWTBearer
from supabase_client import get_supabase_client
from utils.logger import logger


router = APIRouter()

# Cron patterns for frequencies
FREQUENCY_CRON = {
    "daily": "0 9 * * *",
    "weekly": "0 9 * * 1",
    "biweekly": "0 9 1,15 * *",  # 1st and 15th
    "monthly": "0 9 1 * *",
}


def format_usd(amount: float) -> str:
    """Format amount as USD string"""
    return f"${amount:,.2f}"


def get_next_execution(cron_expr: str) -> datetime:
    """Calculate next execution time from cron expression"""
    try:
        cron_iter = croniter(cron_expr, datetime.now())
        return cron_iter.get_next(datetime)
    except Exception:
        return datetime.now() + timedelta(days=7)


def task_to_schedule_response(task: Dict[str, Any]) -> ScheduleResponse:
    """Convert database task to API response"""
    params = task.get("task_params", {})
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            params = {}

    return ScheduleResponse(
        id=task.get("id", ""),
        type=task.get("task_type", "dca"),
        amount=params.get("amount", 0),
        amount_formatted=format_usd(params.get("amount", 0)),
        frequency=params.get("frequency", "weekly"),
        target_token=params.get("target_token", "ETH"),
        source_token=params.get("source_token", "USDC"),
        chain=params.get("chain", "base-mainnet"),
        next_execution=task.get("next_run_at"),
        last_execution=task.get("last_run_at"),
        total_executed=task.get("run_count", 0),
        total_invested=params.get("amount", 0) * task.get("run_count", 0),
        status=task.get("status", "active"),
        created_at=task.get("created_at", datetime.now().isoformat())
    )


@router.post(
    "/create",
    response_model=APIResponse[ScheduleResponse],
    summary="Create DCA schedule",
    description="Create a new dollar-cost averaging schedule"
)
async def create_schedule(
    request: ScheduleCreateRequest,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[ScheduleResponse]:
    """Create a new DCA schedule"""
    user_id = credentials.get("sub")
    wallet_address = credentials.get("wallet_address")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )

        # Get cron expression for frequency
        cron_expr = FREQUENCY_CRON.get(request.frequency, FREQUENCY_CRON["weekly"])
        next_run = get_next_execution(cron_expr)

        # Build task
        task_id = str(uuid.uuid4())
        task_params = {
            "amount": request.amount,
            "frequency": request.frequency,
            "target_token": request.target_token,
            "source_token": request.source_token,
            "chain": request.chain,
            "wallet_address": wallet_address,
        }

        task = {
            "id": task_id,
            "user_id": user_id,
            "task_type": "dca",
            "task_params": json.dumps(task_params),
            "description": f"Buy ${request.amount} of {request.target_token} {request.frequency}",
            "schedule_type": "recurring",
            "cron_expression": cron_expr,
            "next_run_at": next_run.isoformat(),
            "status": "active",
            "run_count": 0,
            "created_at": datetime.now().isoformat(),
        }

        # Insert into database
        result = supabase.table("scheduled_tasks").insert(task).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create schedule"
            )

        # Return response
        task["task_params"] = task_params  # Convert back for response
        return APIResponse(data=task_to_schedule_response(task))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


@router.get(
    "/list",
    response_model=APIResponse[ScheduleListResponse],
    summary="List schedules",
    description="Get all DCA schedules for the authenticated user"
)
async def list_schedules(
    status_filter: Optional[str] = "active",
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[ScheduleListResponse]:
    """List all schedules for the user"""
    user_id = credentials.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )

        # Query schedules
        query = supabase.table("scheduled_tasks").select("*").eq("user_id", user_id).eq("task_type", "dca")

        if status_filter and status_filter != "all":
            query = query.eq("status", status_filter)

        result = query.order("created_at", desc=True).execute()
        tasks = result.data if result.data else []

        schedules = [task_to_schedule_response(task) for task in tasks]

        return APIResponse(data=ScheduleListResponse(
            schedules=schedules,
            total=len(schedules)
        ))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch schedules"
        )


@router.post(
    "/{schedule_id}/cancel",
    response_model=APIResponse[ScheduleActionResponse],
    summary="Cancel schedule",
    description="Cancel a DCA schedule"
)
async def cancel_schedule(
    schedule_id: str,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[ScheduleActionResponse]:
    """Cancel a schedule"""
    user_id = credentials.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )

        # Verify ownership and update
        result = supabase.table("scheduled_tasks").update({
            "status": "cancelled",
            "updated_at": datetime.now().isoformat()
        }).eq("id", schedule_id).eq("user_id", user_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

        return APIResponse(data=ScheduleActionResponse(
            success=True,
            message="Schedule cancelled"
        ))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel schedule"
        )


@router.post(
    "/{schedule_id}/pause",
    response_model=APIResponse[ScheduleActionResponse],
    summary="Pause schedule",
    description="Pause a DCA schedule"
)
async def pause_schedule(
    schedule_id: str,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[ScheduleActionResponse]:
    """Pause a schedule"""
    user_id = credentials.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )

        result = supabase.table("scheduled_tasks").update({
            "status": "paused",
            "updated_at": datetime.now().isoformat()
        }).eq("id", schedule_id).eq("user_id", user_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

        return APIResponse(data=ScheduleActionResponse(
            success=True,
            message="Schedule paused"
        ))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause schedule"
        )


@router.post(
    "/{schedule_id}/resume",
    response_model=APIResponse[ScheduleActionResponse],
    summary="Resume schedule",
    description="Resume a paused DCA schedule"
)
async def resume_schedule(
    schedule_id: str,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[ScheduleActionResponse]:
    """Resume a paused schedule"""
    user_id = credentials.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )

        # Get current task to recalculate next run
        task_result = supabase.table("scheduled_tasks").select("cron_expression").eq(
            "id", schedule_id
        ).eq("user_id", user_id).execute()

        if not task_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )

        cron_expr = task_result.data[0].get("cron_expression")
        next_run = get_next_execution(cron_expr) if cron_expr else datetime.now() + timedelta(days=7)

        result = supabase.table("scheduled_tasks").update({
            "status": "active",
            "next_run_at": next_run.isoformat(),
            "updated_at": datetime.now().isoformat()
        }).eq("id", schedule_id).eq("user_id", user_id).execute()

        return APIResponse(data=ScheduleActionResponse(
            success=True,
            message="Schedule resumed"
        ))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume schedule"
        )
