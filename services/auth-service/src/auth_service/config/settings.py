from typing import Any
from converse_shared.config.settings import AppSettings
from pydantic_settings import SettingsConfigDict


class AuthSettings(AppSettings):
    """Auth service specific settings."""
    
    service_name: str = "auth-service"
    
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "converse"
    postgres_password: str = "converse_secret_change_me"
    auth_db_name: str = "converse_auth"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis_secret_change_me"
    redis_db: int = 0
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # JWT
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30
    jwt_private_key_path: str = "./keys/jwt-private.pem"
    jwt_public_key_path: str = "./keys/jwt-public.pem"
    
    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.auth_db_name}"

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = AuthSettings()
