"""Export API endpoints for MCP integration."""

from datetime import UTC, datetime
from typing import Any, AsyncGenerator, Dict, Optional, Union

from bson import ObjectId
from fastapi import HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import CommonDeps
from app.core.custom_router import APIRouter
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/sessions/{session_id}/export", response_model=None)
async def export_session_for_mcp(
    session_id: str,
    db: CommonDeps,
    format: str = Query("json", description="Export format (json, markdown)"),
    include_metadata: bool = Query(True, description="Include metadata"),
    include_costs: bool = Query(True, description="Include cost information"),
    flatten_threads: bool = Query(False, description="Flatten conversation threads"),
) -> Union[Dict[str, Any], StreamingResponse]:
    """Export a session in a format optimized for MCP consumption.

    This endpoint provides a structured export of session data that's easier
    for MCP servers to process and expose as resources.
    """
    # Validate session ID
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Get session
    session = await db.sessions.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise NotFoundError("Session", session_id)

    # Get all messages for the session
    messages_cursor = db.messages.find({"sessionId": session["sessionId"]}).sort(
        "timestamp", 1
    )

    messages = await messages_cursor.to_list(None)

    # Process messages into structured format
    processed_messages = []
    message_map = {}  # For building thread structure

    for msg in messages:
        processed_msg = {
            "id": str(msg["_id"]),
            "uuid": msg.get("uuid"),
            "timestamp": msg.get("timestamp").isoformat()
            if msg.get("timestamp")
            else None,
            "type": msg.get("type"),
            "role": msg.get("userType"),
            "parent_uuid": msg.get("parentUuid"),
        }

        # Extract content
        if msg.get("message"):
            message_data = msg["message"]
            if isinstance(message_data, dict):
                if "text" in message_data:
                    processed_msg["content"] = message_data["text"]
                elif "content" in message_data:
                    content = message_data["content"]
                    if isinstance(content, str):
                        processed_msg["content"] = content
                    elif isinstance(content, list):
                        # Extract text from content blocks
                        text_parts = []
                        code_blocks = []
                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                                elif block.get("type") == "code":
                                    code_blocks.append(
                                        {
                                            "language": block.get("language"),
                                            "code": block.get("code", ""),
                                        }
                                    )
                        processed_msg["content"] = "\n".join(text_parts)
                        if code_blocks:
                            processed_msg["code_blocks"] = code_blocks
            else:
                processed_msg["content"] = str(message_data)

        # Include metadata if requested
        if include_metadata:
            processed_msg["metadata"] = {
                "model": msg.get("model"),
                "cwd": msg.get("cwd"),
                "git_branch": msg.get("gitBranch"),
                "version": msg.get("version"),
                "is_sidechain": msg.get("isSidechain", False),
            }

        # Include costs if requested
        if include_costs and msg.get("costUsd"):
            processed_msg["cost"] = {
                "usd": msg.get("costUsd"),
                "duration_ms": msg.get("durationMs"),
            }
            if msg.get("usage"):
                processed_msg["usage"] = msg.get("usage")

        processed_messages.append(processed_msg)

        # Build message map for thread structure
        if msg.get("uuid"):
            message_map[msg["uuid"]] = processed_msg

    # Build conversation threads if not flattening
    if not flatten_threads:
        # Build parent-child relationships
        for msg in processed_messages:
            if msg.get("parent_uuid") and msg["parent_uuid"] in message_map:
                parent = message_map[msg["parent_uuid"]]
                if "children" not in parent:
                    parent["children"] = []
                parent["children"].append(msg["uuid"])

    # Prepare export data
    export_data = {
        "session": {
            "id": str(session["_id"]),
            "session_id": session["sessionId"],
            "project_id": str(session.get("projectId"))
            if session.get("projectId")
            else None,
            "started_at": session.get("startedAt").isoformat()
            if session.get("startedAt")
            else None,
            "ended_at": session.get("endedAt").isoformat()
            if session.get("endedAt")
            else None,
            "message_count": session.get("messageCount", 0),
            "total_cost": session.get("totalCost", 0.0),
            "summary": session.get("summary"),
            "title": session.get("title"),
        },
        "messages": processed_messages,
        "export_metadata": {
            "format": format,
            "include_metadata": include_metadata,
            "include_costs": include_costs,
            "flatten_threads": flatten_threads,
            "exported_at": datetime.now(UTC).isoformat(),
            "message_count": len(processed_messages),
        },
    }

    # Convert to markdown if requested
    if format == "markdown":
        return StreamingResponse(
            _generate_markdown_export(export_data),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=session_{session_id}.md"
            },
        )

    return export_data


