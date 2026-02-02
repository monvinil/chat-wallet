"""
Wallet API Routes
Endpoints for wallet management, balances, and authentication.
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
import secrets
import base64
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas.wallet import (
    WalletBalance,
    WalletBalances,
    WalletAddress,
    WalletCreateRequest,
    WalletCreateResponse,
    WalletImportRequest,
    WalletLoginRequest,
    WalletLoginResponse,
)
from api.schemas.common import APIResponse, ErrorResponse
from api.middleware.auth import JWTBearer, create_tokens, verify_token
from api.config import settings

from config import NETWORKS
from chain_utils import ChainUtils
from wallet_manager import WalletManager
from supabase_client import (
    get_user_by_email,
    create_user,
    save_wallet_address,
    get_encrypted_wallet,
    get_user_login_data,
)
from utils.logger import logger


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def format_address(address: str) -> str:
    """Format address for display (first 6, last 4)."""
    if len(address) > 12:
        return f"{address[:6]}...{address[-4:]}"
    return address


def format_usd(amount: Decimal) -> str:
    """Format amount as USD string."""
    return f"${amount:.2f}"


# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================


@router.post(
    "/create",
    response_model=WalletCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new wallet",
    description="Create a new multi-chain wallet with email/password authentication"
)
@limiter.limit("5/minute")
async def create_wallet(request: Request, data: WalletCreateRequest) -> WalletCreateResponse:
    """
    Create a new wallet.

    - Generates 24-word mnemonic
    - Derives EVM and Solana addresses
    - Encrypts wallet with password
    - Creates user account
    - Returns JWT tokens

    **Important:** Save the mnemonic phrase! It's shown only once.
    """
    # Check if user already exists
    existing_user = get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists. Please login instead."
        )

    # Create new wallet
    wallet_info = WalletManager.create_new_wallet()
    if not wallet_info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create wallet"
        )

    # Hash password for storage (separate from encryption)
    password_hash = WalletManager.hash_password(data.password)

    # Create user in database
    try:
        user = create_user(
            email=data.email,
            primary_wallet_address=wallet_info["address"],
            password_hash=password_hash
        )
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )

    # Encrypt wallet data
    encrypted = WalletManager.encrypt_wallet_data(wallet_info["wallet_data"], data.password)

    # Save encrypted wallet to database
    save_wallet_address(
        user["id"],
        wallet_info["address"],
        encrypted_wallet_data=encrypted["encrypted_data"],
        encryption_salt=encrypted["salt"]
    )

    # Save Solana address if available
    solana_address = wallet_info.get("solana_address")
    if solana_address:
        save_wallet_address(user["id"], solana_address, chain="solana")

    # Generate JWT tokens
    tokens = create_tokens(
        user_id=user["id"],
        email=data.email,
        wallet_address=wallet_info["address"]
    )

    logger.info(f"New wallet created for {data.email}")

    return WalletCreateResponse(
        user_id=user["id"],
        evm_address=wallet_info["address"],
        solana_address=solana_address,
        mnemonic=wallet_info["mnemonic"],
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )


@router.post(
    "/login",
    response_model=WalletLoginResponse,
    summary="Login to existing wallet",
    description="Authenticate with email and password"
)
@limiter.limit("10/minute")
async def login(request: Request, data: WalletLoginRequest) -> WalletLoginResponse:
    """
    Login to existing wallet.

    - Verifies email and password
    - Returns JWT tokens
    - Wallet remains locked (encrypted) until unlocked with password
    """
    # Get user data (batched query)
    login_data = get_user_login_data(data.email)

    if not login_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user = login_data.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    stored_hash = user.get("password_hash")
    if not stored_hash or not WalletManager.verify_password(data.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Get wallet address
    wallet = login_data.get("wallet")
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No wallet found for this account"
        )

    # Get Solana address if available
    solana_address = login_data.get("solana_address")

    # Generate JWT tokens
    tokens = create_tokens(
        user_id=user["id"],
        email=data.email,
        wallet_address=wallet["wallet_address"]
    )

    logger.info(f"User logged in: {data.email}")

    return WalletLoginResponse(
        user_id=user["id"],
        email=data.email,
        evm_address=wallet["wallet_address"],
        solana_address=solana_address,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        wallet_locked=True,  # Need password to unlock
    )


@router.post(
    "/import",
    response_model=WalletCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import existing wallet",
    description="Import wallet from mnemonic or private key"
)
@limiter.limit("5/minute")
async def import_wallet(request: Request, data: WalletImportRequest) -> WalletCreateResponse:
    """
    Import an existing wallet.

    - Accepts 12 or 24 word mnemonic, or EVM private key
    - Derives addresses
    - Creates account with encryption
    - Returns JWT tokens
    """
    # Check if user already exists
    existing_user = get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists. Please login instead."
        )

    # Import wallet
    wallet_info = WalletManager.import_wallet(data.recovery_phrase)
    if not wallet_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recovery phrase or private key"
        )

    # Hash password
    password_hash = WalletManager.hash_password(data.password)

    # Create user
    try:
        user = create_user(
            email=data.email,
            primary_wallet_address=wallet_info["address"],
            password_hash=password_hash
        )
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )

    # Encrypt and save
    encrypted = WalletManager.encrypt_wallet_data(wallet_info["wallet_data"], data.password)
    save_wallet_address(
        user["id"],
        wallet_info["address"],
        encrypted_wallet_data=encrypted["encrypted_data"],
        encryption_salt=encrypted["salt"]
    )

    solana_address = wallet_info.get("solana_address")
    if solana_address:
        save_wallet_address(user["id"], solana_address, chain="solana")

    # Generate tokens
    tokens = create_tokens(
        user_id=user["id"],
        email=data.email,
        wallet_address=wallet_info["address"]
    )

    logger.info(f"Wallet imported for {data.email}")

    # Return empty mnemonic if imported from private key
    mnemonic = ""
    if wallet_info.get("type") == "multi-chain":
        # Don't return mnemonic for imported wallets (user already has it)
        mnemonic = "[Already provided - not stored]"

    return WalletCreateResponse(
        user_id=user["id"],
        evm_address=wallet_info["address"],
        solana_address=solana_address,
        mnemonic=mnemonic,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        message="Wallet imported successfully!"
    )


# ============================================================================
# AUTHENTICATED ENDPOINTS
# ============================================================================


@router.get(
    "/balance",
    response_model=APIResponse[WalletBalances],
    summary="Get wallet balances",
    description="Get USDC and native token balances across all chains"
)
async def get_balances(credentials: Dict = Depends(JWTBearer())) -> APIResponse[WalletBalances]:
    """
    Get wallet balances across all chains.

    Returns USDC and native token balances for:
    - Base
    - Arbitrum
    - Ethereum
    - Solana (if wallet supports it)
    """
    wallet_address = credentials.get("wallet_address")
    if not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet address in token"
        )

    # Get Solana address from database
    user_id = credentials.get("sub")
    solana_address = None

    try:
        # Try to get Solana address from user's wallets
        from supabase_client import get_user_wallets
        wallets = get_user_wallets(user_id)
        for w in wallets or []:
            if w.get("chain") == "solana":
                solana_address = w.get("wallet_address")
                break
    except Exception:
        pass

    # Fetch balances from chains
    try:
        balances = ChainUtils.get_all_balances(wallet_address, solana_address)
        total_usdc = ChainUtils.calculate_total_usdc(balances)
    except Exception as e:
        logger.error(f"Failed to fetch balances: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to fetch balances from blockchain"
        )

    # Build response
    chain_balances = []
    for chain_key, chain_data in balances.items():
        network = NETWORKS.get(chain_key, {})
        usdc = Decimal(str(chain_data.get("usdc", 0)))
        native = Decimal(str(chain_data.get("eth", chain_data.get("sol", 0))))

        chain_balances.append(WalletBalance(
            chain=chain_key,
            chain_name=network.get("name", chain_key),
            usdc_balance=usdc,
            usdc_balance_formatted=format_usd(usdc),
            native_balance=native,
            native_symbol=network.get("native_symbol", "ETH"),
        ))

    response_data = WalletBalances(
        total_usdc=Decimal(str(total_usdc)),
        total_usdc_formatted=format_usd(Decimal(str(total_usdc))),
        evm_address=wallet_address,
        solana_address=solana_address,
        balances=chain_balances,
    )

    return APIResponse(data=response_data)


@router.get(
    "/address/{chain}",
    response_model=APIResponse[WalletAddress],
    summary="Get deposit address",
    description="Get deposit address for a specific chain"
)
async def get_deposit_address(
    chain: str = "base-mainnet",
    credentials: Dict = Depends(JWTBearer())
) -> APIResponse[WalletAddress]:
    """
    Get deposit address for receiving funds.

    Optionally generates a QR code for easy mobile deposits.
    """
    wallet_address = credentials.get("wallet_address")
    if not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet address in token"
        )

    network = NETWORKS.get(chain)
    if not network:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported chain: {chain}"
        )

    # For Solana, get the Solana address
    address = wallet_address
    if chain == "solana-mainnet":
        user_id = credentials.get("sub")
        try:
            from supabase_client import get_user_wallets
            wallets = get_user_wallets(user_id)
            for w in wallets or []:
                if w.get("chain") == "solana":
                    address = w.get("wallet_address")
                    break
        except Exception:
            pass

        if address == wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Solana address found for this wallet"
            )

    # Generate QR code
    qr_code = None
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code = base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        logger.warning(f"Failed to generate QR code: {e}")

    response_data = WalletAddress(
        chain=chain,
        chain_name=network["name"],
        address=address,
        address_short=format_address(address),
        explorer_url=ChainUtils.get_explorer_url(chain, address),
        usdc_contract=network.get("usdc_address"),
        qr_code=qr_code,
    )

    return APIResponse(data=response_data)


@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Get a new access token using refresh token"
)
@limiter.limit("20/minute")
async def refresh_token(request: Request, refresh_token: str) -> Dict[str, Any]:
    """
    Refresh the access token.

    Use the refresh token to get a new access token without re-authenticating.
    """
    try:
        payload = verify_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Generate new tokens
        tokens = create_tokens(user_id=user_id)

        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": "bearer",
            "expires_in": tokens.expires_in
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
