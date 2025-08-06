"""Script to fix session costs by recalculating them from messages."""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# ruff: noqa: E402
from bson import Decimal128
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database


async def fix_session_costs(db: AsyncIOMotorDatabase) -> None:
    """Recalculate and update totalCost for all sessions."""

    # Get all sessions
    sessions = await db.sessions.find({}).to_list(None)
    print(f"Found {len(sessions)} sessions to process")

    updated_count = 0

    for session in sessions:
        session_id = session["sessionId"]

        # Calculate total cost from messages
        pipeline = [
            {"$match": {"sessionId": session_id}},
            {
                "$group": {
                    "_id": None,
                    "totalCost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                }
            },
        ]

        result = await db.messages.aggregate(pipeline).to_list(1)

        if result:
            total_cost = result[0]["totalCost"]

            # Handle Decimal128 from MongoDB aggregation
            if hasattr(total_cost, "to_decimal"):
                total_cost = float(str(total_cost))
            else:
                total_cost = float(total_cost) if total_cost is not None else 0.0

            # Update the session with the correct total cost
            update_result = await db.sessions.update_one(
                {"_id": session["_id"]},
                {"$set": {"totalCost": Decimal128(str(total_cost))}},
            )

            if update_result.modified_count > 0:
                updated_count += 1
                print(f"Updated session {session_id}: ${total_cost:.4f}")
        else:
            # No messages found, set cost to 0
            await db.sessions.update_one(
                {"_id": session["_id"]}, {"$set": {"totalCost": Decimal128("0")}}
            )

    print(f"\nCompleted! Updated {updated_count} sessions")


async def main():
    """Main function."""
    print("Connecting to database...")
    db = await get_database()

    print("Fixing session costs...")
    await fix_session_costs(db)


if __name__ == "__main__":
    asyncio.run(main())
