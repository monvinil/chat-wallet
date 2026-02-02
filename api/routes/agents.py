"""
Agent API Routes

Endpoints for agent discovery, management, and interaction.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.middleware.auth import JWTBearer, get_current_user
from api.schemas.agent import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentMessageRequest,
    AgentSubscribeRequest,
    AgentReviewRequest,
    AgentResponse,
    AgentListResponse,
    AgentMessageResponse,
    AgentEarningsResponse,
    AgentSubscriptionResponse,
    AgentReviewResponse,
    AgentCapabilityResponse,
    AgentCategory,
    AgentStatus,
)
from api.schemas.common import APIResponse
from utils.logger import logger


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ======================
# DISCOVERY ENDPOINTS
# ======================

@router.get("/", response_model=AgentListResponse)
@limiter.limit("30/minute")
async def list_agents(
    request: Request,
    category: Optional[AgentCategory] = None,
    search: Optional[str] = Query(None, min_length=2, max_length=100),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    featured: Optional[bool] = None,
    verified: Optional[bool] = None,
    sort_by: str = Query("popular", pattern=r'^(popular|newest|rating|revenue)$'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List and search agents.

    - **category**: Filter by agent category
    - **search**: Search in name and description
    - **tags**: Filter by tags (comma-separated)
    - **featured**: Only show featured agents
    - **verified**: Only show verified agents
    - **sort_by**: Sort order (popular, newest, rating, revenue)
    """
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Build query
        query = supabase.table("agents").select("*").eq("status", "active")

        if category:
            query = query.eq("category", category.value)

        if featured is True:
            query = query.eq("is_featured", True)

        if verified is True:
            query = query.eq("is_verified", True)

        if search:
            # Supabase full-text search
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")

        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            query = query.contains("tags", tag_list)

        # Sorting
        if sort_by == "popular":
            query = query.order("total_users", desc=True)
        elif sort_by == "newest":
            query = query.order("created_at", desc=True)
        elif sort_by == "rating":
            query = query.order("average_rating", desc=True)
        elif sort_by == "revenue":
            query = query.order("total_revenue_usdc", desc=True)

        # Pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        result = query.execute()

        # Get total count
        count_result = supabase.table("agents").select("id", count="exact").eq("status", "active").execute()
        total = count_result.count or 0

        agents = [AgentResponse(**agent) for agent in result.data]

        return AgentListResponse(
            agents=agents,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + page_size) < total,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.get("/featured", response_model=List[AgentResponse])
@limiter.limit("60/minute")
async def get_featured_agents(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
):
    """Get featured agents for homepage/discovery."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        result = supabase.table("agents").select("*").eq(
            "status", "active"
        ).eq(
            "is_featured", True
        ).order(
            "total_users", desc=True
        ).limit(limit).execute()

        return [AgentResponse(**agent) for agent in result.data]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting featured agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get featured agents")


@router.get("/categories")
async def get_categories():
    """Get all agent categories with counts."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Get counts per category
        categories = []
        for cat in AgentCategory:
            result = supabase.table("agents").select(
                "id", count="exact"
            ).eq("status", "active").eq("category", cat.value).execute()

            categories.append({
                "name": cat.value,
                "display_name": cat.value.replace("_", " ").title(),
                "count": result.count or 0,
            })

        return {"categories": categories}

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get categories")


@router.get("/capabilities", response_model=List[AgentCapabilityResponse])
async def get_capabilities():
    """Get all available agent capabilities."""
    # Return built-in capabilities from SDK
    from sdk.usdchat_agent.capabilities import get_all_capabilities

    capabilities = get_all_capabilities()
    return [
        AgentCapabilityResponse(
            name=cap.name,
            display_name=cap.display_name,
            description=cap.description,
            risk_level=cap.risk_level.value,
            requires_verification=cap.requires_verification,
        )
        for cap in capabilities
    ]


# ======================
# AGENT CRUD
# ======================

