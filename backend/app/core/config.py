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

    # AI Configuration
    CLAUDELENS_OPENAI_API_KEY: str = ""
    CLAUDELENS_ENCRYPTION_KEY: str = ""
    AI_RATE_LIMIT_PER_MINUTE: int = 10
    AI_DEFAULT_MODEL: str = "gpt-4"
    AI_MAX_TOKENS: int = 2000
    AI_DEFAULT_TEMPERATURE: float = 0.7

    # Import/Export Rate Limits
    EXPORT_RATE_LIMIT_PER_HOUR: int = 10
    IMPORT_RATE_LIMIT_PER_HOUR: int = 5
    RATE_LIMIT_WINDOW_HOURS: int = 1

    # Backup/Restore Rate Limits
    BACKUP_RATE_LIMIT_PER_HOUR: int = 10
    RESTORE_RATE_LIMIT_PER_HOUR: int = 5

    # Backup storage settings
    BACKUP_STORAGE_PATH: str = "/var/claudelens/backups"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_MAX_SIZE_GB: int = 100

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
