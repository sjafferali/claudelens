"""Export service for handling export operations."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any, AsyncGenerator, Callable, Dict, List, Literal, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import get_logger
from app.models.export_job import ExportJob
from app.services.file_service import FileService

logger = get_logger(__name__)


class ExportProgressTracker:
    """Track export progress and send updates via WebSocket."""

    def __init__(
        self,
        job_id: str,
        total_items: int,
        update_callback: Callable,
    ):
        self.job_id = job_id
        self.total_items = total_items
        self.processed_items = 0
        self.update_callback = update_callback
        self.last_update_time = 0.0
        self.update_interval = 0.5  # seconds

    async def increment(self, count: int = 1) -> None:
        """Increment progress and send update if needed."""
        import time

        self.processed_items += count

        # Throttle updates to avoid overwhelming WebSocket
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            await self.send_update()
            self.last_update_time = current_time

    async def send_update(self) -> None:
        """Send progress update via WebSocket."""
        progress = {
            "current": self.processed_items,
            "total": self.total_items,
            "percentage": round((self.processed_items / self.total_items) * 100, 2)
            if self.total_items > 0
            else 0,
        }
        await self.update_callback(self.job_id, progress)

    async def complete(self) -> None:
        """Mark export as complete."""
        self.processed_items = self.total_items
        await self.send_update()


class ExportService:
    """Service for handling export operations."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize the export service."""
        self.db = db
        self.file_service = FileService()

    async def create_export_job(
        self,
        user_id: str,
        format: Literal["json", "csv", "markdown", "pdf"],
        filters: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExportJob:
        """
        Create a new export job.

        Args:
            user_id: User ID
            format: Export format (json, csv, markdown, pdf)
            filters: Export filters
            options: Export options

        Returns:
            Created export job
        """
        # Estimate size and duration based on filters
        estimated_count = await self._estimate_conversation_count(filters)
        estimated_size = self._estimate_file_size(format, estimated_count)
        estimated_duration = self._estimate_duration(estimated_count)

        # Create export job with explicit ObjectId
        from app.models.export_job import PyObjectId

        job_id = PyObjectId()

        export_job = ExportJob(
            _id=job_id,  # Use the correct field name
            user_id=user_id,
            format=format,
            filters=filters or {},
            options=options or {},
            status="queued",
            estimated_size_bytes=estimated_size,
            estimated_duration_seconds=estimated_duration,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

        # Save to database with proper ObjectId
        job_data = export_job.model_dump(by_alias=True)
        # Ensure _id is ObjectId not string
        job_data["_id"] = job_id
        await self.db.export_jobs.insert_one(job_data)

        logger.info(f"Created export job {export_job.id} for user {user_id}")

        return export_job

    async def process_export(
        self,
        job_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Process an export job.

        Args:
            job_id: Export job ID
            progress_callback: Optional callback for progress updates

        Returns:
            Export result with file info
        """
        # Get export job using ObjectId
        export_job = await self.db.export_jobs.find_one({"_id": ObjectId(job_id)})
        if not export_job:
            raise ValueError(f"Export job {job_id} not found")

        # Update status to processing
        await self.db.export_jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": "processing",
                    "started_at": datetime.now(UTC),
                }
            },
        )

        try:
            # Get session IDs based on filters
            session_ids = await self._get_filtered_session_ids(export_job["filters"])

            # Generate export based on format
            if export_job["format"] == "json":
                content_generator = self.generate_json_export(
                    job_id, session_ids, progress_callback
                )
            elif export_job["format"] == "csv":
                content_generator = self.generate_csv_export(
                    job_id, session_ids, progress_callback
                )
            elif export_job["format"] == "markdown":
                content_generator = self.generate_markdown_export(
                    job_id, session_ids, progress_callback
                )
            elif export_job["format"] == "pdf":
                content_generator = self.generate_pdf_export(
                    job_id, session_ids, progress_callback
                )
            else:
                raise ValueError(f"Unsupported format: {export_job['format']}")

            # Save export file
            file_info = await self.file_service.save_export_file(
                job_id, content_generator, export_job["format"]
            )

            # Update job with completion info
            # Transform file_info to match frontend expectations
            frontend_file_info = {
                "sizeBytes": file_info["size"],
                "conversationsCount": len(session_ids),
                "format": file_info["format"],
                "checksum": file_info.get("checksum"),
            }

            await self.db.export_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(UTC),
                        "file_info": frontend_file_info,
                        "file_path": file_info["path"],
                        "statistics": {
                            "conversations_count": len(session_ids),
                            "file_size": file_info["size"],
                        },
                    }
                },
            )

            logger.info(f"Completed export job {job_id}")

            return file_info

        except Exception as e:
            logger.error(f"Error processing export job {job_id}: {e}")

            # Update job with error
            await self.db.export_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.now(UTC),
                        "errors": [
                            {
                                "message": str(e),
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        ],
                    }
                },
            )

            raise

    async def generate_json_export(
        self,
        job_id: str,
        session_ids: List[str],
        progress_callback: Optional[Callable] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate JSON export with streaming.

        Args:
            job_id: Export job ID
            session_ids: List of session IDs to export
            progress_callback: Optional callback for progress updates

        Yields:
            JSON content in chunks
        """
        yield b'{"conversations":['

        first = True
        tracker = (
            ExportProgressTracker(job_id, len(session_ids), progress_callback)
            if progress_callback
            else None
        )

        # Process in batches of 100 to avoid connection pool exhaustion
        for batch_start in range(0, len(session_ids), 100):
            batch_ids = session_ids[batch_start : batch_start + 100]

            # Batch query for efficiency
            sessions = await self.db.sessions.find(
                {"_id": {"$in": [ObjectId(sid) for sid in batch_ids]}}
            ).to_list(length=100)

            for session in sessions:
                if not first:
                    yield b","
                first = False

                # Include messages for each session
                messages = await self.db.messages.find(
                    {"sessionId": session.get("sessionId")}
                ).to_list(length=None)

                export_data = {
                    "id": str(session["_id"]),
                    "title": session.get("title", ""),
                    "summary": session.get("summary"),
                    "projectId": str(session.get("projectId"))
                    if session.get("projectId")
                    else None,
                    "createdAt": session.get("startedAt").isoformat()
                    if session.get("startedAt")
                    else None,
                    "updatedAt": session.get("endedAt").isoformat()
                    if session.get("endedAt")
                    else None,
                    "model": messages[0].get("model") if messages else "unknown",
                    "costUsd": session.get("totalCost", 0.0),
                    "messageCount": session.get("messageCount", 0),
                    "tags": [],
                    "metadata": {},
                    "messages": [self._format_message(m) for m in messages],
                }

                yield json.dumps(export_data).encode("utf-8")

                if tracker:
                    await tracker.increment()

        yield b"]}"

        if tracker:
            await tracker.complete()

    async def generate_csv_export(
        self,
        job_id: str,
        session_ids: List[str],
        progress_callback: Optional[Callable] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate CSV export with streaming.

        Args:
            job_id: Export job ID
            session_ids: List of session IDs to export
            progress_callback: Optional callback for progress updates

        Yields:
            CSV content in chunks
        """
        import csv
        from io import StringIO

        buffer = StringIO()
        writer = csv.writer(buffer)

        # Write header
        writer.writerow(
            [
                "id",
                "title",
                "summary",
                "created_at",
                "message_count",
                "cost_usd",
                "model",
            ]
        )
        yield buffer.getvalue().encode("utf-8")
        buffer.seek(0)
        buffer.truncate(0)

        tracker = (
            ExportProgressTracker(job_id, len(session_ids), progress_callback)
            if progress_callback
            else None
        )

        # Process sessions
        for batch_start in range(0, len(session_ids), 100):
            batch_ids = session_ids[batch_start : batch_start + 100]

            sessions = await self.db.sessions.find(
                {"_id": {"$in": [ObjectId(sid) for sid in batch_ids]}}
            ).to_list(length=100)

            for session in sessions:
                # Get first message for model info
                first_message = await self.db.messages.find_one(
                    {"sessionId": session.get("sessionId")}
                )

                writer.writerow(
                    [
                        str(session["_id"]),
                        session.get("title", ""),
                        session.get("summary", ""),
                        session.get("startedAt").isoformat()
                        if session.get("startedAt")
                        else "",
                        session.get("messageCount", 0),
                        session.get("totalCost", 0.0),
                        first_message.get("model", "") if first_message else "",
                    ]
                )

                if tracker:
                    await tracker.increment()

                # Flush buffer periodically
                if buffer.tell() > 8192:  # 8KB
                    yield buffer.getvalue().encode("utf-8")
                    buffer.seek(0)
                    buffer.truncate(0)

        # Flush remaining data
        if buffer.tell() > 0:
            yield buffer.getvalue().encode("utf-8")

        if tracker:
            await tracker.complete()

    async def generate_markdown_export(
        self,
        job_id: str,
        session_ids: List[str],
        progress_callback: Optional[Callable] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate Markdown export with streaming.

        Args:
            job_id: Export job ID
            session_ids: List of session IDs to export
            progress_callback: Optional callback for progress updates

        Yields:
            Markdown content in chunks
        """
        yield b"# ClaudeLens Export\n\n"
        yield f"**Export Date**: {datetime.now(UTC).isoformat()}\n\n".encode("utf-8")
        yield f"**Total Conversations**: {len(session_ids)}\n\n---\n\n".encode("utf-8")

        tracker = (
            ExportProgressTracker(job_id, len(session_ids), progress_callback)
            if progress_callback
            else None
        )

        for idx, session_id in enumerate(session_ids, 1):
            session = await self.db.sessions.find_one({"_id": ObjectId(session_id)})
            if not session:
                continue

            # Session header
            yield f"## {idx}. {session.get('title', 'Untitled Session')}\n\n".encode(
                "utf-8"
            )
            yield f"**Session ID**: {session.get('sessionId')}\n".encode("utf-8")
            yield f"**Started**: {session.get('startedAt').isoformat() if session.get('startedAt') else 'N/A'}\n".encode(
                "utf-8"
            )
            yield f"**Messages**: {session.get('messageCount', 0)}\n".encode("utf-8")
            yield f"**Cost**: ${session.get('totalCost', 0.0):.4f}\n\n".encode("utf-8")

            if session.get("summary"):
                yield f"### Summary\n{session['summary']}\n\n".encode("utf-8")

            # Messages
            yield b"### Conversation\n\n"

            messages = (
                await self.db.messages.find({"sessionId": session.get("sessionId")})
                .sort("timestamp", 1)
                .to_list(None)
            )

            for msg in messages:
                role = msg.get("userType", "unknown")
                timestamp = msg.get("timestamp")

                if role == "user":
                    yield b"#### User\n"
                elif role == "assistant":
                    yield b"#### Assistant"
                    if msg.get("model"):
                        yield f" ({msg['model']})".encode("utf-8")
                    yield b"\n"
                else:
                    yield f"#### {role.title()}\n".encode("utf-8")

                if timestamp:
                    yield f"*{timestamp.isoformat()}*\n\n".encode("utf-8")

                # Extract and yield message content
                content = self._extract_message_content(msg)
                if content:
                    yield f"{content}\n\n".encode("utf-8")

                yield b"---\n\n"

            yield b"\n---\n\n"

            if tracker:
                await tracker.increment()

        if tracker:
            await tracker.complete()

    async def generate_pdf_export(
        self,
        job_id: str,
        session_ids: List[str],
        progress_callback: Optional[Callable] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate PDF export (placeholder - requires PDF library).

        Args:
            job_id: Export job ID
            session_ids: List of session IDs to export
            progress_callback: Optional callback for progress updates

        Yields:
            PDF content in chunks
        """
        # This is a placeholder - actual PDF generation would require a library like ReportLab
        # For now, we'll generate a simple text representation
        yield b"PDF export not yet implemented. Please use JSON, CSV, or Markdown format.\n"

        if progress_callback:
            tracker = ExportProgressTracker(job_id, 1, progress_callback)
            await tracker.complete()

    def _format_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Format a message for export."""
        return {
            "id": str(message.get("_id", "")),
            "type": message.get("userType", "unknown"),
            "content": self._extract_message_content(message),
            "timestamp": message["timestamp"].isoformat()
            if message.get("timestamp") and hasattr(message["timestamp"], "isoformat")
            else None,
            "model": message.get("model"),
            "costUsd": message.get("costUsd"),
            "metadata": {
                "cwd": message.get("cwd"),
                "gitBranch": message.get("gitBranch"),
                "version": message.get("version"),
            },
        }

    def _extract_message_content(self, message: Dict[str, Any]) -> str:
        """Extract content from a message."""
        if message.get("message"):
            msg_data = message["message"]
            if isinstance(msg_data, dict):
                if "text" in msg_data:
                    return str(msg_data["text"])
                elif "content" in msg_data:
                    content = msg_data["content"]
                    if isinstance(content, str):
                        return content
                    elif isinstance(content, list):
                        # Extract text from content blocks
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                        return "\n".join(text_parts)
            else:
                return str(msg_data)
        return ""

    async def _estimate_conversation_count(
        self, filters: Optional[Dict[str, Any]]
    ) -> int:
        """Estimate the number of conversations based on filters."""
        query = self._build_filter_query(filters)
        count = await self.db.sessions.count_documents(query)
        return count

    def _estimate_file_size(self, format: str, count: int) -> int:
        """Estimate file size based on format and conversation count."""
        # Rough estimates based on format
        if format == "json":
            return count * 5000  # ~5KB per conversation
        elif format == "csv":
            return count * 200  # ~200 bytes per row
        elif format == "markdown":
            return count * 8000  # ~8KB per conversation
        elif format == "pdf":
            return count * 10000  # ~10KB per conversation
        return count * 1000

    def _estimate_duration(self, count: int) -> int:
        """Estimate processing duration in seconds."""
        # Roughly 100 conversations per second
        return max(1, count // 100)

    def _build_filter_query(self, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build MongoDB query from filters."""
        if not filters:
            return {}

        query: Dict[str, Any] = {}

        # Date range filter
        if filters.get("dateRange"):
            date_range = filters["dateRange"]
            date_query = {}
            if date_range.get("start"):
                date_query["$gte"] = datetime.fromisoformat(
                    date_range["start"].replace("Z", "+00:00")
                )
            if date_range.get("end"):
                date_query["$lte"] = datetime.fromisoformat(
                    date_range["end"].replace("Z", "+00:00")
                )
            if date_query:
                query["startedAt"] = date_query

        # Project filter
        if filters.get("projectIds"):
            query["projectId"] = {
                "$in": [ObjectId(pid) for pid in filters["projectIds"]]
            }

        # Session IDs filter
        if filters.get("sessionIds"):
            query["_id"] = {"$in": [ObjectId(sid) for sid in filters["sessionIds"]]}

        # Cost range filter
        if filters.get("costRange"):
            cost_range = filters["costRange"]
            cost_query = {}
            if "min" in cost_range:
                cost_query["$gte"] = cost_range["min"]
            if "max" in cost_range:
                cost_query["$lte"] = cost_range["max"]
            if cost_query:
                query["totalCost"] = cost_query

        return query

    async def _get_filtered_session_ids(
        self, filters: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Get session IDs based on filters."""
        query = self._build_filter_query(filters)
        sessions = await self.db.sessions.find(query, {"_id": 1}).to_list(None)
        return [str(s["_id"]) for s in sessions]
