"""
Capability system for USDChat Agent SDK.

Capabilities define what an agent can do. Users must explicitly grant
permissions for agents to use certain capabilities.

Built-in capabilities:
- accept_payments: Agent can receive payments
- make_payments: Agent can send payments on user's behalf
- yield_access: Agent can deposit/withdraw from yield protocols
- trade: Agent can execute trades
- read_balance: Agent can view user's balance
- read_history: Agent can view user's transaction history
- notifications: Agent can send notifications
- schedule_tasks: Agent can create scheduled tasks
"""

from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Callable, Optional, List, TypeVar, ParamSpec
import logging

from .exceptions import CapabilityDeniedError


logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class CapabilityLevel(str, Enum):
    """Risk level for capabilities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Capability:
    """Definition of a capability."""
    name: str
    display_name: str
    description: str
    risk_level: CapabilityLevel = CapabilityLevel.LOW
    requires_verification: bool = False
    daily_limit_usdc: Optional[float] = None
    per_request_limit_usdc: Optional[float] = None


# Built-in capabilities
BUILTIN_CAPABILITIES = {
    "accept_payments": Capability(
        name="accept_payments",
        display_name="Accept Payments",
        description="Agent can receive payments via x402 or direct transfer",
        risk_level=CapabilityLevel.LOW,
        requires_verification=False,
    ),
    "make_payments": Capability(
        name="make_payments",
        display_name="Make Payments",
        description="Agent can send payments on your behalf",
        risk_level=CapabilityLevel.HIGH,
        requires_verification=True,
        daily_limit_usdc=100.0,
        per_request_limit_usdc=10.0,
    ),
    "yield_access": Capability(
        name="yield_access",
        display_name="Yield Strategies",
        description="Agent can deposit and withdraw from yield protocols",
        risk_level=CapabilityLevel.HIGH,
        requires_verification=True,
        daily_limit_usdc=1000.0,
    ),
    "trade": Capability(
        name="trade",
        display_name="Trading",
        description="Agent can execute trades on DEXs or perpetual platforms",
        risk_level=CapabilityLevel.CRITICAL,
        requires_verification=True,
        daily_limit_usdc=500.0,
    ),
    "read_balance": Capability(
        name="read_balance",
        display_name="Read Balance",
        description="Agent can view your wallet balance",
        risk_level=CapabilityLevel.LOW,
        requires_verification=False,
    ),
    "read_history": Capability(
        name="read_history",
        display_name="Read History",
        description="Agent can view your transaction history",
        risk_level=CapabilityLevel.MEDIUM,
        requires_verification=False,
    ),
    "notifications": Capability(
        name="notifications",
        display_name="Send Notifications",
        description="Agent can send you notifications",
        risk_level=CapabilityLevel.LOW,
        requires_verification=False,
    ),
    "schedule_tasks": Capability(
        name="schedule_tasks",
        display_name="Schedule Tasks",
        description="Agent can create scheduled tasks",
        risk_level=CapabilityLevel.MEDIUM,
        requires_verification=False,
    ),
}


def capability(
    name: str,
    check_permissions: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to mark a method as requiring a specific capability.

    Usage:
        class MyAgent(Agent):
            @capability("make_payments")
            async def send_money(self, to: str, amount: float):
                # This method can only be called if user granted make_payments
                pass

    Args:
        name: The capability name (must be in BUILTIN_CAPABILITIES or custom)
        check_permissions: If True, verify user granted this capability

    Raises:
        CapabilityDeniedError: If user hasn't granted the required capability
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # Store capability metadata on the function
        func._capability = name
        func._check_permissions = check_permissions

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get context from first positional arg or kwargs
            context = None
            if args and hasattr(args[0], "user"):
                context = args[0]
            elif "context" in kwargs:
                context = kwargs["context"]

            # Check permission if context available and checking enabled
            if check_permissions and context:
                granted = getattr(context.user, "granted_capabilities", [])
                if name not in granted:
                    cap_info = BUILTIN_CAPABILITIES.get(name)
                    cap_display = cap_info.display_name if cap_info else name
                    raise CapabilityDeniedError(
                        capability=name,
                        message=f"Permission '{cap_display}' is required but not granted"
                    )

            return await func(self, *args, **kwargs)

        return wrapper

    return decorator


def requires_capabilities(*capability_names: str) -> Callable[[type], type]:
    """
    Class decorator to declare required capabilities for an agent.

    Usage:
        @requires_capabilities("accept_payments", "read_balance")
        class MyAgent(Agent):
            pass
    """

    def decorator(cls: type) -> type:
        # Store on class
        existing = getattr(cls, "_required_capabilities", [])
        cls._required_capabilities = list(set(existing + list(capability_names)))
        return cls

    return decorator


def get_capability_info(name: str) -> Optional[Capability]:
    """Get information about a capability."""
    return BUILTIN_CAPABILITIES.get(name)


def get_all_capabilities() -> List[Capability]:
    """Get all built-in capabilities."""
    return list(BUILTIN_CAPABILITIES.values())


def validate_capabilities(names: List[str]) -> List[str]:
    """
    Validate a list of capability names.
    Returns list of invalid names, empty if all valid.
    """
    invalid = []
    for name in names:
        if name not in BUILTIN_CAPABILITIES:
            invalid.append(name)
    return invalid
