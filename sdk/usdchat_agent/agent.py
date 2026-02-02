"""
Base Agent class for USDChat Agent SDK.

This is the foundation for building agents that can:
- Accept payments via x402 micropayments
- Make payments on user behalf
- Access yield strategies
- Execute trades
- And more...
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Union
from enum import Enum
import asyncio
import logging
from datetime import datetime

from .types import AgentContext, RequestMetadata, PaymentInfo
from .exceptions import AgentError, PaymentRequiredError


logger = logging.getLogger(__name__)


class PricingModel(str, Enum):
    """How the agent charges for usage."""
    FREE = "free"
    PER_REQUEST = "per_request"
    SUBSCRIPTION = "subscription"
    TIPS_ONLY = "tips_only"


class AgentStatus(str, Enum):
    """Agent lifecycle status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    description: str
    category: str = "utility"
    tags: List[str] = field(default_factory=list)

    # Monetization
    pricing_model: PricingModel = PricingModel.FREE
    price_per_request: Optional[float] = None  # USDC
    subscription_price_monthly: Optional[float] = None  # USDC
    min_tip: float = 0.01
    accepts_tips: bool = True

    # Revenue split (must sum to 100)
    creator_share_percent: float = 70.0
    platform_share_percent: float = 20.0
    referrer_share_percent: float = 10.0

    # Technical
    sdk_version: str = "0.1.0"
    runtime: str = "python"

    # Rate limits
    requests_per_minute: int = 60
    requests_per_day: int = 10000

    # Capabilities this agent needs
    required_capabilities: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """Validate the configuration."""
        if not self.name:
            raise ValueError("Agent name is required")

        if self.pricing_model == PricingModel.PER_REQUEST and not self.price_per_request:
            raise ValueError("price_per_request is required for per_request pricing")

        if self.pricing_model == PricingModel.SUBSCRIPTION and not self.subscription_price_monthly:
            raise ValueError("subscription_price_monthly is required for subscription pricing")

        total_share = self.creator_share_percent + self.platform_share_percent + self.referrer_share_percent
        if abs(total_share - 100.0) > 0.01:
            raise ValueError(f"Revenue shares must sum to 100, got {total_share}")


