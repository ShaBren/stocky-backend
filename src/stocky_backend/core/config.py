"""
Core configuration settings for the Stocky Backend application
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application settings
    APP_NAME: str = "Stocky Backend"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PERSISTENT_SESSION_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Cookie settings for persistent sessions
    COOKIE_NAME: str = "stocky_refresh_token"
    COOKIE_SECURE: bool = False  # Set to True in production with HTTPS
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "lax"  # "lax", "strict", or "none"
    COOKIE_DOMAIN: str | None = None  # Set for subdomain sharing

    # Database settings - will be overridden by .env file
    DATABASE_URL: str = "sqlite+pysqlite:///./data/stocky.db"

    # CORS settings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # UDA (Universal Data Application) settings
    UDA_BASE_URL: str | None = None
    UDA_TIMEOUT: int = 5

    # UPC Lookup Service settings
    UPC_SERVICE_BASE_URL: str | None = None
    UPC_SERVICE_TIMEOUT: int = 10

    # Logging settings
    LOG_LEVEL: str = "INFO"
    MAX_LOG_ENTRIES: int = 10000

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-this-in-production":
            print("WARNING: Using default secret key. Change this in production!")
        return v

    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert ALLOWED_ORIGINS string to list for CORS middleware.

        Supports both comma-separated and JSON array formats.
        """
        origins = self.ALLOWED_ORIGINS
        if isinstance(origins, str):
            origins = origins.strip()
            # Detect JSON array format: ["a", "b"]
            if origins.startswith("[") and origins.endswith("]"):
                import json

                try:
                    origins = json.loads(origins)
                except json.JSONDecodeError:
                    pass
            if isinstance(origins, str):
                return [o.strip().strip('"') for o in origins.split(",") if o.strip()]
        return list(origins) if origins else []

    model_config = {"env_file": ".env", "case_sensitive": True}


# Global settings instance
settings = Settings()
