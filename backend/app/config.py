from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Database connectivity
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/todo_reminder"

    # API Configuration
    PROJECT_NAME: str = "todo-reminder"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "dev"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
