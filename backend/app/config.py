from typing import Optional
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "todo-reminder"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "dev"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/todo_reminder"
    DB_ECHO: bool = False  # SQL logging

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "PLAINTEXT://localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "todo_reminder"
    KAFKA_ACKS: str = "all"
    KAFKA_ENABLE_IDEMPOTENCE: bool = True

    # Schema Registry
    SCHEMA_REGISTRY_URL: str = "http://localhost:8081"
    SCHEMA_REGISTRY_API_KEY: Optional[str] = None  # For Confluent Cloud
    SCHEMA_REGISTRY_API_SECRET: Optional[str] = None  # For Confluent Cloud
    USE_SCHEMA_REGISTRY: bool = True  # Toggle schema registry usage

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
