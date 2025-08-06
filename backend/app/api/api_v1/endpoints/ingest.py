"""Ingestion API endpoints."""

import logging
from datetime import datetime
from typing import Any

from fastapi import BackgroundTasks, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import AuthDeps, CommonDeps
from app.core.custom_router import APIRouter
from app.core.exceptions import ValidationError
from app.schemas.ingest import (
    BatchIngestRequest,
    BatchIngestResponse,
    MessageIngest,
)
from app.services.ingest import IngestService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/batch", response_model=BatchIngestResponse)
async def ingest_batch(
    request: BatchIngestRequest,
    background_tasks: BackgroundTasks,
    db: CommonDeps,
    api_key: AuthDeps,
) -> BatchIngestResponse:
    """Ingest a batch of messages.

    Accepts up to 1000 messages per request. Messages are validated,
    deduplicated, and stored in the database. Returns statistics about
    the ingestion process.
    """
    # Validate batch size
    if len(request.messages) > 1000:
        raise HTTPException(
            status_code=400, detail="Batch size exceeds maximum of 1000 messages"
        )

    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # Initialize service
    ingest_service = IngestService(db)

    try:
        # Process messages with overwrite mode if specified
        stats = await ingest_service.ingest_messages(
            request.messages, overwrite_mode=request.overwrite_mode
        )

        # Schedule background tasks
        if stats.projects_created:
            background_tasks.add_task(
                update_project_metadata, db, stats.projects_created
            )

        return BatchIngestResponse(
            success=True, stats=stats, message="Batch ingestion completed successfully"
        )

    except ValidationError as e:
        logger.error(f"Validation error during ingestion: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error during batch ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process batch")


@router.post("/message", response_model=BatchIngestResponse)
async def ingest_single(
    message: MessageIngest, db: CommonDeps, api_key: AuthDeps
) -> BatchIngestResponse:
    """Ingest a single message.

    Convenience endpoint for ingesting individual messages.
    """
    return await ingest_batch(
        BatchIngestRequest(
            messages=[message], todos=[], config=None, overwrite_mode=False
        ),
        BackgroundTasks(),
        db,
        api_key,
    )


@router.get("/status")
async def ingestion_status(db: CommonDeps, api_key: AuthDeps) -> dict[str, Any]:
    """Get ingestion system status.

    Returns current ingestion statistics and system health.
    """
    # Get collection stats
    messages_count = await db.messages.estimated_document_count()
    sessions_count = await db.sessions.estimated_document_count()
    projects_count = await db.projects.estimated_document_count()

    # Get recent ingestion stats
    recent_ingests = await db.ingestion_logs.find(
        {}, limit=10, sort=[("timestamp", -1)]
    ).to_list(10)

    return {
        "status": "operational",
        "statistics": {
            "total_messages": messages_count,
            "total_sessions": sessions_count,
            "total_projects": projects_count,
        },
        "recent_ingestions": [
            {
                "timestamp": log["timestamp"],
                "messages_processed": log["messages_processed"],
                "duration_ms": log["duration_ms"],
            }
            for log in recent_ingests
        ],
    }


async def update_project_metadata(
    db: AsyncIOMotorDatabase, project_ids: list[str]
) -> None:
    """Background task to update project metadata."""
    try:
        for project_id in project_ids:
            # Count messages and sessions
            pipeline: list[dict[str, Any]] = [
                {"$match": {"projectId": project_id}},
                {
                    "$group": {
                        "_id": None,
                        "message_count": {"$sum": 1},
                        "session_count": {"$addToSet": "$sessionId"},
                    }
                },
            ]

            result = await db.messages.aggregate(pipeline).to_list(1)
            if result:
                stats = result[0]
                await db.projects.update_one(
                    {"_id": project_id},
                    {
                        "$set": {
                            "stats.message_count": stats["message_count"],
                            "stats.session_count": len(stats["session_count"]),
                            "updated_at": datetime.utcnow(),
                        }
                    },
                )
    except Exception as e:
        logger.error(f"Error updating project metadata: {e}")
