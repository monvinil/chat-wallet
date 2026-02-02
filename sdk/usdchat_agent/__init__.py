"""
USDChat Agent SDK

Create AI agents that earn money. This SDK provides the building blocks
for creating agents that can accept payments, make payments, and interact
with the USDChat ecosystem.

Example usage:
    from usdchat_agent import Agent, capability, x402_payment

    class MyAgent(Agent):
        @capability("accept_payments")
        async def handle_request(self, message: str) -> str:
            # Your agent logic here
            return "Response"

    agent = MyAgent(
        name="My Agent",
        description="Does cool things",
        pricing_model="per_request",
        price_usdc=0.01
    )
"""

from .agent import Agent, AgentConfig, AgentResponse
from .capabilities import capability, Capability
from .payments import x402_payment, PaymentRequest, PaymentVerification
from .types import (
    AgentContext,
    UserInfo,
    PaymentInfo,
    RequestMetadata,
)
from .exceptions import (
    AgentError,
    PaymentRequiredError,
    CapabilityDeniedError,
    RateLimitError,
)

__version__ = "0.1.0"
__all__ = [
    # Core
    "Agent",
    "AgentConfig",
    "AgentResponse",
    # Capabilities
    "capability",
    "Capability",
    # Payments
    "x402_payment",
    "PaymentRequest",
    "PaymentVerification",
    # Types
    "AgentContext",
    "UserInfo",
    "PaymentInfo",
    "RequestMetadata",
    # Exceptions
    "AgentError",
    "PaymentRequiredError",
    "CapabilityDeniedError",
    "RateLimitError",
]
