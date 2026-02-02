"""
Exceptions for USDChat Agent SDK.
"""

from typing import Optional, Dict, Any


class AgentError(Exception):
    """Base exception for agent errors."""

    def __init__(self, message: str, code: str = "agent_error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class PaymentRequiredError(AgentError):
    """
    Raised when payment is required to proceed.

    This translates to an HTTP 402 response with x402 payment details.
    """

    def __init__(
        self,
        amount: float,
        currency: str = "USDC",
        payment_address: str = "",
        message: str = "Payment required",
        request_id: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            code="payment_required",
            details={
                "amount": amount,
                "currency": currency,
                "payment_address": payment_address,
                "request_id": request_id,
            }
        )
        self.amount = amount
        self.currency = currency
        self.payment_address = payment_address
        self.request_id = request_id

    def to_402_response(self) -> Dict[str, Any]:
        """Format as HTTP 402 response body."""
        return {
            "error": "payment_required",
            "message": self.message,
            "payment": {
                "amount": self.amount,
                "currency": self.currency,
                "address": self.payment_address,
                "request_id": self.request_id,
                "x402_version": "1.0",
            }
        }


class CapabilityDeniedError(AgentError):
    """Raised when an agent tries to use a capability the user hasn't granted."""

    def __init__(self, capability: str, message: str = "Capability not granted"):
        super().__init__(
            message=message,
            code="capability_denied",
            details={"capability": capability}
        )
        self.capability = capability


class RateLimitError(AgentError):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        limit_type: str = "requests",
        limit: int = 0,
        reset_at: Optional[str] = None,
        message: str = "Rate limit exceeded",
    ):
        super().__init__(
            message=message,
            code="rate_limited",
            details={
                "limit_type": limit_type,
                "limit": limit,
                "reset_at": reset_at,
            }
        )
        self.limit_type = limit_type
        self.limit = limit
        self.reset_at = reset_at


class ConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="configuration_error",
            details={"field": field} if field else {}
        )
        self.field = field


class TransactionError(AgentError):
    """Raised when a transaction fails."""

    def __init__(
        self,
        message: str,
        tx_hash: Optional[str] = None,
        chain: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            code="transaction_error",
            details={
                "tx_hash": tx_hash,
                "chain": chain,
                "reason": reason,
            }
        )
        self.tx_hash = tx_hash
        self.chain = chain
        self.reason = reason


class AuthenticationError(AgentError):
    """Raised for authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="authentication_error"
        )


class ValidationError(AgentError):
    """Raised for input validation failures."""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(
            message=message,
            code="validation_error",
            details={
                "field": field,
                "value": str(value) if value is not None else None,
            }
        )
        self.field = field
        self.value = value