@router.get("/{slug}", response_model=AgentResponse)
@limiter.limit("60/minute")
async def get_agent(request: Request, slug: str):
    """Get agent details by slug."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        result = supabase.table("agents").select("*").eq("slug", slug).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Only show active agents to non-owners
        if result.data["status"] != "active":
            raise HTTPException(status_code=404, detail="Agent not found")

        return AgentResponse(**result.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent")


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_agent(
    request: Request,
    agent_data: AgentCreateRequest,
    user: dict = Depends(JWTBearer()),
):
    """
    Create a new agent.

    Requires authentication. The agent will be in 'draft' status until published.
    """
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Check slug availability
        existing = supabase.table("agents").select("id").eq("slug", agent_data.slug).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Slug already taken")

        # Get user's wallet address
        wallet_result = supabase.table("wallets").select("address").eq(
            "user_id", user["user_id"]
        ).eq("chain", "base").single().execute()

        if not wallet_result.data:
            raise HTTPException(status_code=400, detail="No wallet found")

        creator_address = wallet_result.data["address"]

        # Create agent
        agent_dict = {
            "id": str(uuid.uuid4()),
            "creator_id": user["user_id"],
            "creator_address": creator_address,
            "status": "draft",
            **agent_data.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("agents").insert(agent_dict).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create agent")

        logger.info(f"Agent created: {agent_data.slug} by {user['user_id']}")

        return AgentResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.patch("/{slug}", response_model=AgentResponse)
@limiter.limit("10/minute")
async def update_agent(
    request: Request,
    slug: str,
    update_data: AgentUpdateRequest,
    user: dict = Depends(JWTBearer()),
):
    """Update an agent. Only the creator can update."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Verify ownership
        agent = supabase.table("agents").select("*").eq("slug", slug).single().execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        if agent.data["creator_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow().isoformat()

        result = supabase.table("agents").update(update_dict).eq("slug", slug).execute()

        return AgentResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent")


@router.post("/{slug}/publish", response_model=AgentResponse)
@limiter.limit("5/minute")
async def publish_agent(
    request: Request,
    slug: str,
    user: dict = Depends(JWTBearer()),
):
    """Publish an agent (submit for review or go live)."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Verify ownership
        agent = supabase.table("agents").select("*").eq("slug", slug).single().execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        if agent.data["creator_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        if agent.data["status"] not in ["draft", "suspended"]:
            raise HTTPException(status_code=400, detail="Agent cannot be published from current status")

        # Check if agent has high-risk capabilities (needs review)
        capabilities = agent.data.get("capabilities", [])
        high_risk = ["make_payments", "yield_access", "trade"]
        needs_review = any(cap in high_risk for cap in capabilities)

        new_status = "pending_review" if needs_review else "active"

        result = supabase.table("agents").update({
            "status": new_status,
            "published_at": datetime.utcnow().isoformat() if new_status == "active" else None,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("slug", slug).execute()

        logger.info(f"Agent published: {slug} -> {new_status}")

        return AgentResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish agent")


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_agent(
    request: Request,
    slug: str,
    user: dict = Depends(JWTBearer()),
):
    """Archive an agent (soft delete)."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Verify ownership
        agent = supabase.table("agents").select("creator_id").eq("slug", slug).single().execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        if agent.data["creator_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Archive (soft delete)
        supabase.table("agents").update({
            "status": "archived",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("slug", slug).execute()

        logger.info(f"Agent archived: {slug}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive agent")


# ======================
# AGENT INTERACTION
# ======================

@router.post("/{slug}/message", response_model=AgentMessageResponse)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    slug: str,
    message_data: AgentMessageRequest,
    user: Optional[dict] = Depends(get_current_user),
):
    """
    Send a message to an agent.

    Returns the agent's response. If payment is required, returns
    payment details with HTTP 402.
    """
    import time
    start_time = time.time()

    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Get agent
        agent = supabase.table("agents").select("*").eq("slug", slug).eq("status", "active").single().execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_data = agent.data
        request_id = str(uuid.uuid4())

        # Check if payment required
        pricing = agent_data.get("pricing_model", "free")
        payment_required = pricing == "per_request" and not message_data.payment_tx_hash
        payment_verified = False

        if pricing == "subscription" and user:
            # Check subscription
            sub = supabase.table("agent_subscriptions").select("status").eq(
                "agent_id", agent_data["id"]
            ).eq("user_id", user["user_id"]).eq("status", "active").execute()

            if not sub.data:
                payment_required = True

        # If payment provided, verify it
        if message_data.payment_tx_hash:
            # TODO: Implement payment verification
            payment_verified = True  # Placeholder

        if payment_required and not payment_verified:
            # Return 402 Payment Required
            response_time = int((time.time() - start_time) * 1000)
            return AgentMessageResponse(
                content="",
                payment_required=True,
                payment_amount=agent_data.get("price_per_request"),
                payment_address=agent_data.get("vault_address"),
                request_id=request_id,
                response_time_ms=response_time,
            )

        # TODO: Actually call the agent endpoint
        # For now, return placeholder response
        content = f"Response from {agent_data['name']}. Agent endpoint integration pending."

        response_time = int((time.time() - start_time) * 1000)

        # Log request
        if user:
            supabase.table("agent_requests").insert({
                "id": request_id,
                "agent_id": agent_data["id"],
                "user_id": user["user_id"],
                "request_type": "message",
                "response_status": "success",
                "response_time_ms": response_time,
                "was_paid": payment_verified,
                "payment_amount": message_data.payment_amount,
                "payment_tx": message_data.payment_tx_hash,
            }).execute()

        return AgentMessageResponse(
            content=content,
            payment_required=False,
            request_id=request_id,
            response_time_ms=response_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


# ======================
# SUBSCRIPTIONS
# ======================

@router.post("/{slug}/subscribe", response_model=AgentSubscriptionResponse)
@limiter.limit("5/minute")
async def subscribe_to_agent(
    request: Request,
    slug: str,
    sub_data: AgentSubscribeRequest,
    user: dict = Depends(JWTBearer()),
):
    """Subscribe to an agent."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Get agent
        agent = supabase.table("agents").select("*").eq("slug", slug).eq("status", "active").single().execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        if agent.data["pricing_model"] != "subscription":
            raise HTTPException(status_code=400, detail="Agent does not have subscription pricing")

        # TODO: Verify payment
        # For now, create subscription
        from datetime import timedelta

        now = datetime.utcnow()
        period_end = now + timedelta(days=30 if sub_data.plan_type == "monthly" else 365)

        subscription = {
            "id": str(uuid.uuid4()),
            "agent_id": agent.data["id"],
            "user_id": user["user_id"],
            "plan_type": sub_data.plan_type,
            "price_usdc": agent.data["subscription_price_monthly"],
            "status": "active",
            "started_at": now.isoformat(),
            "current_period_start": now.isoformat(),
            "current_period_end": period_end.isoformat(),
            "last_payment_tx": sub_data.payment_tx_hash,
            "last_payment_at": now.isoformat(),
        }

        result = supabase.table("agent_subscriptions").upsert(
            subscription, on_conflict="agent_id,user_id"
        ).execute()

        return AgentSubscriptionResponse(
            **result.data[0],
            agent_name=agent.data["name"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")


@router.get("/{slug}/subscription", response_model=Optional[AgentSubscriptionResponse])
async def get_subscription(
    request: Request,
    slug: str,
    user: dict = Depends(JWTBearer()),
):
    """Get current user's subscription to an agent."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Get agent
        agent = supabase.table("agents").select("id, name").eq("slug", slug).single().execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Get subscription
        sub = supabase.table("agent_subscriptions").select("*").eq(
            "agent_id", agent.data["id"]
        ).eq("user_id", user["user_id"]).single().execute()

        if not sub.data:
            return None

        return AgentSubscriptionResponse(**sub.data, agent_name=agent.data["name"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")


# ======================
# REVIEWS
# ======================

@router.get("/{slug}/reviews", response_model=List[AgentReviewResponse])
@limiter.limit("30/minute")
async def get_agent_reviews(
    request: Request,
    slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get reviews for an agent."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Get agent ID
        agent = supabase.table("agents").select("id").eq("slug", slug).single().execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        offset = (page - 1) * page_size
        result = supabase.table("agent_reviews").select("*").eq(
            "agent_id", agent.data["id"]
        ).eq("status", "published").order(
            "created_at", desc=True
        ).range(offset, offset + page_size - 1).execute()

        return [AgentReviewResponse(**review) for review in result.data]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reviews: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reviews")


@router.post("/{slug}/reviews", response_model=AgentReviewResponse)
@limiter.limit("3/minute")
async def create_review(
    request: Request,
    slug: str,
    review_data: AgentReviewRequest,
    user: dict = Depends(JWTBearer()),
):
    """Create or update a review for an agent."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Get agent
        agent = supabase.table("agents").select("id").eq("slug", slug).single().execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Check if user has used the agent
        usage = supabase.table("agent_requests").select("id", count="exact").eq(
            "agent_id", agent.data["id"]
        ).eq("user_id", user["user_id"]).execute()

        usage_count = usage.count or 0
        is_verified = usage_count > 0

        review = {
            "id": str(uuid.uuid4()),
            "agent_id": agent.data["id"],
            "user_id": user["user_id"],
            "rating": review_data.rating,
            "title": review_data.title,
            "body": review_data.body,
            "is_verified_user": is_verified,
            "usage_count": usage_count,
            "status": "published",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("agent_reviews").upsert(
            review, on_conflict="agent_id,user_id"
        ).execute()

        return AgentReviewResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating review: {e}")
        raise HTTPException(status_code=500, detail="Failed to create review")


# ======================
# CREATOR ENDPOINTS
# ======================

@router.get("/my/agents", response_model=List[AgentResponse])
async def get_my_agents(
    request: Request,
    user: dict = Depends(JWTBearer()),
):
    """Get agents created by the current user."""
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        result = supabase.table("agents").select("*").eq(
            "creator_id", user["user_id"]
        ).order("created_at", desc=True).execute()

        return [AgentResponse(**agent) for agent in result.data]

    except Exception as e:
        logger.error(f"Error getting my agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agents")


@router.get("/my/earnings", response_model=AgentEarningsResponse)
async def get_my_earnings(
    request: Request,
    agent_slug: Optional[str] = None,
    period: str = Query("month", pattern=r'^(day|week|month|year|all)$'),
    user: dict = Depends(JWTBearer()),
):
    """Get earnings summary for creator's agents."""
    try:
        from supabase_client import get_supabase_client
        from datetime import timedelta

        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database unavailable")

        # Calculate period
        now = datetime.utcnow()
        if period == "day":
            period_start = now - timedelta(days=1)
        elif period == "week":
            period_start = now - timedelta(weeks=1)
        elif period == "month":
            period_start = now - timedelta(days=30)
        elif period == "year":
            period_start = now - timedelta(days=365)
        else:
            period_start = datetime(2020, 1, 1)

        # Get creator's agents
        agents_query = supabase.table("agents").select("id").eq("creator_id", user["user_id"])
        if agent_slug:
            agents_query = agents_query.eq("slug", agent_slug)

        agents = agents_query.execute()
        agent_ids = [a["id"] for a in agents.data]

        if not agent_ids:
            return AgentEarningsResponse(
                agent_id=agent_slug or "all",
                total_revenue_usdc=0,
                creator_earnings_usdc=0,
                pending_earnings_usdc=0,
                total_requests=0,
                total_subscribers=0,
                period_start=period_start,
                period_end=now,
            )

        # Get earnings
        earnings = supabase.table("agent_earnings").select(
            "gross_amount, creator_amount, status"
        ).in_("agent_id", agent_ids).gte(
            "created_at", period_start.isoformat()
        ).execute()

        total_revenue = sum(e["gross_amount"] for e in earnings.data)
        creator_earnings = sum(e["creator_amount"] for e in earnings.data if e["status"] == "confirmed")
        pending = sum(e["creator_amount"] for e in earnings.data if e["status"] == "pending")

        # Get request count
        requests = supabase.table("agent_requests").select(
            "id", count="exact"
        ).in_("agent_id", agent_ids).gte(
            "created_at", period_start.isoformat()
        ).execute()

        # Get subscriber count
        subs = supabase.table("agent_subscriptions").select(
            "id", count="exact"
        ).in_("agent_id", agent_ids).eq("status", "active").execute()

        return AgentEarningsResponse(
            agent_id=agent_slug or "all",
            total_revenue_usdc=total_revenue,
            creator_earnings_usdc=creator_earnings,
            pending_earnings_usdc=pending,
            total_requests=requests.count or 0,
            total_subscribers=subs.count or 0,
            period_start=period_start,
            period_end=now,
        )

    except Exception as e:
        logger.error(f"Error getting earnings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get earnings")
