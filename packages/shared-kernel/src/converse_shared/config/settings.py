"""Base settings configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Base application settings.
    
    Services should inherit from this and add their specific configuration.
    It reads from .env file or environment variables.
    """
    
    # General
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Observability
    service_name: str
    service_version: str = "0.1.0"
    otel_exporter_otlp_endpoint: str | None = None
    otel_traces_sampler_arg: float = 1.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
