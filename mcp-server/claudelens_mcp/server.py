"""ClaudeLens MCP Server - Main server implementation."""

import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import TextContent
from pydantic import BaseModel, Field

from claudelens_mcp.api_client import ClaudeLensAPIClient

# Load environment variables
load_dotenv()

# Configuration
CLAUDELENS_API_URL = os.getenv("CLAUDELENS_API_URL", "http://localhost:8080")
CLAUDELENS_API_KEY = os.getenv("CLAUDELENS_API_KEY")


@dataclass
class AppContext:
    """Application context with ClaudeLens API client."""
    api_client: ClaudeLensAPIClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with API client."""
    # Initialize on startup
    api_client = ClaudeLensAPIClient(
        base_url=CLAUDELENS_API_URL,
        api_key=CLAUDELENS_API_KEY
    )
    try:
        yield AppContext(api_client=api_client)
    finally:
        # Cleanup on shutdown
        await api_client.close()


# Create FastMCP server with lifespan
mcp = FastMCP(
    "ClaudeLens MCP",
    instructions="""Access and search through Claude conversation history from ClaudeLens.

This MCP server provides:
- Resources for browsing sessions and messages
- Tools for searching conversations
- Navigation through conversation threads
- Analytics and summaries

Use the resources to browse session history and tools to search and analyze conversations.""",
    lifespan=app_lifespan
)


# ==================== Resources ====================

@mcp.resource("claudelens://sessions")
async def list_sessions_resource(ctx: Context) -> str:
    """List all available Claude sessions.

    Returns a JSON list of sessions with their metadata including:
    - Session ID and timestamps
    - Message count and total cost
    - Summary (if available)
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        # Get first 100 sessions
        result = await api_client.list_sessions(limit=100, sort_order="desc")
        sessions = result.get("items", [])

        # Format for display
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                "id": session.get("_id"),
                "session_id": session.get("sessionId"),
                "started_at": session.get("startedAt"),
                "ended_at": session.get("endedAt"),
                "message_count": session.get("messageCount", 0),
                "total_cost": session.get("totalCost", 0.0),
                "summary": session.get("summary", "No summary available"),
                "title": session.get("title", "Untitled Session")
            })

        return json.dumps(formatted_sessions, indent=2, default=str)
    except Exception as e:
        return f"Error fetching sessions: {str(e)}"


@mcp.resource("claudelens://sessions/{session_id}")
async def get_session_resource(ctx: Context, session_id: str) -> str:
    """Get details for a specific Claude session.

    Returns detailed information about a session including its messages.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        # Get session with initial messages
        session = await api_client.get_session(session_id, include_messages=True)

        # Format for display
        formatted = {
            "session": {
                "id": session.get("_id"),
                "session_id": session.get("sessionId"),
                "started_at": session.get("startedAt"),
                "ended_at": session.get("endedAt"),
                "message_count": session.get("messageCount", 0),
                "total_cost": session.get("totalCost", 0.0),
                "summary": session.get("summary", "No summary available"),
                "title": session.get("title", "Untitled Session")
            },
            "initial_messages": session.get("messages", [])
        }

        return json.dumps(formatted, indent=2, default=str)
    except Exception as e:
        return f"Error fetching session {session_id}: {str(e)}"


@mcp.resource("claudelens://sessions/{session_id}/messages")
async def get_session_messages_resource(ctx: Context, session_id: str) -> str:
    """Get all messages for a specific Claude session.

    Returns the complete conversation history for the session.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        # Get all messages for the session
        result = await api_client.get_session_messages(session_id, limit=1000)

        session = result.get("session", {})
        messages = result.get("messages", [])

        # Format messages for display
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "timestamp": msg.get("timestamp"),
                "type": msg.get("type"),
                "role": msg.get("userType", "unknown"),
                "model": msg.get("model"),
                "cost": msg.get("costUsd"),
                "uuid": msg.get("uuid"),
                "parent_uuid": msg.get("parentUuid")
            }

            # Extract message content
            if msg.get("message"):
                message_data = msg.get("message", {})
                if isinstance(message_data, dict):
                    if "text" in message_data:
                        formatted_msg["content"] = message_data["text"]
                    elif "content" in message_data:
                        # Handle structured content
                        content = message_data["content"]
                        if isinstance(content, str):
                            formatted_msg["content"] = content
                        elif isinstance(content, list):
                            # Extract text from content blocks
                            text_parts = []
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                            formatted_msg["content"] = "\n".join(text_parts)
                        else:
                            formatted_msg["content"] = str(content)
                    else:
                        formatted_msg["content"] = str(message_data)
                else:
                    formatted_msg["content"] = str(message_data)

            formatted_messages.append(formatted_msg)

        return json.dumps({
            "session_id": session_id,
            "total_messages": len(messages),
            "messages": formatted_messages
        }, indent=2, default=str)
    except Exception as e:
        return f"Error fetching messages for session {session_id}: {str(e)}"


