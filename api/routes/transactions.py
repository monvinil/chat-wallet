"""
Transaction API Routes
Endpoints for sending, receiving, and tracking transactions.
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
import secrets
import json

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas.transaction import (
    TransactionPreviewRequest,
    TransactionPreview,
    TransactionRequest,
    TransactionResponse,
    TransactionStatus,
    TransactionHistoryItem,
    TransactionHistoryResponse,
    TransactionType,
    BridgePreviewRequest,
    BridgePreview,
)
from api.schemas.common import APIResponse, ErrorResponse
from api.middleware.auth import JWTBearer
from api.config import settings

from config import NETWORKS, calculate_fee
from chain_utils import ChainUtils
from utils.logger import logger


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# In-memory preview store (in production, use Redis or database)
# Format: {preview_id: {data, expires_at}}
_preview_store: Dict[str, Dict[str, Any]] = {}


def format_address(address: str) -> str:
    """Format address for display."""
    if len(address) > 12:
        return f"{address[:6]}...{address[-4:]}"
    return address


def format_usd(amount: Decimal) -> str:
    """Format amount as USD."""
    return f"${amount:.2f}"


def cleanup_expired_previews():
    """Remove expired previews from store."""
    now = datetime.utcnow()
    expired = [k for k, v in _preview_store.items() if v.get("expires_at", now) < now]
    for k in expired:
        del _preview_store[k]


# ============================================================================
# PREVIEW ENDPOINTS
# ============================================================================


@router.post(
    "/preview",
    response_model=APIResponse[TransactionPreview],
    summary="Preview transaction",
    description="Get transaction preview with fee breakdown before execution"
)
async def preview_transaction(
    data: TransactionPreviewRequest,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[TransactionPreview]:
    """
    Preview a transaction before execution.

    Shows:
    - Exact amount to send
    - Fee breakdown
    - Total cost
    - Estimated confirmation time

    Returns a preview_id that must be used for execution.
    """
    wallet_address = credentials.get("wallet_address")
    if not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet address in token"
        )

    # Validate chain
    network = NETWORKS.get(data.chain)
    if not network:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported chain: {data.chain}"
        )

    # Calculate fee
    fee = Decimal(str(calculate_fee(float(data.amount))))
    total = data.amount + fee

    # Generate preview ID
    preview_id = secrets.token_urlsafe(16)
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Store preview
    _preview_store[preview_id] = {
        "user_id": credentials.get("sub"),
        "wallet_address": wallet_address,
        "to_address": data.to_address,
        "amount": str(data.amount),
        "fee": str(fee),
        "total": str(total),
        "chain": data.chain,
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
    }

    # Cleanup old previews
    cleanup_expired_previews()

    preview = TransactionPreview(
        amount=data.amount,
        amount_formatted=format_usd(data.amount),
        to_address=data.to_address,
        to_address_short=format_address(data.to_address),
        from_address=wallet_address,
        from_address_short=format_address(wallet_address),
        chain=data.chain,
        chain_name=network["name"],
        fee=fee,
        fee_formatted=f"${fee:.4f}",
        total=total,
        total_formatted=format_usd(total),
        preview_id=preview_id,
        expires_at=expires_at,
    )

    return APIResponse(data=preview)


@router.post(
    "/bridge/preview",
    response_model=APIResponse[BridgePreview],
    summary="Preview cross-chain bridge",
    description="Get bridge preview for cross-chain USDC transfer"
)
async def preview_bridge(
    data: BridgePreviewRequest,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[BridgePreview]:
    """
    Preview a cross-chain bridge transaction.

    Uses Circle CCTP for native USDC transfers between chains.
    """
    # Validate chains
    from_network = NETWORKS.get(data.from_chain)
    to_network = NETWORKS.get(data.to_chain)

    if not from_network or not to_network:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source or destination chain"
        )

    if data.from_chain == data.to_chain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination chains must be different"
        )

    # CCTP bridge fee (typically minimal, ~$0.10-0.50 gas)
    bridge_fee = Decimal("0.25")
    total_received = data.amount - bridge_fee

    # Generate preview ID
    preview_id = secrets.token_urlsafe(16)
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Store preview
    _preview_store[preview_id] = {
        "user_id": credentials.get("sub"),
        "wallet_address": credentials.get("wallet_address"),
        "from_chain": data.from_chain,
        "to_chain": data.to_chain,
        "amount": str(data.amount),
        "bridge_fee": str(bridge_fee),
        "total_received": str(total_received),
        "type": "bridge",
        "expires_at": expires_at,
    }

    preview = BridgePreview(
        from_chain=data.from_chain,
        from_chain_name=from_network["name"],
        to_chain=data.to_chain,
        to_chain_name=to_network["name"],
        amount=data.amount,
        amount_formatted=format_usd(data.amount),
        bridge_fee=bridge_fee,
        bridge_fee_formatted=format_usd(bridge_fee),
        estimated_time="10-20 minutes",
        total_received=total_received,
        total_received_formatted=format_usd(total_received),
        preview_id=preview_id,
        expires_at=expires_at,
    )

    return APIResponse(data=preview)


# ============================================================================
# EXECUTION ENDPOINTS
# ============================================================================


@router.post(
    "/send",
    response_model=APIResponse[TransactionResponse],
    summary="Execute transaction",
    description="Execute a previously previewed transaction"
)
@limiter.limit("10/minute")
async def execute_transaction(
    request: Request,
    data: TransactionRequest,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[TransactionResponse]:
    """
    Execute a transaction.

    Requires:
    - Valid preview_id from /preview endpoint
    - user_confirmed=true

    The preview must:
    - Not be expired (10 minute window)
    - Belong to the authenticated user
    """
    # Get preview
    preview = _preview_store.get(data.preview_id)
    if not preview:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preview not found or expired. Please create a new preview."
        )

    # Verify ownership
    if preview.get("user_id") != credentials.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Preview does not belong to this user"
        )

    # Verify not expired
    if preview.get("expires_at", datetime.min) < datetime.utcnow():
        del _preview_store[data.preview_id]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preview has expired. Please create a new preview."
        )

    # Check if it's a bridge (different execution path)
    if preview.get("type") == "bridge":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /bridge/execute for bridge transactions"
        )

    # Get wallet data (this would need the password/unlocked wallet in real implementation)
    # For now, we'll need to integrate with the session-based wallet system
    # This is a placeholder for the actual signing logic
    try:
        # Import the direct transaction executor
        from direct_tx import get_direct_executor

        # NOTE: In production, the private key would come from the unlocked wallet session
        # For API use, we'd need a way to securely pass the signing key
        # Options:
        # 1. Require wallet unlock before transaction (store key encrypted in session)
        # 2. Use hardware wallet signing
        # 3. Use MPC signing (Circle Programmable Wallets)

        # For now, return a mock response since we can't sign without the key
        # This endpoint demonstrates the flow; actual signing requires wallet integration

        logger.warning("Transaction execution requested but signing not implemented in API yet")

        # Clean up preview
        del _preview_store[data.preview_id]

        # Return mock response (in production, would execute real transaction)
        mock_tx_hash = f"0x{''.join(secrets.token_hex(32))}"
        chain = preview.get("chain", "base-mainnet")
        network = NETWORKS.get(chain, NETWORKS["base-mainnet"])

        response = TransactionResponse(
            success=True,
            tx_hash=mock_tx_hash,
            explorer_url=f"{network.get('explorer_url', '')}/tx/{mock_tx_hash}",
            amount=Decimal(preview.get("amount", "0")),
            amount_formatted=format_usd(Decimal(preview.get("amount", "0"))),
            to_address=preview.get("to_address", ""),
            chain=chain,
            chain_name=network.get("name", chain),
            status=TransactionStatus.CONFIRMING,
            message="Transaction submitted (mock - signing not implemented in API)"
        )

        return APIResponse(data=response)

    except Exception as e:
        logger.error(f"Transaction execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction failed: {str(e)}"
        )


# ============================================================================
# HISTORY ENDPOINTS
# ============================================================================


@router.get(
    "/history",
    response_model=TransactionHistoryResponse,
    summary="Get transaction history",
    description="Get paginated transaction history"
)
async def get_transaction_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    chain: Optional[str] = Query(default=None, description="Filter by chain"),
    credentials: Dict = Depends(JWTBearer())
) -> TransactionHistoryResponse:
    """
    Get transaction history for the authenticated user.

    Supports pagination and filtering by chain.
    """
    user_id = credentials.get("sub")

    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )

        # Build query
        query = supabase.table("transactions").select("*").eq("user_id", user_id)

        if chain:
            query = query.eq("chain", chain)

        # Get total count
        count_result = query.execute()
        total = len(count_result.data) if count_result.data else 0

        # Get paginated results
        offset = (page - 1) * page_size
        query = supabase.table("transactions").select("*").eq("user_id", user_id)
        if chain:
            query = query.eq("chain", chain)
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

        result = query.execute()
        transactions_data = result.data or []

        # Convert to response models
        transactions = []
        for tx in transactions_data:
            network = NETWORKS.get(tx.get("chain", "base-mainnet"), {})
            amount = Decimal(str(tx.get("amount", 0)))

            transactions.append(TransactionHistoryItem(
                id=tx.get("id", ""),
                type=TransactionType(tx.get("type", "send")),
                amount=amount,
                amount_formatted=format_usd(amount),
                chain=tx.get("chain", ""),
                chain_name=network.get("name", tx.get("chain", "")),
                tx_hash=tx.get("tx_hash"),
                explorer_url=f"{network.get('explorer_url', '')}/tx/{tx.get('tx_hash', '')}" if tx.get("tx_hash") else None,
                counterparty=tx.get("to_address") or tx.get("from_address"),
                counterparty_short=format_address(tx.get("to_address") or tx.get("from_address", "")),
                status=TransactionStatus(tx.get("status", "confirmed")),
                created_at=datetime.fromisoformat(tx.get("created_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                confirmed_at=datetime.fromisoformat(tx.get("confirmed_at").replace("Z", "+00:00")) if tx.get("confirmed_at") else None,
            ))

        return TransactionHistoryResponse(
            transactions=transactions,
            total=total,
            page=page,
            page_size=page_size,
            has_more=offset + len(transactions) < total,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transaction history"
        )


@router.get(
    "/status/{tx_hash}",
    summary="Get transaction status",
    description="Check the status of a specific transaction"
)
async def get_transaction_status(
    tx_hash: str,
    credentials: Dict = Depends(JWTBearer())
) -> Dict[str, Any]:
    """
    Get the status of a specific transaction by hash.
    """
    try:
        from supabase_client import get_supabase_client

        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable"
            )

        # SECURITY: Filter by user_id to prevent IDOR - users can only see their own transactions
        user_id = credentials.get("sub")
        result = supabase.table("transactions").select("*").eq(
            "tx_hash", tx_hash
        ).eq("user_id", user_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        tx = result.data
        network = NETWORKS.get(tx.get("chain", "base-mainnet"), {})

        return {
            "tx_hash": tx_hash,
            "status": tx.get("status", "unknown"),
            "chain": tx.get("chain"),
            "chain_name": network.get("name"),
            "explorer_url": f"{network.get('explorer_url', '')}/tx/{tx_hash}",
            "amount": tx.get("amount"),
            "created_at": tx.get("created_at"),
            "confirmed_at": tx.get("confirmed_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transaction status"
        )
