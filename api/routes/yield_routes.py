"""
Yield API Routes
Endpoints for Aave yield management.
"""

import os
import sys
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas.yield_schemas import (
    YieldStatusResponse,
    YieldDepositRequest,
    YieldWithdrawRequest,
    YieldTransactionResponse,
)
from api.schemas.common import APIResponse
from api.middleware.auth import JWTBearer
from aave_client import AaveClient, get_yield_summary
from wallet_manager import WalletManager
from supabase_client import get_encrypted_wallet
from utils.logger import logger


router = APIRouter()


def format_usd(amount: float) -> str:
    """Format amount as USD string"""
    return f"${amount:,.2f}"


@router.get(
    "/status",
    response_model=APIResponse[YieldStatusResponse],
    summary="Get yield status",
    description="Get current yield earning status including APY and projected earnings"
)
async def get_yield_status(
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[YieldStatusResponse]:
    """Get yield status for the authenticated user"""
    wallet_address = credentials.get("wallet_address")
    if not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet address in token"
        )

    try:
        # Get yield summary across networks
        summary = get_yield_summary(wallet_address)

        total_deposited = summary.get("total_deposited", 0)
        avg_apy = summary.get("average_apy", 0)

        # Calculate projections
        projected_daily = total_deposited * (avg_apy / 100) / 365
        projected_monthly = total_deposited * (avg_apy / 100) / 12
        projected_yearly = total_deposited * (avg_apy / 100)

        # Estimate earned (simplified - in production, track actual deposits)
        # For now, estimate based on deposited amount and 30-day average
        estimated_earned = projected_monthly  # Placeholder

        response_data = YieldStatusResponse(
            enabled=total_deposited > 0,
            protocol="Aave V3",
            apy=avg_apy,
            deposited_amount=total_deposited,
            deposited_amount_formatted=format_usd(total_deposited),
            earned_amount=estimated_earned,
            earned_amount_formatted=format_usd(estimated_earned),
            projected_daily=round(projected_daily, 4),
            projected_monthly=round(projected_monthly, 2),
            projected_yearly=round(projected_yearly, 2),
            positions=summary.get("positions", [])
        )

        return APIResponse(data=response_data)

    except Exception as e:
        logger.error(f"Failed to get yield status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch yield status"
        )


@router.post(
    "/deposit",
    response_model=APIResponse[YieldTransactionResponse],
    summary="Deposit to yield",
    description="Deposit USDC into Aave to start earning yield"
)
async def deposit_to_yield(
    request: YieldDepositRequest,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[YieldTransactionResponse]:
    """Deposit USDC into Aave yield"""
    user_id = credentials.get("sub")
    wallet_address = credentials.get("wallet_address")

    if not user_id or not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        # Get encrypted wallet data
        encrypted_wallet = get_encrypted_wallet(user_id)
        if not encrypted_wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found"
            )

        # Decrypt wallet to get private key
        wallet_data = WalletManager.decrypt_wallet_data(
            encrypted_wallet["encrypted_wallet_data"],
            encrypted_wallet["encryption_salt"],
            request.password
        )

        if not wallet_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )

        private_key = wallet_data.get("private_key")
        if not private_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve wallet key"
            )

        # Initialize Aave client
        client = AaveClient(request.chain)

        # Determine amount to deposit
        if request.amount is None:
            # Deposit all available USDC
            amount = client.get_usdc_balance(wallet_address, use_cache=False)
            if amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No USDC available to deposit"
                )
        else:
            amount = request.amount
            # Verify sufficient balance
            balance = client.get_usdc_balance(wallet_address, use_cache=False)
            if balance < amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient USDC balance. Have: ${balance:.2f}, Need: ${amount:.2f}"
                )

        # Execute deposit
        result = client.deposit(private_key, amount)

        if result.get("success"):
            return APIResponse(data=YieldTransactionResponse(
                success=True,
                tx_hash=result.get("tx_hash"),
                amount=amount,
                chain=request.chain
            ))
        else:
            return APIResponse(data=YieldTransactionResponse(
                success=False,
                error=result.get("error", "Deposit failed")
            ))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Yield deposit failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deposit failed: {str(e)}"
        )


@router.post(
    "/withdraw",
    response_model=APIResponse[YieldTransactionResponse],
    summary="Withdraw from yield",
    description="Withdraw USDC from Aave yield"
)
async def withdraw_from_yield(
    request: YieldWithdrawRequest,
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[YieldTransactionResponse]:
    """Withdraw USDC from Aave yield"""
    user_id = credentials.get("sub")
    wallet_address = credentials.get("wallet_address")

    if not user_id or not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

    try:
        # Get encrypted wallet data
        encrypted_wallet = get_encrypted_wallet(user_id)
        if not encrypted_wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found"
            )

        # Decrypt wallet to get private key
        wallet_data = WalletManager.decrypt_wallet_data(
            encrypted_wallet["encrypted_wallet_data"],
            encrypted_wallet["encryption_salt"],
            request.password
        )

        if not wallet_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )

        private_key = wallet_data.get("private_key")
        if not private_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve wallet key"
            )

        # Initialize Aave client
        client = AaveClient(request.chain)

        # Verify there's something to withdraw
        deposited = client.get_ausdc_balance(wallet_address, use_cache=False)
        if deposited <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No funds deposited in yield"
            )

        # Determine amount (-1 means withdraw all)
        amount = request.amount if request.amount is not None else -1

        # Execute withdrawal
        result = client.withdraw(private_key, amount)

        if result.get("success"):
            return APIResponse(data=YieldTransactionResponse(
                success=True,
                tx_hash=result.get("tx_hash"),
                amount=deposited if amount == -1 else amount,
                chain=request.chain
            ))
        else:
            return APIResponse(data=YieldTransactionResponse(
                success=False,
                error=result.get("error", "Withdrawal failed")
            ))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Yield withdrawal failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Withdrawal failed: {str(e)}"
        )
