"""
Payment utilities for USDChat Agent SDK.

Implements x402 micropayments and payment verification.
https://www.x402.org/
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, TypeVar, ParamSpec
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import logging

from .exceptions import PaymentRequiredError


logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class PaymentRequest:
    """
    An x402 payment request.

    This represents a request for payment that can be returned as
    an HTTP 402 response or embedded in an API response.
    """
    amount: float
    currency: str = "USDC"
    chain: str = "base"
    recipient: str = ""  # Wallet address to receive payment

    # Request metadata
    request_id: str = ""
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

    # x402 specific
    x402_version: str = "1.0"
    payment_methods: list = field(default_factory=lambda: ["usdc_transfer", "x402"])

    def to_402_header(self) -> str:
        """Generate the WWW-Authenticate header for HTTP 402."""
        # x402 spec: WWW-Authenticate: X402 address="...", amount="...", ...
        parts = [
            f'address="{self.recipient}"',
            f'amount="{self.amount}"',
            f'currency="{self.currency}"',
            f'chain="{self.chain}"',
            f'request_id="{self.request_id}"',
        ]
        if self.description:
            parts.append(f'description="{self.description}"')
        if self.expires_at:
            parts.append(f'expires="{self.expires_at.isoformat()}"')

        return f"X402 {', '.join(parts)}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON response."""
        return {
            "payment_required": True,
            "x402_version": self.x402_version,
            "amount": self.amount,
            "currency": self.currency,
            "chain": self.chain,
            "recipient": self.recipient,
            "request_id": self.request_id,
            "description": self.description,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "payment_methods": self.payment_methods,
        }


@dataclass
class PaymentVerification:
    """Result of verifying a payment."""
    verified: bool
    tx_hash: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "USDC"
    chain: str = "base"

    # Verification details
    payer_address: Optional[str] = None
    recipient_address: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    block_number: Optional[int] = None

    # Error info
    error: Optional[str] = None


def create_payment_request(
    amount: float,
    recipient: str,
    currency: str = "USDC",
    chain: str = "base",
    description: Optional[str] = None,
    expires_in_minutes: int = 30,
) -> PaymentRequest:
    """
    Create a payment request.

    Args:
        amount: Amount to request in the specified currency
        recipient: Wallet address to receive the payment
        currency: Currency code (default: USDC)
        chain: Blockchain network (default: base)
        description: Human-readable description of what the payment is for
        expires_in_minutes: How long the request is valid

    Returns:
        PaymentRequest that can be converted to x402 format
    """
    import uuid

    return PaymentRequest(
        amount=amount,
        currency=currency,
        chain=chain,
        recipient=recipient,
        request_id=str(uuid.uuid4()),
        description=description,
        expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
    )


async def verify_payment(
    tx_hash: str,
    expected_amount: float,
    expected_recipient: str,
    chain: str = "base",
    currency: str = "USDC",
) -> PaymentVerification:
    """
    Verify a payment transaction.

    Args:
        tx_hash: Transaction hash to verify
        expected_amount: Expected payment amount
        expected_recipient: Expected recipient address
        chain: Blockchain network
        currency: Expected currency

    Returns:
        PaymentVerification with verification result
    """
    # This would integrate with chain_utils or the API
    # For now, return a placeholder that the platform will implement

    logger.info(f"Verifying payment: {tx_hash} for {expected_amount} {currency}")

    # TODO: Implement actual verification via platform API
    # This will call: POST /api/v1/payments/verify
    # {
    #     "tx_hash": tx_hash,
    #     "expected_amount": expected_amount,
    #     "expected_recipient": expected_recipient,
    #     "chain": chain,
    #     "currency": currency
    # }

    return PaymentVerification(
        verified=False,
        error="Payment verification requires platform API (not implemented in standalone SDK)",
    )


def x402_payment(
    amount: float,
    description: Optional[str] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to require x402 payment for a method.

    Usage:
        class MyAgent(Agent):
            @x402_payment(amount=0.01, description="Generate image")
            async def generate_image(self, prompt: str) -> str:
                # This method requires 0.01 USDC payment
                return "image_url"

    Args:
        amount: Payment amount in USDC
        description: Human-readable description for the payment

    The decorated method will:
    1. Check if payment is already verified in context
    2. If not, raise PaymentRequiredError with x402 details
    3. If verified, proceed with the method
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # Store payment metadata on the function
        func._x402_amount = amount
        func._x402_description = description or f"Payment for {func.__name__}"

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get context from args
            context = None
            if args and hasattr(args[0], "payment_verified"):
                context = args[0]
            elif "context" in kwargs:
                context = kwargs["context"]

            # Check if payment already verified
            if context and context.payment_verified:
                # Payment verified, check amount
                if context.payment_amount and context.payment_amount >= amount:
                    return await func(self, *args, **kwargs)

            # Payment required - get agent's vault address
            vault_address = ""
            if context:
                vault_address = context.agent_vault_address or ""

            raise PaymentRequiredError(
                amount=amount,
                currency="USDC",
                payment_address=vault_address,
                message=func._x402_description,
            )

        return wrapper

    return decorator


def generate_payment_signature(
    request_id: str,
    amount: float,
    recipient: str,
    secret: str,
) -> str:
    """
    Generate HMAC signature for a payment request.

    Used to verify that payment callbacks are authentic.
    """
    message = f"{request_id}:{amount}:{recipient}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_payment_signature(
    request_id: str,
    amount: float,
    recipient: str,
    signature: str,
    secret: str,
) -> bool:
    """Verify a payment signature is valid."""
    expected = generate_payment_signature(request_id, amount, recipient, secret)
    return hmac.compare_digest(signature, expected)
