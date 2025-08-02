"""Security utilities."""
import secrets

from app.core.config import settings


def verify_api_key(api_key: str) -> bool:
    """Verify API key."""
    # Simple comparison for now
    # In production, this should check against database
    return api_key == settings.API_KEY


def generate_api_key() -> str:
    """Generate a new API key."""
    return secrets.token_urlsafe(32)