@mcp.resource("claudelens://conversations/structured")
async def get_structured_conversations_resource(ctx: Context) -> str:
    """Get all conversations in a structured, hierarchical format.

    Returns sessions organized by project with complete metadata.
    This provides a comprehensive overview of all conversation history.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        result = await api_client.get_structured_conversations(
            limit=100,
            include_summaries=True,
            include_costs=True
        )

        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Error fetching structured conversations: {str(e)}"


@mcp.resource("claudelens://messages/{message_id}")
async def get_message_resource(ctx: Context, message_id: str) -> str:
    """Get details for a specific message.

    Returns complete information about a single message.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        # Try as message ID first
        try:
            message = await api_client.get_message(message_id)
        except:
            # Try as UUID if ID fails
            message = await api_client.get_message_by_uuid(message_id)

        # Format for display
        formatted = {
            "id": message.get("_id"),
            "uuid": message.get("uuid"),
            "session_id": message.get("sessionId"),
            "timestamp": message.get("timestamp"),
            "type": message.get("type"),
            "role": message.get("userType", "unknown"),
            "model": message.get("model"),
            "cost": message.get("costUsd"),
            "parent_uuid": message.get("parentUuid"),
            "cwd": message.get("cwd"),
            "git_branch": message.get("gitBranch")
        }

        # Extract message content
        if message.get("message"):
            formatted["content"] = message.get("message")

        # Include usage data if available
        if message.get("usage"):
            formatted["usage"] = message.get("usage")

        return json.dumps(formatted, indent=2, default=str)
    except Exception as e:
        return f"Error fetching message {message_id}: {str(e)}"


# ==================== Tools ====================

class SearchParameters(BaseModel):
    """Parameters for searching messages."""
    query: str = Field(description="Search query text")
    session_ids: Optional[List[str]] = Field(default=None, description="Filter by specific session IDs")
    message_types: Optional[List[str]] = Field(default=None, description="Filter by message types (user, assistant)")
    models: Optional[List[str]] = Field(default=None, description="Filter by model names")
    limit: int = Field(default=20, description="Maximum number of results to return")
    highlight: bool = Field(default=True, description="Whether to highlight matching text")
    is_regex: bool = Field(default=False, description="Whether to treat query as regex")


@mcp.tool()
async def search_messages(ctx: Context, params: SearchParameters) -> str:
    """Search through Claude conversation messages.

    Searches across all messages in the database with optional filters.
    Returns matching messages with context and highlights.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        result = await api_client.search_messages(
            query=params.query,
            session_ids=params.session_ids,
            message_types=params.message_types,
            models=params.models,
            limit=params.limit,
            highlight=params.highlight,
            is_regex=params.is_regex
        )

        # Format results for display
        formatted_results = {
            "query": params.query,
            "total_results": result.get("total", 0),
            "results": []
        }

        for item in result.get("results", []):
            formatted_item = {
                "session_id": item.get("sessionId"),
                "message_id": item.get("_id"),
                "uuid": item.get("uuid"),
                "timestamp": item.get("timestamp"),
                "type": item.get("type"),
                "role": item.get("userType"),
                "model": item.get("model"),
                "score": item.get("score"),
                "highlights": item.get("highlights", [])
            }

            # Include message preview
            if item.get("message"):
                message_data = item.get("message", {})
                if isinstance(message_data, dict) and "text" in message_data:
                    formatted_item["content_preview"] = message_data["text"][:500]
                else:
                    formatted_item["content_preview"] = str(message_data)[:500]

            formatted_results["results"].append(formatted_item)

        return json.dumps(formatted_results, indent=2, default=str)
    except Exception as e:
        return f"Error searching messages: {str(e)}"


@mcp.tool()
async def search_code(ctx: Context, query: str, language: Optional[str] = None) -> str:
    """Search specifically for code snippets in conversations.

    Optimized search for finding code blocks with optional language filtering.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        result = await api_client.search_code(
            query=query,
            language=language,
            limit=20
        )

        # Format results for display
        formatted_results = {
            "query": query,
            "language_filter": language,
            "total_results": result.get("total", 0),
            "results": []
        }

        for item in result.get("results", []):
            formatted_item = {
                "session_id": item.get("sessionId"),
                "message_id": item.get("_id"),
                "timestamp": item.get("timestamp"),
                "model": item.get("model"),
                "code_blocks": item.get("code_blocks", [])
            }
            formatted_results["results"].append(formatted_item)

        return json.dumps(formatted_results, indent=2, default=str)
    except Exception as e:
        return f"Error searching code: {str(e)}"


@mcp.tool()
async def get_conversation_thread(
    ctx: Context,
    session_id: str,
    message_uuid: str,
    depth: int = 10
) -> str:
    """Navigate through a conversation thread.

    Returns the parent and child messages for a specific message,
    allowing navigation through branching conversations.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        thread = await api_client.get_message_thread(session_id, message_uuid, depth)

        # Format thread for display
        formatted_thread = {
            "session_id": session_id,
            "center_message_uuid": message_uuid,
            "depth": depth,
            "thread": thread
        }

        return json.dumps(formatted_thread, indent=2, default=str)
    except Exception as e:
        return f"Error fetching conversation thread: {str(e)}"


@mcp.tool()
async def generate_summary(ctx: Context, session_id: str) -> str:
    """Generate or regenerate a summary for a session.

    Creates a concise summary of the conversation based on key messages.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        result = await api_client.generate_session_summary(session_id)

        return json.dumps({
            "session_id": session_id,
            "summary": result.get("summary", "Failed to generate summary")
        }, indent=2, default=str)
    except Exception as e:
        return f"Error generating summary: {str(e)}"


