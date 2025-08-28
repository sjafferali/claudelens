"""Message service layer."""

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.message import Message, MessageDetail
from app.services.rolling_message_service import RollingMessageService


class MessageService:
    """Service for message operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.rolling_service = RollingMessageService(db)

    async def list_messages(
        self,
        user_id: str,
        filter_dict: dict[str, Any],
        skip: int,
        limit: int,
        sort_order: str,
    ) -> tuple[list[Message], int]:
        """List messages with pagination."""
        # Get user's project IDs first
        user_projects = await self.db.projects.find(
            {"user_id": ObjectId(user_id)}, {"_id": 1}
        ).to_list(None)
        project_ids = [p["_id"] for p in user_projects]

        # Get sessions belonging to user's projects
        user_sessions = await self.db.sessions.find(
            {"projectId": {"$in": project_ids}}, {"sessionId": 1}
        ).to_list(None)
        session_ids = [s["sessionId"] for s in user_sessions]

        # Filter messages by user's sessions
        filter_dict["sessionId"] = {"$in": session_ids}

        # Remove any user_id filter that might have been passed
        filter_dict.pop("user_id", None)

        # Use rolling service for queries
        docs, total = await self.rolling_service.find_messages(
            filter_dict, skip, limit, sort_order
        )

        messages = []
        for doc in docs:
            message_data = {
                "_id": str(doc["_id"]),
                "uuid": doc["uuid"],
                "type": doc["type"],
                "session_id": doc["sessionId"],
                "content": doc.get("content"),
                "timestamp": doc["timestamp"],
                "model": doc.get("model"),
                "parent_uuid": doc.get("parentUuid"),
                "created_at": doc.get("createdAt", doc["timestamp"]),
            }
            messages.append(Message(**message_data))

        return messages, total

    async def get_message(self, user_id: str, message_id: str) -> MessageDetail | None:
        """Get a single message by ID."""
        if not ObjectId.is_valid(message_id):
            return None

        doc = await self.rolling_service.find_one({"_id": ObjectId(message_id)})
        if not doc:
            return None

        # Verify ownership through session -> project chain
        session = await self.db.sessions.find_one({"sessionId": doc["sessionId"]})
        if not session:
            return None

        project = await self.db.projects.find_one(
            {"_id": session["projectId"], "user_id": ObjectId(user_id)}
        )
        if not project:
            return None

        return self._doc_to_message_detail(doc)

    async def get_message_by_uuid(
        self, user_id: str, uuid: str
    ) -> MessageDetail | None:
        """Get a message by its Claude UUID."""
        doc = await self.rolling_service.find_one({"uuid": uuid})
        if not doc:
            return None

        # Verify ownership through session -> project chain
        session = await self.db.sessions.find_one({"sessionId": doc["sessionId"]})
        if not session:
            return None

        project = await self.db.projects.find_one(
            {"_id": session["projectId"], "user_id": ObjectId(user_id)}
        )
        if not project:
            return None

        return self._doc_to_message_detail(doc)

    async def get_message_context(
        self, user_id: str, message_id: str, before: int, after: int
    ) -> dict | None:
        """Get a message with surrounding context."""
        if not ObjectId.is_valid(message_id):
            return None

        # Get the target message
        target = await self.rolling_service.find_one({"_id": ObjectId(message_id)})
        if not target:
            return None

        session_id = target["sessionId"]
        timestamp = target["timestamp"]

        # Get messages before
        before_messages_docs, _ = await self.rolling_service.find_messages(
            {
                "sessionId": session_id,
                "timestamp": {"$lt": timestamp},
            },
            skip=0,
            limit=before,
            sort_order="desc",
        )

        before_messages = []
        for doc in before_messages_docs:
            before_messages.append(
                Message(
                    _id=str(doc["_id"]),
                    uuid=doc["uuid"],
                    type=doc["type"],
                    session_id=doc["sessionId"],
                    content=doc.get("content"),
                    timestamp=doc["timestamp"],
                    model=doc.get("model"),
                    parent_uuid=doc.get("parentUuid"),
                    created_at=doc.get("createdAt", doc["timestamp"]),
                )
            )

        # Reverse to get chronological order
        before_messages.reverse()

        # Get messages after
        after_messages_docs, _ = await self.rolling_service.find_messages(
            {
                "sessionId": session_id,
                "timestamp": {"$gt": timestamp},
            },
            skip=0,
            limit=after,
            sort_order="asc",
        )

        after_messages = []
        for doc in after_messages_docs:
            after_messages.append(
                Message(
                    _id=str(doc["_id"]),
                    uuid=doc["uuid"],
                    type=doc["type"],
                    session_id=doc["sessionId"],
                    content=doc.get("content"),
                    timestamp=doc["timestamp"],
                    model=doc.get("model"),
                    parent_uuid=doc.get("parentUuid"),
                    created_at=doc.get("createdAt", doc["timestamp"]),
                )
            )

        return {
            "before": before_messages,
            "target": self._doc_to_message_detail(target),
            "after": after_messages,
            "session_id": session_id,
        }

    def _doc_to_message_detail(self, doc: dict) -> MessageDetail:
        """Convert MongoDB document to MessageDetail."""
        # Extract usage from metadata if not at top level
        usage = doc.get("usage")
        if not usage and doc.get("metadata") and doc["metadata"].get("usage"):
            usage = doc["metadata"]["usage"]

        # Convert cost_usd from Decimal128 if needed
        cost_usd = doc.get("costUsd")
        if cost_usd and hasattr(cost_usd, "to_decimal"):
            cost_usd = float(cost_usd.to_decimal())
        elif cost_usd:
            cost_usd = float(cost_usd)

        return MessageDetail(
            _id=str(doc["_id"]),
            uuid=doc["uuid"],
            type=doc["type"],
            session_id=doc["sessionId"],
            content=doc.get("content"),
            timestamp=doc["timestamp"],
            model=doc.get("model"),
            parent_uuid=doc.get("parentUuid"),
            created_at=doc.get("createdAt", doc["timestamp"]),
            usage=usage,
            cost_usd=cost_usd,
            tool_use=doc.get("toolUse"),
            attachments=doc.get("attachments"),
            content_hash=doc.get("contentHash"),
        )

    async def update_message_cost(
        self, user_id: str, message_id: str, cost_usd: float
    ) -> bool:
        """Update the cost for a specific message."""
        from bson import Decimal128

        try:
            # First verify ownership through hierarchy
            message = await self.get_message(user_id, message_id)
            if not message:
                return False

            # Now update without user_id filter
            result = await self.rolling_service.update_one(
                {"_id": ObjectId(message_id)},
                {"$set": {"costUsd": Decimal128(str(cost_usd))}},
            )
            return result  # rolling_service.update_one returns bool
        except Exception:
            return False

    async def batch_update_costs(
        self, user_id: str, cost_updates: dict[str, float]
    ) -> int:
        """Batch update costs for multiple messages by UUID."""
        from bson import Decimal128

        updated_count = 0
        for uuid, cost in cost_updates.items():
            # Verify ownership through hierarchy
            msg = await self.get_message_by_uuid(user_id, uuid)
            if not msg:
                continue

            result = await self.rolling_service.update_one(
                {"uuid": uuid}, {"$set": {"costUsd": Decimal128(str(cost))}}
            )
            if result:  # rolling_service.update_one returns bool
                updated_count += 1

        # Update session total costs
        session_ids = set()
        for uuid in cost_updates.keys():
            doc = await self.rolling_service.find_one({"uuid": uuid})
            if doc:
                session_ids.add(doc["sessionId"])

        # Update each session's total cost
        for session_id in session_ids:
            await self._update_session_total_cost(user_id, session_id)

        return updated_count

    async def _update_session_total_cost(self, user_id: str, session_id: str) -> None:
        """Update the total cost for a session."""
        # Verify session ownership through hierarchy
        session = await self.db.sessions.find_one({"sessionId": session_id})
        if not session:
            return

        project = await self.db.projects.find_one(
            {"_id": session.get("projectId"), "user_id": ObjectId(user_id)}
        )
        if not project:
            return

        from datetime import UTC, datetime, timedelta

        pipeline: list[dict[str, Any]] = [
            {"$match": {"sessionId": session_id}},
            {
                "$group": {
                    "_id": None,
                    "totalCost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                }
            },
        ]

        # Use a reasonable date range for aggregation
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=365)  # Look back 1 year

        result = await self.rolling_service.aggregate_across_collections(
            pipeline, start_date, end_date
        )
        if result:
            # Handle Decimal128 from MongoDB aggregation
            total_cost_value = result[0]["totalCost"]
            if hasattr(total_cost_value, "to_decimal"):
                # It's a Decimal128 object
                total_cost = float(str(total_cost_value))
            else:
                # It's already a numeric type
                total_cost = float(total_cost_value)

            # Convert to Decimal128 for MongoDB storage
            from bson import Decimal128

            await self.db.sessions.update_one(
                {"sessionId": session_id},
                {"$set": {"totalCost": Decimal128(str(total_cost))}},
            )
