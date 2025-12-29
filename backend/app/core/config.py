import os
from pydantic_settings import BaseSettings
import secrets
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./staffone.db"
    
    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS (comma-separated string from env, converted to list)
    CORS_ORIGINS: str = "*"
    
    # Timezone & Working Hours Settings
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"  # Default timezone for new users
    STANDARD_WORKING_HOURS: float = 8.0  # Standard expected work hours per day
    AUTO_CHECKOUT_HOURS: float = 12.0  # Hours after which to auto-checkout
    
    # Geofencing Settings
    GEOFENCING_ENABLED: bool = False  # Toggle for location validation
    GEOFENCING_MODE: str = "flag"  # "block" or "flag" - block rejects, flag allows but marks
    DEFAULT_GEOFENCE_RADIUS_METERS: float = 100.0  # Default radius for office locations
    
    # HRMS / Salary Settings
    OFFICE_STANDARD_HOURS: float = 9.0  # Standard working hours per day (for salary calc)
    OVERTIME_MULTIPLIER: float = 1.5  # Overtime pay multiplier
    DEDUCTION_RATE: float = 1.0  # Undertime deduction rate (1x hourly rate)
    WEEKEND_DAYS: str = "5,6"  # Saturday=5, Sunday=6 (comma-separated)
    
    # SMTP Settings
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@staffone.com")
    SMTP_FROM_NAME: str = "StaffOne HRMS"
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() == "true"
    
    @property
    def weekend_days_list(self) -> list[int]:
        """Convert weekend days string to list of integers."""
        return [int(d.strip()) for d in self.WEEKEND_DAYS.split(",")]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()