@dataclass
class AgentResponse:
    """Response from an agent handler."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    payment_received: Optional[PaymentInfo] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class Agent(ABC):
    """
    Base class for USDChat agents.

    Subclass this to create your own agent:

        class MyAgent(Agent):
            async def handle(self, message: str, context: AgentContext) -> AgentResponse:
                # Your logic here
                return AgentResponse(content="Hello!")

    Configuration:

        agent = MyAgent(
            name="My Agent",
            description="Does amazing things",
            category="utility",
            pricing_model="per_request",
            price_per_request=0.01
        )
    """

    def __init__(
        self,
        name: str,
        description: str,
        category: str = "utility",
        tags: Optional[List[str]] = None,
        pricing_model: Union[str, PricingModel] = PricingModel.FREE,
        price_per_request: Optional[float] = None,
        subscription_price_monthly: Optional[float] = None,
        min_tip: float = 0.01,
        accepts_tips: bool = True,
        creator_share_percent: float = 70.0,
        platform_share_percent: float = 20.0,
        referrer_share_percent: float = 10.0,
        requests_per_minute: int = 60,
        requests_per_day: int = 10000,
        required_capabilities: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize the agent with configuration."""
        if isinstance(pricing_model, str):
            pricing_model = PricingModel(pricing_model)

        self.config = AgentConfig(
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            pricing_model=pricing_model,
            price_per_request=price_per_request,
            subscription_price_monthly=subscription_price_monthly,
            min_tip=min_tip,
            accepts_tips=accepts_tips,
            creator_share_percent=creator_share_percent,
            platform_share_percent=platform_share_percent,
            referrer_share_percent=referrer_share_percent,
            requests_per_minute=requests_per_minute,
            requests_per_day=requests_per_day,
            required_capabilities=required_capabilities or [],
        )
        self.config.validate()

        # Internal state
        self._handlers: Dict[str, Callable] = {}
        self._startup_hooks: List[Callable] = []
        self._shutdown_hooks: List[Callable] = []

        # Auto-discover capabilities from decorated methods
        self._discover_capabilities()

    def _discover_capabilities(self) -> None:
        """Find all methods decorated with @capability."""
        for name in dir(self):
            if name.startswith("_"):
                continue
            method = getattr(self, name, None)
            if callable(method) and hasattr(method, "_capability"):
                cap = method._capability
                if cap not in self.config.required_capabilities:
                    self.config.required_capabilities.append(cap)

    @abstractmethod
    async def handle(self, message: str, context: AgentContext) -> AgentResponse:
        """
        Handle an incoming request.

        This is the main entry point for your agent. Override this method
        to implement your agent's logic.

        Args:
            message: The user's message/request
            context: Request context including user info, payment status, etc.

        Returns:
            AgentResponse with the result
        """
        pass

    async def on_startup(self) -> None:
        """Called when the agent starts. Override to add initialization logic."""
        pass

    async def on_shutdown(self) -> None:
        """Called when the agent stops. Override to add cleanup logic."""
        pass

    async def on_payment_received(self, payment: PaymentInfo) -> None:
        """Called when a payment is received. Override to add payment handling logic."""
        pass

    async def on_subscription_started(self, user_id: str, plan: str) -> None:
        """Called when a user starts a subscription. Override to add welcome logic."""
        pass

    async def on_subscription_cancelled(self, user_id: str) -> None:
        """Called when a subscription is cancelled. Override to add farewell logic."""
        pass

    def requires_payment(self, context: AgentContext) -> bool:
        """
        Check if this request requires payment.

        Override to implement custom payment logic (e.g., free tier, trial).
        """
        if self.config.pricing_model == PricingModel.FREE:
            return False

        if self.config.pricing_model == PricingModel.TIPS_ONLY:
            return False

        if self.config.pricing_model == PricingModel.SUBSCRIPTION:
            # Check if user has active subscription
            return not context.has_active_subscription

        if self.config.pricing_model == PricingModel.PER_REQUEST:
            # Check if payment included
            return not context.payment_verified

        return False

    def get_payment_amount(self, context: AgentContext) -> float:
        """Get the amount required for this request."""
        if self.config.pricing_model == PricingModel.PER_REQUEST:
            return self.config.price_per_request or 0

        if self.config.pricing_model == PricingModel.SUBSCRIPTION:
            return self.config.subscription_price_monthly or 0

        return 0

    async def process_request(
        self,
        message: str,
        context: AgentContext
    ) -> AgentResponse:
        """
        Process an incoming request with payment and capability checks.

        This is the internal method called by the platform. It handles:
        - Payment verification
        - Capability checks
        - Rate limiting
        - Error handling

        Don't override this - override `handle()` instead.
        """
        try:
            # Check payment requirement
            if self.requires_payment(context):
                amount = self.get_payment_amount(context)
                raise PaymentRequiredError(
                    amount=amount,
                    currency="USDC",
                    payment_address=context.agent_vault_address,
                    message=f"Payment of {amount} USDC required"
                )

            # Handle the request
            response = await self.handle(message, context)

            # Track payment if received
            if context.payment_verified and context.payment_amount:
                payment_info = PaymentInfo(
                    amount=context.payment_amount,
                    currency="USDC",
                    tx_hash=context.payment_tx_hash,
                    verified=True,
                    received_at=datetime.utcnow()
                )
                response.payment_received = payment_info
                await self.on_payment_received(payment_info)

            return response

        except PaymentRequiredError:
            raise  # Re-raise payment errors

        except Exception as e:
            logger.exception(f"Agent error: {e}")
            return AgentResponse(
                content="",
                error=str(e)
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent config for registration."""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "category": self.config.category,
            "tags": self.config.tags,
            "pricing_model": self.config.pricing_model.value,
            "price_per_request": self.config.price_per_request,
            "subscription_price_monthly": self.config.subscription_price_monthly,
            "min_tip": self.config.min_tip,
            "accepts_tips": self.config.accepts_tips,
            "creator_share_percent": self.config.creator_share_percent,
            "platform_share_percent": self.config.platform_share_percent,
            "referrer_share_percent": self.config.referrer_share_percent,
            "requests_per_minute": self.config.requests_per_minute,
            "requests_per_day": self.config.requests_per_day,
            "required_capabilities": self.config.required_capabilities,
            "sdk_version": self.config.sdk_version,
            "runtime": self.config.runtime,
        }

    def __repr__(self) -> str:
        return f"<Agent name={self.config.name!r} pricing={self.config.pricing_model.value}>"
