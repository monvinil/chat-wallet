"""
Agent schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PricingModel(str, Enum):
    FREE = "free"
    PER_REQUEST = "per_request"
    SUBSCRIPTION = "subscription"
    TIPS_ONLY = "tips_only"


class AgentStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class AgentCategory(str, Enum):
    TRADING = "trading"
    CONTENT = "content"
    SERVICE = "service"
    CHARACTER = "character"
    YIELD = "yield"
    UTILITY = "utility"


# Request schemas

class AgentCreateRequest(BaseModel):
    """Request to create a new agent."""
    name: str = Field(..., min_length=3, max_length=200)
    slug: str = Field(..., min_length=3, max_length=100, pattern=r'^[a-z0-9-]+$')
    description: str = Field(..., min_length=10, max_length=2000)
    category: AgentCategory

    # Optional fields
    tags: List[str] = Field(default_factory=list, max_length=10)
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None

    # Monetization
    pricing_model: PricingModel = PricingModel.FREE
    price_per_request: Optional[float] = Field(None, ge=0.001, le=1000)
    subscription_price_monthly: Optional[float] = Field(None, ge=0.1, le=10000)
    min_tip: float = Field(0.01, ge=0.001)
    accepts_tips: bool = True

    # Revenue split (must sum to 100)
    creator_share_percent: float = Field(70.0, ge=50, le=90)
    platform_share_percent: float = Field(20.0, ge=10, le=30)
    referrer_share_percent: float = Field(10.0, ge=0, le=20)

    # Technical
    endpoint_url: Optional[str] = None
    source_code_url: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)

    # Rate limits
    requests_per_minute: int = Field(60, ge=1, le=1000)
    requests_per_day: int = Field(10000, ge=100, le=1000000)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        # Ensure tags are lowercase and alphanumeric
        return [tag.lower().strip() for tag in v if tag.strip()]

    @field_validator('creator_share_percent', 'platform_share_percent', 'referrer_share_percent')
    @classmethod
    def validate_shares(cls, v, info):
        # Shares will be validated together in model_validator
        return v

    def model_post_init(self, __context):
        # Validate revenue split
        total = self.creator_share_percent + self.platform_share_percent + self.referrer_share_percent
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Revenue shares must sum to 100, got {total}")

        # Validate pricing model requirements
        if self.pricing_model == PricingModel.PER_REQUEST and not self.price_per_request:
            raise ValueError("price_per_request required for per_request pricing")
        if self.pricing_model == PricingModel.SUBSCRIPTION and not self.subscription_price_monthly:
            raise ValueError("subscription_price_monthly required for subscription pricing")


class AgentUpdateRequest(BaseModel):
    """Request to update an agent."""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    tags: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    endpoint_url: Optional[str] = None
    source_code_url: Optional[str] = None
    requests_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    requests_per_day: Optional[int] = Field(None, ge=100, le=1000000)


class AgentMessageRequest(BaseModel):
    """Request to send a message to an agent."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None

    # Payment info (for x402)
    payment_tx_hash: Optional[str] = None
    payment_amount: Optional[float] = None


class AgentSubscribeRequest(BaseModel):
    """Request to subscribe to an agent."""
    plan_type: str = Field("monthly", pattern=r'^(monthly|yearly|lifetime)$')
    payment_tx_hash: str


class AgentReviewRequest(BaseModel):
    """Request to review an agent."""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = Field(None, max_length=2000)


# Response schemas

class AgentResponse(BaseModel):
    """Agent details response."""
    id: str
    slug: str
    name: str
    description: str
    category: str
    tags: List[str]
    avatar_url: Optional[str]
    banner_url: Optional[str]

    # Creator
    creator_id: Optional[str]
    creator_address: str

    # Monetization
    pricing_model: str
    price_per_request: Optional[float]
    subscription_price_monthly: Optional[float]
    accepts_tips: bool

    # Status
    status: str
    is_verified: bool
    is_featured: bool

    # Stats
    total_users: int
    total_requests: int
    total_revenue_usdc: float
    average_rating: float
    rating_count: int

    # Dates
    created_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Paginated list of agents."""
    agents: List[AgentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class AgentMessageResponse(BaseModel):
    """Response from agent message."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Payment info
    payment_required: bool = False
    payment_amount: Optional[float] = None
    payment_address: Optional[str] = None

    # Request tracking
    request_id: str
    response_time_ms: int


class AgentEarningsResponse(BaseModel):
    """Agent earnings summary."""
    agent_id: str
    total_revenue_usdc: float
    creator_earnings_usdc: float
    pending_earnings_usdc: float
    total_requests: int
    total_subscribers: int
    period_start: datetime
    period_end: datetime


class AgentSubscriptionResponse(BaseModel):
    """User's subscription to an agent."""
    id: str
    agent_id: str
    agent_name: str
    plan_type: str
    price_usdc: float
    status: str
    current_period_start: datetime
    current_period_end: Optional[datetime]
    auto_renew: bool


class AgentReviewResponse(BaseModel):
    """Agent review."""
    id: str
    agent_id: str
    user_id: str
    rating: int
    title: Optional[str]
    body: Optional[str]
    is_verified_user: bool
    helpful_count: int
    created_at: datetime


class AgentCapabilityResponse(BaseModel):
    """Agent capability info."""
    name: str
    display_name: str
    description: str
    risk_level: str
    requires_verification: bool
