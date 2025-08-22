"""Service for managing rate limit settings."""

from datetime import UTC, datetime, timedelta
from typing import Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import get_logger
from app.models.rate_limit_settings import RateLimitSettings

logger = get_logger(__name__)


class RateLimitService:
    """Service for managing rate limit settings."""

    SETTINGS_KEY = "rate_limits"

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize the rate limit service."""
        self.db = db
        self._cached_settings: Optional[RateLimitSettings] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 60  # Cache for 1 minute

    async def get_settings(self) -> RateLimitSettings:
        """Get current rate limit settings, using cache if available."""
        # Check cache
        if self._cached_settings and self._cache_timestamp:
            if (
                datetime.utcnow() - self._cache_timestamp
            ).total_seconds() < self._cache_ttl_seconds:
                return self._cached_settings

        # Get from database
        doc = await self.db.settings.find_one({"key": self.SETTINGS_KEY})

        if doc:
            settings_data = doc.get("value", {})
            self._cached_settings = RateLimitSettings(**settings_data)
        else:
            # Use defaults from config
            self._cached_settings = RateLimitSettings(
                export_limit_per_hour=settings.EXPORT_RATE_LIMIT_PER_HOUR,
                import_limit_per_hour=settings.IMPORT_RATE_LIMIT_PER_HOUR,
                backup_limit_per_hour=settings.BACKUP_RATE_LIMIT_PER_HOUR,
                restore_limit_per_hour=settings.RESTORE_RATE_LIMIT_PER_HOUR,
                max_backup_size_gb=settings.BACKUP_MAX_SIZE_GB,
                rate_limit_window_hours=settings.RATE_LIMIT_WINDOW_HOURS,
                max_upload_size_mb=100,  # Default 100 MB
                max_export_size_mb=500,  # Default 500 MB
                max_page_size=100,  # Default max 100 items per page
                default_page_size=20,  # Default 20 items per page
                rate_limiting_enabled=True,  # Enabled by default
                updated_by="system",  # System initialization
            )

            # Save defaults to database
            await self._save_settings(self._cached_settings)

        self._cache_timestamp = datetime.utcnow()
        return self._cached_settings

    async def update_settings(
        self, updates: Dict, updated_by: Optional[str] = None
    ) -> RateLimitSettings:
        """Update rate limit settings."""
        current_settings = await self.get_settings()

        # Apply updates
        updated_data = current_settings.dict()
        for key, value in updates.items():
            if value is not None and key in updated_data:
                updated_data[key] = value

        # Update metadata
        updated_data["updated_at"] = datetime.utcnow()
        updated_data["updated_by"] = updated_by

        # Create new settings object
        new_settings = RateLimitSettings(**updated_data)

        # Save to database
        await self._save_settings(new_settings)

        # Update cache
        self._cached_settings = new_settings
        self._cache_timestamp = datetime.utcnow()

        logger.info(f"Rate limit settings updated by {updated_by or 'system'}")

        return new_settings

    async def _save_settings(self, settings: RateLimitSettings) -> None:
        """Save settings to database."""
        await self.db.settings.update_one(
            {"key": self.SETTINGS_KEY},
            {
                "$set": {
                    "key": self.SETTINGS_KEY,
                    "value": settings.dict(),
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    async def check_rate_limit(
        self, user_id: str, limit_type: str
    ) -> tuple[bool, Dict]:
        """Check if user has exceeded rate limit.

        Returns:
            Tuple of (allowed, info) where allowed is True if action is allowed,
            and info contains rate limit details.
        """
        settings = await self.get_settings()

        # Check if rate limiting is enabled
        if not settings.rate_limiting_enabled:
            return True, {"enabled": False, "message": "Rate limiting is disabled"}

        # Get the appropriate limit
        limit_map = {
            "export": settings.export_limit_per_hour,
            "import": settings.import_limit_per_hour,
            "backup": settings.backup_limit_per_hour,
            "restore": settings.restore_limit_per_hour,
        }

        limit = limit_map.get(limit_type)
        if limit is None:
            return True, {"error": f"Unknown limit type: {limit_type}"}

        # If limit is 0, it means unlimited
        if limit == 0:
            return True, {"limit": "unlimited", "message": "No rate limit applied"}

        # Check usage in the time window
        now = datetime.now(UTC)
        window_start = now - timedelta(hours=settings.rate_limit_window_hours)

        # Count recent actions
        collection_name = f"{limit_type}_rate_tracking"
        count = await self.db[collection_name].count_documents(
            {"user_id": user_id, "timestamp": {"$gte": window_start}}
        )

        if count >= limit:
            # Calculate when the oldest action will expire
            oldest = await self.db[collection_name].find_one(
                {"user_id": user_id, "timestamp": {"$gte": window_start}},
                sort=[("timestamp", 1)],
            )

            reset_time = None
            if oldest:
                reset_time = oldest["timestamp"] + timedelta(
                    hours=settings.rate_limit_window_hours
                )
                reset_in_seconds = (reset_time - now).total_seconds()
            else:
                reset_in_seconds = 0

            return False, {
                "limit": limit,
                "current": count,
                "remaining": 0,
                "window_hours": settings.rate_limit_window_hours,
                "reset_in_seconds": max(0, reset_in_seconds),
                "message": f"Rate limit exceeded. Maximum {limit} {limit_type}s per {settings.rate_limit_window_hours} hour(s).",
            }

        # Record this action
        await self.db[collection_name].insert_one(
            {"user_id": user_id, "timestamp": now, "action": limit_type}
        )

        # Clean up old entries (older than window)
        await self.db[collection_name].delete_many({"timestamp": {"$lt": window_start}})

        return True, {
            "limit": limit,
            "current": count + 1,
            "remaining": limit - count - 1,
            "window_hours": settings.rate_limit_window_hours,
            "message": "Action allowed",
        }

    async def get_usage_stats(self, user_id: str) -> Dict:
        """Get current usage statistics for all rate limits."""
        settings = await self.get_settings()
        now = datetime.now(UTC)
        window_start = now - timedelta(hours=settings.rate_limit_window_hours)

        stats = {}

        for limit_type in ["export", "import", "backup", "restore"]:
            collection_name = f"{limit_type}_rate_tracking"
            count = await self.db[collection_name].count_documents(
                {"user_id": user_id, "timestamp": {"$gte": window_start}}
            )

            limit = getattr(settings, f"{limit_type}_limit_per_hour", 0)

            # Find when the oldest action will expire for reset time
            oldest = await self.db[collection_name].find_one(
                {"user_id": user_id, "timestamp": {"$gte": window_start}},
                sort=[("timestamp", 1)],
            )

            reset_in_seconds = None
            if oldest and limit > 0 and count >= limit:
                reset_time = oldest["timestamp"] + timedelta(
                    hours=settings.rate_limit_window_hours
                )
                reset_in_seconds = max(0, (reset_time - now).total_seconds())

            stats[limit_type] = {
                "current": count,
                "limit": limit if limit > 0 else "unlimited",
                "remaining": max(0, limit - count) if limit > 0 else "unlimited",
                "reset_in_seconds": reset_in_seconds,
            }

        return stats

    async def reset_user_limits(
        self, user_id: str, limit_type: Optional[str] = None
    ) -> None:
        """Reset rate limits for a user."""
        if limit_type:
            # Reset specific limit type
            collection_name = f"{limit_type}_rate_tracking"
            await self.db[collection_name].delete_many({"user_id": user_id})
            logger.info(f"Reset {limit_type} rate limits for user {user_id}")
        else:
            # Reset all limits
            for lt in ["export", "import", "backup", "restore"]:
                collection_name = f"{lt}_rate_tracking"
                await self.db[collection_name].delete_many({"user_id": user_id})
            logger.info(f"Reset all rate limits for user {user_id}")
