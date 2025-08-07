"""Session service layer."""

from datetime import UTC, datetime
from typing import Any

from bson import Decimal128
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.message import Message
from app.schemas.session import Session, SessionDetail


class SessionService:
    """Service for session operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def list_sessions(
        self,
        filter_dict: dict[str, Any],
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Session], int]:
        """List sessions with pagination."""
        # Count total
        total = await self.db.sessions.count_documents(filter_dict)

        # Build sort
        sort_direction = -1 if sort_order == "desc" else 1
        sort_field = {
            "started_at": "startedAt",
            "ended_at": "endedAt",
            "message_count": "messageCount",
            "total_cost": "totalCost",
        }.get(sort_by, sort_by)

        # Get sessions
        cursor = (
            self.db.sessions.find(filter_dict)
            .sort(sort_field, sort_direction)
            .skip(skip)
            .limit(limit)
        )

        sessions = []
        async for doc in cursor:
            # Convert Decimal128 to float
            total_cost = doc.get("totalCost")
            if isinstance(total_cost, Decimal128):
                total_cost = float(total_cost.to_decimal())

            # Map MongoDB fields to schema fields
            session_data = {
                "_id": str(doc["_id"]),
                "session_id": doc["sessionId"],
                "project_id": str(doc["projectId"]),
                "summary": doc.get("summary"),
                "started_at": doc["startedAt"],
                "ended_at": doc.get("endedAt"),
                "message_count": doc.get("messageCount", 0),
                "total_cost": total_cost,
                "tools_used": doc.get("toolsUsed", 0),
                "total_tokens": doc.get("totalTokens", 0),
                "input_tokens": doc.get("inputTokens", 0),
                "output_tokens": doc.get("outputTokens", 0),
            }
            sessions.append(Session(**session_data))

        return sessions, total

    async def get_session(
        self, session_id: str, include_messages: bool = False
    ) -> SessionDetail | None:
        """Get a single session by its MongoDB _id or sessionId."""
        doc = None

        # First try as MongoDB ObjectId
        try:
            from bson import ObjectId

            if ObjectId.is_valid(session_id):
                doc = await self.db.sessions.find_one({"_id": ObjectId(session_id)})
        except Exception:
            pass

        # If not found, try as sessionId field
        if not doc:
            doc = await self.db.sessions.find_one({"sessionId": session_id})

        if not doc:
            return None

        # Get the actual sessionId from the document
        actual_session_id = doc["sessionId"]

        # Get additional details
        models_used = await self.db.messages.distinct(
            "model", {"sessionId": actual_session_id, "model": {"$ne": None}}
        )

        # Get first and last messages
        first_msg = await self.db.messages.find_one(
            {"sessionId": actual_session_id}, sort=[("timestamp", 1)]
        )
        last_msg = await self.db.messages.find_one(
            {"sessionId": actual_session_id}, sort=[("timestamp", -1)]
        )

        # Get working directory from first message
        working_directory = None
        if first_msg:
            working_directory = first_msg.get("cwd")

        # Convert Decimal128 to float
        total_cost = doc.get("totalCost")
        if isinstance(total_cost, Decimal128):
            total_cost = float(total_cost.to_decimal())

        session_data = {
            "_id": str(doc["_id"]),
            "session_id": doc["sessionId"],
            "project_id": str(doc["projectId"]),
            "summary": doc.get("summary"),
            "started_at": doc["startedAt"],
            "ended_at": doc.get("endedAt"),
            "message_count": doc.get("messageCount", 0),
            "total_cost": total_cost,
            "tools_used": doc.get("toolsUsed", 0),
            "total_tokens": doc.get("totalTokens", 0),
            "input_tokens": doc.get("inputTokens", 0),
            "output_tokens": doc.get("outputTokens", 0),
            "models_used": models_used,
            "first_message": first_msg.get("content", "")[:100] if first_msg else None,
            "last_message": last_msg.get("content", "")[:100] if last_msg else None,
            "working_directory": working_directory,
        }

        # Include messages if requested
        if include_messages:
            messages = await self.get_session_messages(
                actual_session_id, skip=0, limit=10
            )
            session_data["messages"] = messages

        return SessionDetail(**session_data)

    async def get_session_messages(
        self, session_id: str, skip: int, limit: int
    ) -> list[Message]:
        """Get messages for a session by its MongoDB _id or sessionId."""
        doc = None

        # First try as MongoDB ObjectId
        try:
            from bson import ObjectId

            if ObjectId.is_valid(session_id):
                doc = await self.db.sessions.find_one({"_id": ObjectId(session_id)})
        except Exception:
            pass

        # If not found, try as sessionId field
        if not doc:
            doc = await self.db.sessions.find_one({"sessionId": session_id})

        if not doc:
            return []

        # Get the actual sessionId from the document
        actual_session_id = doc["sessionId"]

        cursor = (
            self.db.messages.find({"sessionId": actual_session_id})
            .sort("timestamp", 1)
            .skip(skip)
            .limit(limit)
        )

        messages = []
        async for doc in cursor:
            # Get cost and usage information
            cost_usd = doc.get("costUsd")
            if cost_usd:
                cost_usd = (
                    float(cost_usd.to_decimal())
                    if hasattr(cost_usd, "to_decimal")
                    else float(cost_usd)
                )

            # Extract usage data
            usage = doc.get("usage")
            input_tokens = None
            output_tokens = None
            if usage:
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")

            # Extract content - handle both direct content and message.content formats
            content = doc.get("content")
            if not content and "message" in doc and isinstance(doc["message"], dict):
                content = doc["message"].get("content")

            message_data = {
                "_id": str(doc["_id"]),
                "uuid": doc["uuid"],
                "messageUuid": doc[
                    "uuid"
                ],  # Add messageUuid for frontend compatibility
                "type": doc["type"],
                "session_id": doc["sessionId"],
                "sessionId": doc[
                    "sessionId"
                ],  # Add sessionId for frontend compatibility
                "content": content,
                "timestamp": doc["timestamp"],
                "model": doc.get("model"),
                "parent_uuid": doc.get("parentUuid"),
                "parentUuid": doc.get(
                    "parentUuid"
                ),  # Add parentUuid for frontend compatibility
                "created_at": doc.get(
                    "createdAt", doc["timestamp"]
                ),  # Fallback to timestamp if no createdAt
                "totalCost": cost_usd,
                "cost_usd": cost_usd,
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "usage": usage,
            }
            messages.append(Message(**message_data))

        return messages

    async def get_message_thread(
        self, session_id: str, message_uuid: str, depth: int
    ) -> dict[str, Any] | None:
        """Get conversation thread for a message."""
        # First get the session to find the actual sessionId
        try:
            from bson import ObjectId

            if not ObjectId.is_valid(session_id):
                return None
            session_doc = await self.db.sessions.find_one({"_id": ObjectId(session_id)})
            if not session_doc:
                return None
            actual_session_id = session_doc["sessionId"]
        except Exception:
            return None

        # Find the target message
        target = await self.db.messages.find_one(
            {"sessionId": actual_session_id, "uuid": message_uuid}
        )

        if not target:
            return None

        thread: dict[str, Any] = {
            "target": Message(
                _id=str(target["_id"]),
                uuid=target["uuid"],
                type=target["type"],
                session_id=target["sessionId"],
                content=target.get("content"),
                timestamp=target["timestamp"],
                model=target.get("model"),
                parent_uuid=target.get("parentUuid"),
                created_at=target["createdAt"],
            ),
            "ancestors": [],
            "descendants": [],
        }

        # Get ancestors
        current_uuid = target.get("parentUuid")
        ancestor_depth = 0
        while current_uuid and ancestor_depth < depth:
            parent = await self.db.messages.find_one(
                {"sessionId": session_id, "uuid": current_uuid}
            )
            if not parent:
                break

            ancestors_list: list[Any] = thread["ancestors"]
            ancestors_list.insert(
                0,
                Message(
                    _id=str(parent["_id"]),
                    uuid=parent["uuid"],
                    type=parent["type"],
                    session_id=parent["sessionId"],
                    content=parent.get("content"),
                    timestamp=parent["timestamp"],
                    model=parent.get("model"),
                    parent_uuid=parent.get("parentUuid"),
                    created_at=parent["createdAt"],
                ),
            )

            current_uuid = parent.get("parentUuid")
            ancestor_depth += 1

        # Get descendants
        descendants = await self._get_descendants(session_id, message_uuid, depth)
        thread["descendants"] = descendants

        return thread

    async def _get_descendants(
        self, session_id: str, parent_uuid: str, depth: int, current_depth: int = 0
    ) -> list[Message]:
        """Recursively get descendants of a message."""
        if current_depth >= depth:
            return []

        cursor = self.db.messages.find(
            {"sessionId": session_id, "parentUuid": parent_uuid}
        ).sort("timestamp", 1)

        descendants = []
        async for doc in cursor:
            message = Message(
                _id=str(doc["_id"]),
                uuid=doc["uuid"],
                type=doc["type"],
                session_id=doc["sessionId"],
                content=doc.get("content"),
                timestamp=doc["timestamp"],
                model=doc.get("model"),
                parent_uuid=doc.get("parentUuid"),
                created_at=doc["createdAt"],
            )
            descendants.append(message)

            # Get descendants of this message
            sub_descendants = await self._get_descendants(
                session_id, doc["uuid"], depth, current_depth + 1
            )
            descendants.extend(sub_descendants)

        return descendants

    async def generate_summary(self, session_id: str) -> str | None:
        """Generate a summary for a session."""
        # Get session by _id
        try:
            from bson import ObjectId

            if not ObjectId.is_valid(session_id):
                return None
            session = await self.db.sessions.find_one({"_id": ObjectId(session_id)})
            if not session:
                return None
            actual_session_id = session["sessionId"]
        except Exception:
            return None

        # Get first and last few messages
        messages = (
            await self.db.messages.find(
                {"sessionId": actual_session_id, "type": {"$in": ["user", "assistant"]}}
            )
            .sort("timestamp", 1)
            .to_list(None)
        )

        if not messages:
            return "Empty conversation"

        # Enhanced summary generation
        first_user_msg = next((msg for msg in messages if msg["type"] == "user"), None)

        if first_user_msg and first_user_msg.get("content"):
            content: str = first_user_msg["content"]

            # Clean up the content for better titles
            # Remove markdown code blocks
            import re

            content = re.sub(r"```[\s\S]*?```", "", content)
            # Remove multiple spaces and newlines
            content = " ".join(content.split())

            # Try to extract a meaningful title
            # Look for question patterns
            question_match = re.search(
                r"^((?:how|what|why|when|where|who|can|should|is|are|does|do|help|implement|create|fix|debug|explain|show|find|write|build|add|update|improve)[^.?!]*[.?!])",
                content,
                re.IGNORECASE,
            )

            if question_match:
                summary = question_match.group(1).strip()
                # Capitalize first letter
                summary = summary[0].upper() + summary[1:] if summary else summary
                # Don't truncate if this looks like a complete summary
                # Only truncate if it's very long and seems like raw content
                if len(summary) > 200 and not summary.startswith("#"):
                    summary = summary[:197] + "..."
            else:
                # Look for imperative sentences or statements
                sentences = re.split(r"[.!?]+", content)
                if sentences and sentences[0].strip():
                    summary = sentences[0].strip()
                    # Capitalize first letter
                    summary = summary[0].upper() + summary[1:] if summary else summary
                    # Don't truncate if this looks like a complete summary
                    # Only truncate if it's very long and seems like raw content
                    if len(summary) > 200 and not summary.startswith("#"):
                        summary = summary[:197] + "..."
                else:
                    # Fallback to truncated content
                    summary = content[:100]
                    if len(content) > 100:
                        summary += "..."
        else:
            # Check if there are tool uses or specific patterns in assistant messages
            assistant_msgs = [msg for msg in messages[:3] if msg["type"] == "assistant"]
            if assistant_msgs:
                # Look for common patterns
                for msg in assistant_msgs:
                    content = msg.get("content", "")
                    if "error" in content.lower():
                        summary = "Debugging session"
                        break
                    elif "implement" in content.lower() or "create" in content.lower():
                        summary = "Implementation task"
                        break
                    elif "fix" in content.lower() or "bug" in content.lower():
                        summary = "Bug fixing session"
                        break
                else:
                    summary = f"Conversation with {len(messages)} messages"
            else:
                summary = f"Conversation with {len(messages)} messages"

        # Update session with summary
        await self.db.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"summary": summary, "updatedAt": datetime.now(UTC)}},
        )

        return summary
