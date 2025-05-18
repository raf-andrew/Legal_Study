"""Configuration module."""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets
from pydantic import validator

class Settings(BaseSettings):
    """Application settings."""

    # Project info
    PROJECT_NAME: str = "Legal Study API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "API for Legal Study platform"

    # API
    API_V1_STR: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # Database
    DATABASE_URL: Optional[str] = None

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS: List[str] = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/public"
    ]

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    CORS_EXPOSE_HEADERS: List[str] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 600

    # Security Headers
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return "sqlite:///./app.db"

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

settings = Settings()
