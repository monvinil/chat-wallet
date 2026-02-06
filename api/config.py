"""
API Configuration
Environment-based settings for the FastAPI application.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    api_title: str = "USDChat API"
    api_description: str = "AI-powered wallet API for managing USDC, agents, and payments"
    api_version: str = "0.1.0"
    debug: bool = False

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS Settings
    cors_origins: List[str] = [
        "http://localhost:8501",  # Streamlit dev
        "http://localhost:3000",  # React dev
        "https://*.streamlit.app",  # Streamlit Cloud
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # JWT Settings
    # SECURITY: No insecure default - must be set via environment variable
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours
    jwt_refresh_token_expire_days: int = 30

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # Database (Supabase)
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_anon_key: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_key: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")

    # Circle Integration
    circle_api_key: Optional[str] = os.getenv("CIRCLE_API_KEY")
    circle_entity_id: Optional[str] = os.getenv("CIRCLE_ENTITY_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    s = Settings()
    # SECURITY: Validate critical settings at startup
    if not s.jwt_secret_key:
        import secrets as _secrets
        import warnings
        warnings.warn(
            "JWT_SECRET_KEY not set! Generating ephemeral key. "
            "All tokens will be invalidated on restart. "
            "Set JWT_SECRET_KEY in your .env file for production.",
            RuntimeWarning,
            stacklevel=2,
        )
        s.jwt_secret_key = _secrets.token_urlsafe(32)
    return s


# Commonly used settings
settings = get_settings()
