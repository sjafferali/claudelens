"""
Migration script to fix orphaned data without user_id.

Strategy:
1. Find all unique API keys that have been used
2. Map data to users based on creation timestamps and API key usage
3. For unmappable data, assign to a system admin or delete
"""

import asyncio
import logging
from typing import Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrphanedDataMigration:
    def __init__(self, mongodb_url: str, database_name: str):
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[database_name]

    async def analyze_orphaned_data(self) -> Dict:
        """Analyze the scope of orphaned data."""
        stats = {
            "orphaned_projects": 0,
            "orphaned_sessions": 0,
            "orphaned_messages": 0,
            "users_found": 0,
            "api_keys_found": 0,
        }

        # Count orphaned projects
        stats["orphaned_projects"] = await self.db.projects.count_documents(
            {"user_id": {"$exists": False}}
        )

        # Count orphaned sessions
        stats["orphaned_sessions"] = await self.db.sessions.count_documents(
            {"user_id": {"$exists": False}}
        )

        # Count orphaned messages
        stats["orphaned_messages"] = await self.db.messages.count_documents(
            {"user_id": {"$exists": False}}
        )

        # Count users
        stats["users_found"] = await self.db.users.count_documents({})

        # Count API keys
        users_with_keys = await self.db.users.count_documents(
            {"api_keys": {"$exists": True, "$ne": []}}
        )
        stats["api_keys_found"] = users_with_keys

        return stats

    async def realistic_assignment(self) -> tuple[Dict[str, ObjectId], ObjectId]:
        """
        Try to map orphaned data to users based on:
        1. If only one user exists, assign all data to them
        2. If multiple users, use creation timestamps and activity patterns
        3. Fall back to admin user
        """
        mapping = {}

        # Get all users
        users = await self.db.users.find({}).to_list(None)

        if len(users) == 0:
            raise Exception("No users found! Cannot proceed with migration.")

        if len(users) == 1:
            # Simple case: only one user, assign everything to them
            user = users[0]
            logger.info(
                f"Only one user found ({user['username']}), assigning all orphaned data to them"
            )

            # Get all orphaned projects
            orphaned_projects = await self.db.projects.find(
                {"user_id": {"$exists": False}}
            ).to_list(None)

            for project in orphaned_projects:
                mapping[str(project["_id"])] = user["_id"]

            return mapping, user["_id"]

        # Multiple users - need more complex logic
        # For now, find the admin user or the first user
        admin_user = None
        for user in users:
            if user.get("role") == "admin":
                admin_user = user
                break

        if not admin_user:
            admin_user = users[0]  # Fallback to first user

        logger.info(
            f"Multiple users found, assigning orphaned data to {admin_user['username']}"
        )

        # Map all orphaned projects to admin
        orphaned_projects = await self.db.projects.find(
            {"user_id": {"$exists": False}}
        ).to_list(None)

        for project in orphaned_projects:
            mapping[str(project["_id"])] = admin_user["_id"]

        return mapping, admin_user["_id"]

    async def execute_migration(self, dry_run: bool = True):
        """Execute the migration."""
        logger.info(f"Starting migration (dry_run={dry_run})")

        # Analyze current state
        stats = await self.analyze_orphaned_data()
        logger.info(f"Current state: {stats}")

        if (
            stats["orphaned_projects"] == 0
            and stats["orphaned_sessions"] == 0
            and stats["orphaned_messages"] == 0
        ):
            logger.info("No orphaned data found, migration not needed")
            return

        # Get mapping
        project_mapping, default_user_id = await self.realistic_assignment()

        if dry_run:
            logger.info("DRY RUN - No changes will be made")
            logger.info(f"Would assign {len(project_mapping)} projects to users")
            logger.info(f"Default user for unmapped data: {default_user_id}")
            return

        # Update projects
        for project_id_str, user_id in project_mapping.items():
            result = await self.db.projects.update_one(
                {"_id": ObjectId(project_id_str)}, {"$set": {"user_id": user_id}}
            )
            if result.modified_count > 0:
                logger.info(f"Updated project {project_id_str} with user_id {user_id}")

        # Update sessions - match by projectId
        for project_id_str, user_id in project_mapping.items():
            result = await self.db.sessions.update_many(
                {"projectId": ObjectId(project_id_str), "user_id": {"$exists": False}},
                {"$set": {"user_id": user_id}},
            )
            logger.info(
                f"Updated {result.modified_count} sessions for project {project_id_str}"
            )

        # Update orphaned sessions without projects
        result = await self.db.sessions.update_many(
            {"user_id": {"$exists": False}}, {"$set": {"user_id": default_user_id}}
        )
        logger.info(
            f"Updated {result.modified_count} orphaned sessions with default user"
        )

        # Update messages - match by sessionId
        sessions = await self.db.sessions.find(
            {}, {"sessionId": 1, "user_id": 1}
        ).to_list(None)
        session_user_map = {s["sessionId"]: s["user_id"] for s in sessions}

        for session_id, user_id in session_user_map.items():
            result = await self.db.messages.update_many(
                {"sessionId": session_id, "user_id": {"$exists": False}},
                {"$set": {"user_id": user_id}},
            )
            logger.info(
                f"Updated {result.modified_count} messages for session {session_id}"
            )

        # Update any remaining orphaned messages
        result = await self.db.messages.update_many(
            {"user_id": {"$exists": False}}, {"$set": {"user_id": default_user_id}}
        )
        logger.info(f"Updated {result.modified_count} fully orphaned messages")

        # Final verification
        final_stats = await self.analyze_orphaned_data()
        logger.info(f"Migration complete. Final state: {final_stats}")

        if (
            final_stats["orphaned_projects"] > 0
            or final_stats["orphaned_sessions"] > 0
            or final_stats["orphaned_messages"] > 0
        ):
            logger.warning("Some orphaned data still remains!")
        else:
            logger.info("All orphaned data has been assigned to users")


async def main():
    # Configuration
    MONGODB_URL = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    DATABASE_NAME = "claudelens"
    DRY_RUN = False  # Execute the migration

    migration = OrphanedDataMigration(MONGODB_URL, DATABASE_NAME)
    await migration.execute_migration(dry_run=DRY_RUN)


if __name__ == "__main__":
    asyncio.run(main())