@mcp.tool()
async def get_message_context(
    ctx: Context,
    message_id: str,
    before: int = 5,
    after: int = 5
) -> str:
    """Get a message with surrounding context.

    Returns the specified message along with messages before and after it
    in the same session for better understanding of the conversation flow.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        context = await api_client.get_message_context(message_id, before, after)

        # Format context for display
        formatted_context = {
            "center_message_id": message_id,
            "messages_before": before,
            "messages_after": after,
            "context": context
        }

        return json.dumps(formatted_context, indent=2, default=str)
    except Exception as e:
        return f"Error fetching message context: {str(e)}"


@mcp.tool()
async def list_projects(ctx: Context) -> str:
    """List all available projects in ClaudeLens.

    Returns a list of projects with their metadata.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        result = await api_client.list_projects(limit=100)
        projects = result.get("items", [])

        # Format for display
        formatted_projects = []
        for project in projects:
            formatted_projects.append({
                "id": project.get("_id"),
                "name": project.get("name"),
                "description": project.get("description"),
                "session_count": project.get("sessionCount", 0),
                "total_cost": project.get("totalCost", 0.0),
                "created_at": project.get("createdAt"),
                "updated_at": project.get("updatedAt")
            })

        return json.dumps(formatted_projects, indent=2, default=str)
    except Exception as e:
        return f"Error fetching projects: {str(e)}"


@mcp.tool()
async def get_session_analytics(ctx: Context, session_id: str) -> str:
    """Get analytics for a specific session.

    Returns detailed analytics including token usage, costs, and patterns.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        analytics = await api_client.get_session_analytics(session_id)

        return json.dumps(analytics, indent=2, default=str)
    except Exception as e:
        return f"Error fetching session analytics: {str(e)}"


@mcp.tool()
async def export_session(
    ctx: Context,
    session_id: str,
    format: str = "json",
    include_metadata: bool = True,
    include_costs: bool = True,
    flatten_threads: bool = False
) -> str:
    """Export a complete session in a structured format.

    Provides a comprehensive export of a session with all messages,
    metadata, and thread structure. Useful for archiving or detailed analysis.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        result = await api_client.export_session_for_mcp(
            session_id=session_id,
            format=format,
            include_metadata=include_metadata,
            include_costs=include_costs,
            flatten_threads=flatten_threads
        )

        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Error exporting session: {str(e)}"


@mcp.tool()
async def get_recent_searches(ctx: Context, limit: int = 10) -> str:
    """Get recent search queries.

    Returns the most recent searches performed for quick access.
    """
    api_client = ctx.request_context.lifespan_context.api_client

    try:
        searches = await api_client.get_recent_searches(limit)

        return json.dumps({
            "recent_searches": searches,
            "count": len(searches)
        }, indent=2, default=str)
    except Exception as e:
        return f"Error fetching recent searches: {str(e)}"


# ==================== Prompts ====================

@mcp.prompt(title="Session Analysis")
def analyze_session_prompt(session_id: str) -> str:
    """Prompt template for analyzing a Claude session."""
    return f"""Please analyze the Claude session with ID: {session_id}

Use the following steps:
1. Retrieve the session details using the claudelens://sessions/{session_id} resource
2. Get all messages using claudelens://sessions/{session_id}/messages resource
3. Analyze the conversation flow, topics discussed, and any issues encountered
4. Generate insights about the session including:
   - Main topics and goals
   - Problem-solving approaches used
   - Any errors or challenges faced
   - Overall effectiveness of the conversation
5. Provide recommendations for similar future conversations"""


@mcp.prompt(title="Search and Summarize")
def search_and_summarize_prompt(query: str, limit: int = 20) -> str:
    """Prompt template for searching and summarizing results."""
    return f"""Please search for "{query}" across all Claude conversations and provide a summary.

Use the search_messages tool with these parameters:
- query: "{query}"
- limit: {limit}

Then:
1. Analyze the search results
2. Identify common patterns or themes
3. Summarize the key findings
4. Highlight any particularly useful or interesting conversations
5. Provide recommendations based on the findings"""


@mcp.prompt(title="Code Search Analysis")
def code_search_prompt(query: str, language: Optional[str] = None) -> str:
    """Prompt template for searching and analyzing code snippets."""
    lang_filter = f" in {language}" if language else ""
    return f"""Please search for code snippets{lang_filter} related to "{query}".

Use the search_code tool to find relevant code blocks, then:
1. Analyze the code patterns found
2. Identify best practices and common approaches
3. Note any potential issues or improvements
4. Summarize the different solutions attempted
5. Provide recommendations for the best approach"""


def main():
    """Main entry point for the MCP server."""
    import sys
    mcp.run()
    return 0


if __name__ == "__main__":
    main()
