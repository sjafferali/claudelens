#!/usr/bin/env python3
"""Script to clean up orphaned data in the database.

This should be run periodically (e.g., via cron) to ensure database consistency.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.services.project_deletion import ProjectDeletionService  # noqa: E402


async def main():
    """Run the cleanup process."""
    print("=" * 60)
    print("CLAUDELENS DATABASE CLEANUP")
    print("=" * 60)

    # Connect to database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    try:
        # Initialize deletion service
        deletion_service = ProjectDeletionService(db)

        print("\nScanning for orphaned data...")

        # Run cleanup
        stats = await deletion_service.cleanup_all_orphaned_data()

        print("\nCleanup Results:")
        print(f"  Orphaned sessions deleted: {stats['orphaned_sessions']}")
        print(f"  Orphaned messages deleted: {stats['orphaned_messages']}")
        print(f"  Incomplete deletions resumed: {stats['incomplete_deletions']}")

        if any(stats.values()):
            print("\n✅ Database cleaned successfully!")
        else:
            print("\n✅ No orphaned data found - database is clean!")

    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        return 1
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
