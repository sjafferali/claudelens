"""Application configuration."""

from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "ClaudeLens"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    MONGODB_URL: str = "mongodb://claudelens_app:claudelens_password@localhost:27017/claudelens?authSource=claudelens"
    DATABASE_NAME: str = "claudelens"
    MAX_CONNECTIONS_COUNT: int = 100
    MIN_CONNECTIONS_COUNT: int = 10

    # API
    API_V1_STR: str = "/api/v1"
    API_KEY: str = "default-api-key"

    # CORS
    BACKEND_CORS_ORIGINS: ClassVar[list[str]] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
