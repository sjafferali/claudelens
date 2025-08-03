"""Parser for Claude conversation messages."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class ClaudeMessageParser:
    """Parses and validates Claude message format."""

    def parse_jsonl_message(self, raw_message: dict[str, Any]) -> dict[str, Any] | None:
        """Parse a raw message from JSONL files.

        Handles the following message types:
        - summary: Session summaries (stored separately)
        - user: User inputs with optional tool results
        - assistant: Claude responses with model info and costs

        Returns None if message should be skipped.
        """
        msg_type = raw_message.get("type")

        # Skip summary messages - they should be handled differently
        # Summary data is attached to the leaf message, not sent as separate messages
        if msg_type == "summary":
            return None

        # Basic validation
        required_fields = ["uuid", "type", "timestamp"]
        if not all(field in raw_message for field in required_fields):
            return None

        # Parse timestamp
        try:
            timestamp = self._parse_timestamp(raw_message["timestamp"])
        except Exception:
            return None

        # Build normalized message
        message = {
            "uuid": raw_message["uuid"],
            "type": raw_message["type"],
            "timestamp": timestamp.isoformat(),
            "sessionId": raw_message.get("sessionId"),
            "parentUuid": raw_message.get("parentUuid"),
            "isSidechain": raw_message.get("isSidechain", False),
            "userType": raw_message.get("userType", "external"),
            "cwd": raw_message.get("cwd"),
            "version": raw_message.get("version"),
            "gitBranch": raw_message.get("gitBranch"),
        }

        # Add message content based on type
        if "message" in raw_message:
            message["message"] = raw_message["message"]

        # Add type-specific fields
        if msg_type == "user":
            message.update(self._parse_user_message(raw_message))
        elif msg_type == "assistant":
            message.update(self._parse_assistant_message(raw_message))

        return message

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime."""
        # Handle different timestamp formats
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        return datetime.fromisoformat(timestamp_str)

    def _parse_user_message(self, raw_message: dict[str, Any]) -> dict[str, Any]:
        """Parse user message fields."""
        result = {
            "userType": raw_message.get("userType", "external"),
            "cwd": raw_message.get("cwd"),
        }

        # Extract message content
        if "message" in raw_message:
            result["message"] = raw_message["message"]

        # Tool use results
        if "toolUseResult" in raw_message:
            tool_result = raw_message["toolUseResult"]
            # Ensure tool result is always a dict
            if isinstance(tool_result, str):
                result["toolUseResult"] = {"output": tool_result}
            elif isinstance(tool_result, dict):
                result["toolUseResult"] = tool_result
            else:
                # Handle other types by converting to string
                result["toolUseResult"] = {"output": str(tool_result)}

        return result

    def _parse_assistant_message(self, raw_message: dict[str, Any]) -> dict[str, Any]:
        """Parse assistant message fields."""
        result = {}

        # Extract message content
        if "message" in raw_message:
            message = raw_message["message"]
            result["message"] = message

            # Extract model info
            if isinstance(message, dict):
                if "model" in message:
                    result["model"] = message["model"]
                if "usage" in message:
                    result["usage"] = message["usage"]

        # Cost and duration (from JSONL metadata)
        if "costUsd" in raw_message:
            result["costUsd"] = raw_message["costUsd"]
        if "durationMs" in raw_message:
            result["durationMs"] = raw_message["durationMs"]

        # Request ID
        if "requestId" in raw_message:
            result["requestId"] = raw_message["requestId"]

        return result


class ClaudeDatabaseReader:
    """Reads messages from Claude's SQLite database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def read_messages(
        self, after_timestamp: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Read messages from SQLite database.

        Joins data from multiple tables to reconstruct full messages.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        try:
            query = """
            SELECT
                b.uuid,
                b.parent_uuid,
                b.session_id,
                b.timestamp,
                b.message_type,
                b.cwd,
                b.user_type,
                b.version,
                b.isSidechain,
                u.message as user_message,
                u.tool_use_result,
                a.message as assistant_message,
                a.cost_usd,
                a.duration_ms,
                a.model,
                c.summary
            FROM base_messages b
            LEFT JOIN user_messages u ON b.uuid = u.uuid
            LEFT JOIN assistant_messages a ON b.uuid = a.uuid
            LEFT JOIN conversation_summaries c ON b.uuid = c.leaf_uuid
            """

            params = []
            if after_timestamp:
                query += " WHERE b.timestamp > ?"
                params.append(int(after_timestamp.timestamp() * 1000))

            query += " ORDER BY b.timestamp ASC"

            cursor = conn.execute(query, params)
            messages = []

            for row in cursor:
                message = self._row_to_message(dict(row))
                if message:
                    messages.append(message)

            return messages

        finally:
            conn.close()

    def _row_to_message(self, row: dict[str, Any]) -> dict[str, Any] | None:
        """Convert SQLite row to message format."""
        # Skip if no message type
        if not row.get("message_type"):
            return None

        # Base message structure
        message = {
            "uuid": row["uuid"],
            "type": row["message_type"],
            "parentUuid": row["parent_uuid"],
            "sessionId": row["session_id"],
            "timestamp": datetime.fromtimestamp(row["timestamp"] / 1000).isoformat(),
            "cwd": row["cwd"],
            "userType": row["user_type"],
            "version": row["version"],
            "isSidechain": bool(row["isSidechain"]),
        }

        # Add type-specific content
        if row["message_type"] == "user" and row["user_message"]:
            message["message"] = json.loads(row["user_message"])
            if row["tool_use_result"]:
                # Handle tool_use_result - it might be a JSON string or already parsed
                try:
                    tool_result = json.loads(row["tool_use_result"])
                    # If it's a string, wrap it in a dict
                    if isinstance(tool_result, str):
                        message["toolUseResult"] = {"output": tool_result}
                    else:
                        message["toolUseResult"] = tool_result
                except (json.JSONDecodeError, TypeError):
                    # If it's not valid JSON, treat it as a plain string
                    message["toolUseResult"] = {"output": str(row["tool_use_result"])}

        elif row["message_type"] == "assistant" and row["assistant_message"]:
            message["message"] = json.loads(row["assistant_message"])
            if row["cost_usd"]:
                message["costUsd"] = row["cost_usd"]
            if row["duration_ms"]:
                message["durationMs"] = row["duration_ms"]
            if row["model"]:
                message["model"] = row["model"]

        # Add summary if this is a summary node
        if row["summary"]:
            message["summary"] = row["summary"]

        return message
