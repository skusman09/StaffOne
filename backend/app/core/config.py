from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./checkinout.db"
    
    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS (comma-separated string from env, converted to list)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    # Timezone & Working Hours Settings
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"  # Default timezone for new users
    STANDARD_WORKING_HOURS: float = 8.0  # Standard expected work hours per day
    AUTO_CHECKOUT_HOURS: float = 12.0  # Hours after which to auto-checkout
    
    # Geofencing Settings
    GEOFENCING_ENABLED: bool = False  # Toggle for location validation
    GEOFENCING_MODE: str = "flag"  # "block" or "flag" - block rejects, flag allows but marks
    DEFAULT_GEOFENCE_RADIUS_METERS: float = 100.0  # Default radius for office locations
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


