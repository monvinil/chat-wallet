"""
JWT Authentication Middleware
Handles token creation, validation, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from api.config import settings


class TokenPayload(BaseModel):
    """JWT Token payload structure."""
    sub: str  # User ID
    email: Optional[str] = None
    wallet_address: Optional[str] = None
    exp: datetime
    iat: datetime
    type: str = "access"  # "access" or "refresh"


class TokenResponse(BaseModel):
    """Token response structure."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(
    user_id: str,
    email: Optional[str] = None,
    wallet_address: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: The user's unique identifier
        email: Optional user email
        wallet_address: Optional wallet address
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "email": email,
        "wallet_address": wallet_address,
        "exp": expire,
        "iat": now,
        "type": "access"
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: The user's unique identifier

    Returns:
        Encoded JWT refresh token string
    """
    now = datetime.utcnow()
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "type": "refresh"
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_tokens(
    user_id: str,
    email: Optional[str] = None,
    wallet_address: Optional[str] = None
) -> TokenResponse:
    """
    Create both access and refresh tokens.

    Args:
        user_id: The user's unique identifier
        email: Optional user email
        wallet_address: Optional wallet address

    Returns:
        TokenResponse with both tokens
    """
    access_token = create_access_token(user_id, email, wallet_address)
    refresh_token = create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}."
            )

        # Verify expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


class JWTBearer(HTTPBearer):
    """
    JWT Bearer authentication dependency.
    Use as a dependency in route handlers to require authentication.

    Example:
        @router.get("/protected")
        async def protected_route(credentials: dict = Depends(JWTBearer())):
            user_id = credentials["sub"]
            ...
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Dict[str, Any]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )

        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )

        # Verify and return token payload
        return verify_token(credentials.credentials)


# Convenience dependency instances
jwt_bearer = JWTBearer()
jwt_bearer_optional = JWTBearer(auto_error=False)


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user from Authorization header if present.
    Returns None if no valid token is provided (doesn't raise error).

    Use this for endpoints that work both authenticated and unauthenticated.

    Example:
        @router.get("/resource")
        async def get_resource(user: Optional[dict] = Depends(get_current_user)):
            if user:
                # Authenticated user
                user_id = user["user_id"]
            else:
                # Anonymous user
                pass
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None

        payload = verify_token(token)
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "wallet_address": payload.get("wallet_address"),
        }
    except (ValueError, HTTPException):
        return None
