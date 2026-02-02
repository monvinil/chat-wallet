"""
Type definitions for USDChat Agent SDK.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


@dataclass
class UserInfo:
    """Information about the user making the request."""
    user_id: str
    wallet_address: str
    solana_address: Optional[str] = None

    # Subscription status
    is_subscribed: bool = False
    subscription_expires_at: Optional[datetime] = None

    # Usage stats
    total_requests: int = 0
    total_spent_usdc: float = 0.0

    # Permissions granted to this agent
    granted_capabilities: List[str] = field(default_factory=list)


@dataclass
class PaymentInfo:
    """Information about a payment."""
    amount: float
    currency: str = "USDC"
    tx_hash: Optional[str] = None
    verified: bool = False
    received_at: Optional[datetime] = None

    # For subscriptions
    is_subscription: bool = False
    subscription_period_end: Optional[datetime] = None


@dataclass
class RequestMetadata:
    """Metadata about the incoming request."""
    request_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Source info
    source: str = "api"  # 'api', 'chat', 'webhook', 'scheduled'
    ip_hash: Optional[str] = None
    user_agent: Optional[str] = None

    # x402 data
    x402_request_id: Optional[str] = None
    x402_payment_hash: Optional[str] = None

    # Custom data
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """
    Context provided to agent handlers.

    Contains all information about the current request including
    user info, payment status, and metadata.
    """
    # User info
    user: UserInfo

    # Request metadata
    metadata: RequestMetadata

    # Payment status
    payment_required: bool = False
    payment_verified: bool = False
    payment_amount: Optional[float] = None
    payment_tx_hash: Optional[str] = None

    # Subscription status
    has_active_subscription: bool = False
    subscription_expires_at: Optional[datetime] = None

    # Agent context
    agent_id: str = ""
    agent_vault_address: str = ""

    # Conversation history (for stateful agents)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Custom context
    custom: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })


class Chain(str, Enum):
    """Supported blockchain networks."""
    BASE = "base"
    ETHEREUM = "ethereum"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    POLYGON = "polygon"
    SOLANA = "solana"


class TransactionType(str, Enum):
    """Types of transactions."""
    TRANSFER = "transfer"
    SWAP = "swap"
    BRIDGE = "bridge"
    YIELD_DEPOSIT = "yield_deposit"
    YIELD_WITHDRAW = "yield_withdraw"
    AGENT_PAYMENT = "agent_payment"
    SUBSCRIPTION = "subscription"
    TIP = "tip"


@dataclass
class TransactionRequest:
    """Request to execute a transaction on user's behalf."""
    type: TransactionType
    amount: float
    currency: str = "USDC"
    chain: Chain = Chain.BASE

    # For transfers
    to_address: Optional[str] = None

    # For swaps
    from_token: Optional[str] = None
    to_token: Optional[str] = None
    slippage_percent: float = 0.5

    # For bridges
    destination_chain: Optional[Chain] = None

    # For yield
    protocol: Optional[str] = None  # 'aave', 'compound', etc.

    # Metadata
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransactionResult:
    """Result of a transaction execution."""
    success: bool
    tx_hash: Optional[str] = None
    error: Optional[str] = None

    # Transaction details
    amount: float = 0
    fee: float = 0
    chain: Optional[Chain] = None

    # Timing
    submitted_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None

    # For pending transactions
    is_pending: bool = False
    estimated_confirmation: Optional[datetime] = None
