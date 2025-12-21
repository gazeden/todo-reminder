from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Frontend application settings.
    """

    # API configuration
    API_BASE_URL: str = "http://localhost:8000/api/v1"

    # App configuration
    APP_TITLE: str = "Todo Reminder"
    APP_ICON: str = "📝"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "dev"
    DEBUG: bool = False

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20

    # Session timeout (minutes)
    SESSION_TIMEOUT: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
