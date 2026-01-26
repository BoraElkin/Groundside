"""
Application configuration management.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow",
        protected_namespaces=()  # Allow fields starting with 'model_'
    )

    # Application
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    backend_cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Database
    database_url: str = "postgresql://groundops:groundops@localhost:5432/groundops"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    flightaware_api_key: str = ""

    # LLM Settings
    llm_provider: str = "anthropic"  # "anthropic" or "openai"
    llm_model: str = "claude-sonnet-4-20250514"  # Anthropic model
    openai_model: str = "gpt-4-turbo-preview"  # OpenAI model

    # Azure Storage
    azure_storage_connection_string: str = ""
    azure_storage_container: str = "ground-ops-data"

    # Email/SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_from_email: str = "alerts@groundops.example.com"

    # Webhooks
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""

    # ML Model Settings
    delay_prediction_threshold: float = 0.7
    confidence_interval: float = 0.95
    model_refresh_interval_hours: int = 24

    # Airport Configuration
    default_airport_code: str = "IST"
    timezone: str = "Europe/Istanbul"

    # External APIs
    aodb_api_url: str = ""
    aodb_api_key: str = ""
    handler_api_url: str = ""
    handler_api_key: str = ""
    gps_tracker_url: str = ""
    gps_tracker_key: str = ""

    # Logging
    log_level: str = "INFO"

    @property
    def async_database_url(self) -> str:
        """Convert sync database URL to async version."""
        return self.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
