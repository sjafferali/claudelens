"""Background tasks for periodic operations."""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger
from app.services.rate_limit_usage_service import RateLimitUsageService

logger = get_logger(__name__)


class BackgroundTaskManager:
    """Manages background tasks for the application."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize the background task manager."""
        self.db = db
        self.tasks: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        """Start all background tasks."""
        if self._running:
            logger.warning("Background tasks already running")
            return

        self._running = True
        logger.info("Starting background tasks")

        # Start individual tasks
        self.tasks.append(asyncio.create_task(self._rate_limit_cleanup_task()))
        self.tasks.append(asyncio.create_task(self._metrics_flush_task()))

        logger.info(f"Started {len(self.tasks)} background tasks")

    async def stop(self) -> None:
        """Stop all background tasks."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping background tasks")

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        logger.info("Background tasks stopped")

    async def _rate_limit_cleanup_task(self) -> None:
        """Periodically clean up old rate limit usage data."""
        while self._running:
            try:
                # Run cleanup once per day at 3 AM
                now = datetime.now(timezone.utc)
                next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)

                # If it's already past 3 AM, schedule for tomorrow
                if now.hour >= 3:
                    next_run = next_run.replace(day=next_run.day + 1)

                # Calculate wait time
                wait_seconds = (next_run - now).total_seconds()

                logger.info(
                    f"Next rate limit cleanup scheduled in {wait_seconds/3600:.1f} hours"
                )

                # Wait until next run time
                await asyncio.sleep(wait_seconds)

                if not self._running:
                    break

                # Perform cleanup
                logger.info("Starting rate limit usage data cleanup")
                service = RateLimitUsageService(self.db)

                # Clean up data older than 30 days by default
                deleted_count = await service.cleanup_old_data(retention_days=30)

                logger.info(
                    f"Rate limit cleanup completed. Deleted {deleted_count} old records"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limit cleanup task: {e}", exc_info=True)
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)

    async def _metrics_flush_task(self) -> None:
        """Periodically flush in-memory metrics to database."""
        flush_interval = 60  # Flush every 60 seconds

        while self._running:
            try:
                await asyncio.sleep(flush_interval)

                if not self._running:
                    break

                # Flush metrics
                service = RateLimitUsageService(self.db)
                await service._flush_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics flush task: {e}", exc_info=True)
                # Continue running even if flush fails
                await asyncio.sleep(flush_interval)


# Global task manager instance
_task_manager: Optional[BackgroundTaskManager] = None


async def start_background_tasks(db: AsyncIOMotorDatabase) -> None:
    """Start background tasks."""
    global _task_manager

    if _task_manager is None:
        _task_manager = BackgroundTaskManager(db)
        await _task_manager.start()


async def stop_background_tasks() -> None:
    """Stop background tasks."""
    global _task_manager

    if _task_manager is not None:
        await _task_manager.stop()
        _task_manager = None
