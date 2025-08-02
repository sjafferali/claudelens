"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "ClaudeLens"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Database
    MONGODB_URL: str = "mongodb://claudelens_app:claudelens_password@localhost:27017/claudelens?authSource=claudelens"
    DATABASE_NAME: str = "claudelens"
    MAX_CONNECTIONS_COUNT: int = 10
    MIN_CONNECTIONS_COUNT: int = 10
    
    # API
    API_V1_STR: str = "/api/v1"
    API_KEY: str = "default-api-key"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()