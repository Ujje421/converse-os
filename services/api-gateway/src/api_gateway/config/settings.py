from typing import Any
from converse_shared.config.settings import AppSettings
from pydantic_settings import SettingsConfigDict


class GatewaySettings(AppSettings):
    """API Gateway specific settings."""
    
    service_name: str = "api-gateway"
    
    # Redis for Gateway-level Rate Limiting
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis_secret_change_me"
    redis_db: int = 5
    
    # JWT Public Key for validation
    jwt_algorithm: str = "RS256"
    jwt_public_key_path: str = "./keys/jwt-public.pem"
    
    # Microservice backend URLs
    auth_service_url: str = "http://localhost:8001"
    user_service_url: str = "http://localhost:8002"
    org_service_url: str = "http://localhost:8003"
    agent_service_url: str = "http://localhost:8004"
    audit_service_url: str = "http://localhost:8005"
    
    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = GatewaySettings()
