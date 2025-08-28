"""
Migration script to transition from redundant ownership to hierarchical ownership model.

This migration:
1. Ensures all projects have user_id set
2. Removes user_id from sessions collection
3. Removes user_id from messages collection
"""

import asyncio
import logging
from typing import Dict

from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HierarchicalOwnershipMigration:
    def __init__(self, mongodb_url: str, database_name: str):
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client[database_name]

    async def analyze_current_state(self) -> Dict:
        """Analyze the current state of ownership fields."""
        stats = {
            "projects_with_user_id": 0,
            "projects_without_user_id": 0,
            "sessions_with_user_id": 0,
            "sessions_without_user_id": 0,
            "messages_with_user_id": 0,
            "messages_without_user_id": 0,
            "orphaned_sessions": 0,
            "orphaned_messages": 0,
        }

        # Check projects
        stats["projects_with_user_id"] = await self.db.projects.count_documents(
            {"user_id": {"$exists": True, "$ne": None}}
        )
        stats["projects_without_user_id"] = await self.db.projects.count_documents(
            {"$or": [{"user_id": {"$exists": False}}, {"user_id": None}]}
        )

        # Check sessions
        stats["sessions_with_user_id"] = await self.db.sessions.count_documents(
            {"user_id": {"$exists": True}}
        )
        stats["sessions_without_user_id"] = await self.db.sessions.count_documents(
            {"user_id": {"$exists": False}}
        )

        # Check messages
        stats["messages_with_user_id"] = await self.db.messages.count_documents(
            {"user_id": {"$exists": True}}
        )
        stats["messages_without_user_id"] = await self.db.messages.count_documents(
            {"user_id": {"$exists": False}}
        )

        # Check for orphaned sessions (sessions without valid project)
        sessions = await self.db.sessions.find({}, {"projectId": 1}).to_list(None)
        for session in sessions:
            project = await self.db.projects.find_one({"_id": session.get("projectId")})
            if not project:
                stats["orphaned_sessions"] += 1

        # Check for orphaned messages (messages without valid session)
        # Sample check (not full scan for performance)
        sample_messages = await self.db.messages.find({}).limit(100).to_list(100)
        orphaned_count = 0
        for msg in sample_messages:
            session = await self.db.sessions.find_one(
                {"sessionId": msg.get("sessionId")}
            )
            if not session:
                orphaned_count += 1
        if sample_messages:
            # Extrapolate
            total_messages = await self.db.messages.count_documents({})
            stats["orphaned_messages"] = int(
                (orphaned_count / len(sample_messages)) * total_messages
            )

        return stats

    async def ensure_project_ownership(self) -> int:
        """Ensure all projects have user_id set."""
        projects_fixed = 0

        # Find projects without user_id
        projects_without_user = await self.db.projects.find(
            {"$or": [{"user_id": {"$exists": False}}, {"user_id": None}]}
        ).to_list(None)

        if projects_without_user:
            logger.warning(
                f"Found {len(projects_without_user)} projects without user_id"
            )

            # Get default admin user
            admin_user = await self.db.users.find_one({"role": "admin"})
            if not admin_user:
                # Fall back to first user
                admin_user = await self.db.users.find_one({})

            if not admin_user:
                raise Exception("No users found! Cannot assign orphaned projects.")

            # Assign all orphaned projects to admin
            for project in projects_without_user:
                result = await self.db.projects.update_one(
                    {"_id": project["_id"]}, {"$set": {"user_id": admin_user["_id"]}}
                )
                if result.modified_count > 0:
                    projects_fixed += 1
                    logger.info(
                        f"Assigned project {project['_id']} to user {admin_user['username']}"
                    )

        return projects_fixed

    async def remove_redundant_user_ids(self, dry_run: bool = True) -> Dict:
        """Remove user_id fields from sessions and messages."""
        stats = {"sessions_updated": 0, "messages_updated": 0}

        if dry_run:
            # Count how many documents would be updated
            stats["sessions_updated"] = await self.db.sessions.count_documents(
                {"user_id": {"$exists": True}}
            )
            stats["messages_updated"] = await self.db.messages.count_documents(
                {"user_id": {"$exists": True}}
            )
            logger.info(
                f"DRY RUN: Would remove user_id from {stats['sessions_updated']} sessions"
            )
            logger.info(
                f"DRY RUN: Would remove user_id from {stats['messages_updated']} messages"
            )
        else:
            # Actually remove the fields
            # Remove user_id from sessions
            result = await self.db.sessions.update_many(
                {"user_id": {"$exists": True}}, {"$unset": {"user_id": ""}}
            )
            stats["sessions_updated"] = result.modified_count
            logger.info(f"Removed user_id from {stats['sessions_updated']} sessions")

            # Remove user_id from messages
            result = await self.db.messages.update_many(
                {"user_id": {"$exists": True}}, {"$unset": {"user_id": ""}}
            )
            stats["messages_updated"] = result.modified_count
            logger.info(f"Removed user_id from {stats['messages_updated']} messages")

        return stats

    async def execute_migration(self, dry_run: bool = True):
        """Execute the full migration."""
        logger.info(f"Starting hierarchical ownership migration (dry_run={dry_run})")

        # Analyze current state
        initial_stats = await self.analyze_current_state()
        logger.info(f"Initial state: {initial_stats}")

        # Step 1: Ensure all projects have user_id
        if not dry_run:
            projects_fixed = await self.ensure_project_ownership()
            logger.info(f"Fixed {projects_fixed} projects without user_id")
        else:
            logger.info(
                f"DRY RUN: Would fix {initial_stats['projects_without_user_id']} projects"
            )

        # Step 2: Remove redundant user_id fields
        await self.remove_redundant_user_ids(dry_run)

        # Final verification
        if not dry_run:
            final_stats = await self.analyze_current_state()
            logger.info(f"Migration complete. Final state: {final_stats}")

            # Verify success
            if final_stats["projects_without_user_id"] > 0:
                logger.warning("Some projects still lack user_id!")
            if final_stats["sessions_with_user_id"] > 0:
                logger.warning("Some sessions still have user_id!")
            if final_stats["messages_with_user_id"] > 0:
                logger.warning("Some messages still have user_id!")

            if (
                final_stats["projects_without_user_id"] == 0
                and final_stats["sessions_with_user_id"] == 0
                and final_stats["messages_with_user_id"] == 0
            ):
                logger.info(
                    "✅ Migration successful! Hierarchical ownership model is now in place."
                )
        else:
            logger.info("DRY RUN complete. Run with dry_run=False to apply changes.")


async def main():
    # Configuration - using your remote MongoDB
    MONGODB_URL = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    DATABASE_NAME = "claudelens"
    DRY_RUN = False  # Execute the migration

    migration = HierarchicalOwnershipMigration(MONGODB_URL, DATABASE_NAME)
    await migration.execute_migration(dry_run=DRY_RUN)


if __name__ == "__main__":
    asyncio.run(main())