@router.get("/conversations/structured")
async def get_structured_conversations(
    db: CommonDeps,
    project_id: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    include_summaries: bool = Query(True),
    include_costs: bool = Query(True),
) -> Dict[str, Any]:
    """Get conversations in a structured format optimized for MCP resources.

    Returns sessions grouped by project with hierarchical organization.
    """
    # Build filter
    filter_dict = {}
    if project_id:
        if not ObjectId.is_valid(project_id):
            raise HTTPException(status_code=400, detail="Invalid project ID")
        filter_dict["projectId"] = ObjectId(project_id)

    # Get sessions
    sessions_cursor = db.sessions.find(filter_dict).sort("startedAt", -1).limit(limit)
    sessions = await sessions_cursor.to_list(None)

    # Group by project if not filtering by project
    if not project_id:
        # Get project information
        project_ids = list(
            set(s.get("projectId") for s in sessions if s.get("projectId"))
        )
        projects = {}
        if project_ids:
            projects_cursor = db.projects.find({"_id": {"$in": project_ids}})
            async for project in projects_cursor:
                projects[str(project["_id"])] = {
                    "id": str(project["_id"]),
                    "name": project.get("name", "Unnamed Project"),
                    "description": project.get("description"),
                    "sessions": [],
                }

        # Add "No Project" group
        projects["no_project"] = {
            "id": "no_project",
            "name": "No Project",
            "description": "Sessions without a project",
            "sessions": [],
        }

        # Group sessions by project
        for session in sessions:
            project_key = (
                str(session.get("projectId"))
                if session.get("projectId")
                else "no_project"
            )
            if project_key not in projects:
                projects[project_key] = {
                    "id": project_key,
                    "name": "Unknown Project",
                    "sessions": [],
                }

            session_data = {
                "id": str(session["_id"]),
                "session_id": session["sessionId"],
                "started_at": session.get("startedAt").isoformat()
                if session.get("startedAt")
                else None,
                "ended_at": session.get("endedAt").isoformat()
                if session.get("endedAt")
                else None,
                "message_count": session.get("messageCount", 0),
                "title": session.get("title", "Untitled Session"),
            }

            if include_summaries:
                session_data["summary"] = session.get("summary")

            if include_costs:
                session_data["total_cost"] = session.get("totalCost", 0.0)

            projects[project_key]["sessions"].append(session_data)

        return {
            "projects": list(projects.values()),
            "total_sessions": len(sessions),
            "metadata": {
                "include_summaries": include_summaries,
                "include_costs": include_costs,
            },
        }
    else:
        # Return flat list for single project
        processed_sessions = []
        for session in sessions:
            session_data = {
                "id": str(session["_id"]),
                "session_id": session["sessionId"],
                "started_at": session.get("startedAt").isoformat()
                if session.get("startedAt")
                else None,
                "ended_at": session.get("endedAt").isoformat()
                if session.get("endedAt")
                else None,
                "message_count": session.get("messageCount", 0),
                "title": session.get("title", "Untitled Session"),
            }

            if include_summaries:
                session_data["summary"] = session.get("summary")

            if include_costs:
                session_data["total_cost"] = session.get("totalCost", 0.0)

            processed_sessions.append(session_data)

        return {
            "project_id": project_id,
            "sessions": processed_sessions,
            "total_sessions": len(processed_sessions),
            "metadata": {
                "include_summaries": include_summaries,
                "include_costs": include_costs,
            },
        }


async def _generate_markdown_export(
    export_data: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """Generate markdown format export."""

    session = export_data["session"]
    messages = export_data["messages"]

    # Start with session header
    yield "# Claude Session Export\n\n"
    yield f"**Session ID**: {session['session_id']}\n"
    yield f"**Started**: {session['started_at']}\n"
    yield f"**Ended**: {session['ended_at']}\n"
    yield f"**Messages**: {session['message_count']}\n"
    if session.get("total_cost"):
        yield f"**Total Cost**: ${session['total_cost']:.4f}\n"
    if session.get("summary"):
        yield f"\n## Summary\n{session['summary']}\n"

    yield "\n---\n\n## Conversation\n\n"

    # Output messages
    for msg in messages:
        role = msg.get("role", "unknown")
        timestamp = msg.get("timestamp", "")

        # Format role header
        if role == "user":
            yield "### 👤 User"
        elif role == "assistant":
            yield "### 🤖 Assistant"
        else:
            yield f"### {role.title()}"

        if msg.get("metadata", {}).get("model"):
            yield f" ({msg['metadata']['model']})"

        yield f"\n*{timestamp}*\n\n"

        # Output content
        if msg.get("content"):
            yield f"{msg['content']}\n\n"

        # Output code blocks if present
        if msg.get("code_blocks"):
            for block in msg["code_blocks"]:
                lang = block.get("language", "")
                code = block.get("code", "")
                yield f"```{lang}\n{code}\n```\n\n"

        # Output cost if present
        if msg.get("cost"):
            yield f"*Cost: ${msg['cost']['usd']:.6f}"
            if msg["cost"].get("duration_ms"):
                yield f" | Duration: {msg['cost']['duration_ms']}ms"
            yield "*\n\n"

        yield "---\n\n"
