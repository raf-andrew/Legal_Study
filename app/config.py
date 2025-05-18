"""
Configuration settings for the application.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # Database settings
    DATABASE_URL: str = "sqlite:///./legal_study.db"

    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Legal Study"

    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["*"]

    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"

settings = Settings()
