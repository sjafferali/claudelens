"""Security utilities."""

from app.core.config import settings


def verify_api_key(api_key: str) -> bool:
    """Verify API key."""
    # Simple comparison for now
    # In production, this should check against database
    return api_key == settings.API_KEY
