"""
Application configuration — uses Pydantic Settings for type-safe env var handling.

Production safety:
- Validates SECRET_KEY is not the default
- Validates CORS_ORIGINS is not '*'
- Validates REDIS_URL is configured
- All secrets come from environment variables (.env)
"""
import logging
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional, List

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./staffone.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "*"

    # Timezone & Working Hours
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"
    STANDARD_WORKING_HOURS: float = 8.0
    AUTO_CHECKOUT_HOURS: float = 12.0

    # Geofencing
    GEOFENCING_ENABLED: bool = False
    GEOFENCING_MODE: str = "flag"
    DEFAULT_GEOFENCE_RADIUS_METERS: float = 100.0

    # HRMS / Salary
    OFFICE_STANDARD_HOURS: float = 9.0
    OVERTIME_MULTIPLIER: float = 1.5
    DEDUCTION_RATE: float = 1.0
    WEEKEND_DAYS: str = "5,6"

    # SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@staffone.com"
    SMTP_FROM_NAME: str = "StaffOne HRMS"
    SMTP_TLS: bool = True

    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_OTP: str = "3/minute"

    # Redis (REQUIRED in production)
    REDIS_URL: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 10

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def _validate_production_config(self):
        """Enforce security constraints in production mode."""
        if self.is_production:
            if self.SECRET_KEY == "your-secret-key-change-in-production":
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be changed from the default in production!"
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be at least 32 characters in production."
                )
            if self.CORS_ORIGINS.strip() == "*":
                raise ValueError(
                    "CRITICAL: CORS_ORIGINS cannot be '*' in production."
                )
            if not self.REDIS_URL:
                raise ValueError(
                    "CRITICAL: REDIS_URL must be configured in production. "
                    "Redis is required for rate limiting, caching, and background jobs."
                )
        else:
            if self.SECRET_KEY == "your-secret-key-change-in-production":
                logger.warning("⚠️  SECRET_KEY is default — OK for development.")
            if self.CORS_ORIGINS.strip() == "*":
                logger.warning("⚠️  CORS_ORIGINS is '*' — set explicit domains before production.")
            if not self.REDIS_URL:
                logger.warning("⚠️  REDIS_URL not set — using in-memory fallbacks (not safe for production).")
        return self

    @property
    def weekend_days_list(self) -> list[int]:
        return [int(d.strip()) for d in self.WEEKEND_DAYS.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
