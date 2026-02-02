"""
Health Check Endpoints
Service health and status monitoring.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from api.config import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    services: Dict[str, str]


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    ready: bool
    checks: Dict[str, bool]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Basic health check endpoint"
)
async def health_check() -> HealthResponse:
    """
    Basic health check.
    Returns API status and version information.
    """
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        timestamp=datetime.utcnow().isoformat(),
        services={
            "api": "up",
        }
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if the service is ready to accept requests"
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check.
    Verifies that all required services are available.
    """
    checks = {}

    # Check Supabase connection
    try:
        from supabase_client import get_supabase_client
        client = get_supabase_client()
        checks["database"] = client is not None
    except Exception:
        checks["database"] = False

    # Check if Circle credentials are configured
    checks["circle"] = bool(settings.circle_api_key)

    # Overall readiness
    ready = all(checks.values())

    return ReadinessResponse(
        ready=ready,
        checks=checks
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="API root",
    description="API root endpoint with basic info"
)
async def root() -> Dict[str, Any]:
    """API root endpoint."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs" if settings.debug else None,
        "health": "/health",
        "ready": "/ready"
    }
