from pydantic_settings import BaseSettings, SettingsConfigDict

import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Database connectivity
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/todo_reminder"

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "todo-reminder"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "dev"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
