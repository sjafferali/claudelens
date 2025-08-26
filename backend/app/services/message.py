"""Message service layer."""

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.message import Message, MessageDetail


class MessageService:
    """Service for message operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def list_messages(
        self,
        user_id: str,
        filter_dict: dict[str, Any],
        skip: int,
        limit: int,
        sort_order: str,
    ) -> tuple[list[Message], int]:
        """List messages with pagination."""
        # Add user_id filtering
        filter_dict["user_id"] = ObjectId(user_id)

        # Count total
        total = await self.db.messages.count_documents(filter_dict)

        # Build sort
        sort_direction = 1 if sort_order == "asc" else -1

        # Get messages
        cursor = (
            self.db.messages.find(filter_dict)
            .sort("timestamp", sort_direction)
            .skip(skip)
            .limit(limit)
        )

        messages = []
        async for doc in cursor:
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

        doc = await self.db.messages.find_one(
            {"_id": ObjectId(message_id), "user_id": ObjectId(user_id)}
        )
        if not doc:
            return None

        return self._doc_to_message_detail(doc)

    async def get_message_by_uuid(
        self, user_id: str, uuid: str
    ) -> MessageDetail | None:
        """Get a message by its Claude UUID."""
        doc = await self.db.messages.find_one(
            {"uuid": uuid, "user_id": ObjectId(user_id)}
        )
        if not doc:
            return None

        return self._doc_to_message_detail(doc)

    async def get_message_context(
        self, user_id: str, message_id: str, before: int, after: int
    ) -> dict | None:
        """Get a message with surrounding context."""
        if not ObjectId.is_valid(message_id):
            return None

        # Get the target message
        target = await self.db.messages.find_one(
            {"_id": ObjectId(message_id), "user_id": ObjectId(user_id)}
        )
        if not target:
            return None

        session_id = target["sessionId"]
        timestamp = target["timestamp"]

        # Get messages before
        before_cursor = (
            self.db.messages.find(
                {
                    "sessionId": session_id,
                    "timestamp": {"$lt": timestamp},
                    "user_id": ObjectId(user_id),
                }
            )
            .sort("timestamp", -1)
            .limit(before)
        )

        before_messages = []
        async for doc in before_cursor:
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
        after_cursor = (
            self.db.messages.find(
                {
                    "sessionId": session_id,
                    "timestamp": {"$gt": timestamp},
                    "user_id": ObjectId(user_id),
                }
            )
            .sort("timestamp", 1)
            .limit(after)
        )

        after_messages = []
        async for doc in after_cursor:
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
            result = await self.db.messages.update_one(
                {"_id": ObjectId(message_id), "user_id": ObjectId(user_id)},
                {"$set": {"costUsd": Decimal128(str(cost_usd))}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def batch_update_costs(
        self, user_id: str, cost_updates: dict[str, float]
    ) -> int:
        """Batch update costs for multiple messages by UUID."""
        from bson import Decimal128

        updated_count = 0
        for uuid, cost in cost_updates.items():
            result = await self.db.messages.update_one(
                {"uuid": uuid, "user_id": ObjectId(user_id)},
                {"$set": {"costUsd": Decimal128(str(cost))}},
            )
            if result.modified_count > 0:
                updated_count += 1

        # Update session total costs
        session_ids = set()
        cursor = self.db.messages.find(
            {"uuid": {"$in": list(cost_updates.keys())}, "user_id": ObjectId(user_id)},
            {"sessionId": 1},
        )
        async for doc in cursor:
            session_ids.add(doc["sessionId"])

        # Update each session's total cost
        for session_id in session_ids:
            await self._update_session_total_cost(user_id, session_id)

        return updated_count

    async def _update_session_total_cost(self, user_id: str, session_id: str) -> None:
        """Update the total cost for a session."""
        pipeline: list[dict[str, Any]] = [
            {"$match": {"sessionId": session_id, "user_id": ObjectId(user_id)}},
            {
                "$group": {
                    "_id": None,
                    "totalCost": {"$sum": {"$ifNull": ["$costUsd", 0]}},
                }
            },
        ]

        result = await self.db.messages.aggregate(pipeline).to_list(1)
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
                {"sessionId": session_id, "user_id": ObjectId(user_id)},
                {"$set": {"totalCost": Decimal128(str(total_cost))}},
            )
