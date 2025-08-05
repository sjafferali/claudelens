# ClaudeLens API Documentation

ClaudeLens provides a comprehensive REST API built with FastAPI, offering 67+ endpoints for conversation management, analytics, search, and real-time updates.

## Table of Contents
- [Base Information](#base-information)
- [Authentication](#authentication)
- [Analytics Endpoints](#analytics-endpoints)
- [Search Endpoints](#search-endpoints)
- [Session Management](#session-management)
- [Message Operations](#message-operations)
- [Project Management](#project-management)
- [Data Ingestion](#data-ingestion)
- [WebSocket Real-time Updates](#websocket-real-time-updates)
- [Health & Status](#health--status)
- [Data Schemas](#data-schemas)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Base Information

- **Base URL**: `http://localhost:8000/api/v1`
- **API Version**: v1
- **Framework**: FastAPI with automatic OpenAPI documentation
- **Interactive Docs**: Available at `/docs` (Swagger UI) and `/redoc`
- **Content Type**: `application/json`
- **Response Format**: JSON with consistent structure

## Authentication

ClaudeLens uses API key authentication for secure endpoints.

### Authentication Method
- **Type**: API Key Authentication
- **Header**: `X-API-Key`
- **Required For**: Data ingestion endpoints
- **Optional For**: Read-only analytics and search endpoints

### Example
```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/api/v1/ingest/batch
```

### Configuration
Set your API key in the backend environment variables:
```bash
API_KEY=your-secure-api-key-here
```

## Analytics Endpoints

ClaudeLens provides 30 comprehensive analytics endpoints for detailed insights into conversation patterns, costs, and performance.

### Overview Analytics

#### Get Analytics Summary
```http
GET /api/v1/analytics/summary
```

Returns high-level metrics including total messages, sessions, projects, costs, and trends.

**Parameters:**
- `time_range` (optional): Time period for analysis (7d, 30d, 90d, all)
- `project_id` (optional): Filter by specific project

**Response:**
```json
{
  "total_messages": 15420,
  "total_sessions": 892,
  "total_projects": 45,
  "total_cost": 127.89,
  "messages_trend": 15.2,
  "cost_trend": -8.7,
  "most_active_project": "project_id_123",
  "most_used_model": "claude-3-sonnet-20240229",
  "time_range": {
    "start": "2025-07-01T00:00:00Z",
    "end": "2025-08-05T23:59:59Z"
  }
}
```

#### Get Activity Heatmap
```http
GET /api/v1/analytics/activity/heatmap?days=30
```

Returns activity data aggregated by hour and day for heatmap visualization.

**Parameters:**
- `days` (optional, default: 30): Number of days to analyze
- `project_id` (optional): Filter by project

### Cost Analytics

#### Get Cost Analytics
```http
GET /api/v1/analytics/costs
```

Comprehensive cost analysis over time with model breakdown.

**Response:**
```json
{
  "total_cost": 127.89,
  "cost_trend": -8.7,
  "daily_costs": [
    {
      "date": "2025-08-05",
      "cost": 12.45,
      "message_count": 234
    }
  ],
  "model_breakdown": [
    {
      "model": "claude-3-sonnet-20240229",
      "cost": 89.23,
      "percentage": 69.8
    }
  ]
}
```

#### Get Cost Breakdown
```http
GET /api/v1/analytics/cost/breakdown
```

Detailed cost breakdown by model, time period, and project.

#### Get Cost Prediction
```http
GET /api/v1/analytics/cost/prediction
```

Cost forecasting with confidence intervals based on usage patterns.

**Response:**
```json
{
  "predictions": [
    {
      "period": "next_7_days",
      "predicted_cost": 45.67,
      "confidence_interval": {
        "lower": 38.92,
        "upper": 52.41
      }
    }
  ],
  "model_predictions": [
    {
      "model": "claude-3-sonnet-20240229",
      "predicted_usage": 1250,
      "predicted_cost": 32.18
    }
  ]
}
```

### Token Analytics

#### Get Token Usage Statistics
```http
GET /api/v1/analytics/tokens
```

Token usage patterns and efficiency metrics.

#### Get Token Analytics (Detailed)
```http
GET /api/v1/analytics/token-analytics
```

Advanced token analytics with percentiles and performance insights.

**Response:**
```json
{
  "total_tokens": 2450892,
  "input_tokens": 1234567,
  "output_tokens": 1216325,
  "efficiency_score": 87.3,
  "percentiles": {
    "p50": 1250,
    "p90": 4567,
    "p95": 7890,
    "p99": 15623
  },
  "distribution": [
    {
      "range": "0-1000",
      "count": 5432,
      "percentage": 62.1
    }
  ]
}
```

### Tool Usage Analytics

#### Get Tool Usage Summary
```http
GET /api/v1/analytics/tools/summary
```

High-level tool usage statistics for dashboard cards.

#### Get Detailed Tool Usage
```http
GET /api/v1/analytics/tools/detailed
```

Comprehensive tool execution analytics with success rates and performance metrics.

**Response:**
```json
{
  "total_tool_calls": 8934,
  "success_rate": 94.2,
  "tools": [
    {
      "name": "Edit",
      "usage_count": 2345,
      "success_rate": 96.8,
      "avg_execution_time": 1.23,
      "error_patterns": [
        {
          "error_type": "file_not_found",
          "count": 12,
          "percentage": 3.2
        }
      ]
    }
  ],
  "usage_trends": [
    {
      "tool": "Read",
      "trend": "increasing",
      "change_percentage": 15.4
    }
  ]
}
```

### Advanced Analytics

#### Get Conversation Flow Analytics
```http
GET /api/v1/analytics/conversation-flow
```

Interactive conversation flow data for visualization.

#### Get Session Health Metrics
```http
GET /api/v1/analytics/session/health
```

Session health analysis based on tool execution and error patterns.

#### Get Git Branch Analytics
```http
GET /api/v1/analytics/git-branches
```

Development workflow insights and branch activity analysis.

#### Get Directory Usage Analytics
```http
GET /api/v1/analytics/directory-usage
```

Workspace analysis with hierarchical directory structure.

#### Get Performance Benchmarks
```http
GET /api/v1/analytics/benchmarks?entities=project1,project2&metrics=cost,tokens,success_rate
```

Multi-dimensional performance comparisons.

**Parameters:**
- `entities`: Comma-separated list of entities to benchmark
- `metrics`: Metrics to compare (cost, tokens, success_rate, response_time)
- `time_range`: Time period for analysis

## Search Endpoints

Comprehensive search capabilities across all conversation data.

### Full-text Search
```http
POST /api/v1/search/
```

**Request Body:**
```json
{
  "query": "error handling in Python",
  "filters": {
    "project_ids": ["project_123"],
    "models": ["claude-3-sonnet-20240229"],
    "date_range": {
      "start": "2025-07-01",
      "end": "2025-08-05"
    },
    "message_types": ["assistant", "user"]
  },
  "highlight": true,
  "skip": 0,
  "limit": 20
}
```

**Response:**
```json
{
  "query": "error handling in Python",
  "total": 156,
  "results": [
    {
      "message_id": "msg_123",
      "session_id": "session_456",
      "content": "Here's how to handle errors in Python...",
      "highlights": [
        "handle <mark>errors</mark> in <mark>Python</mark>"
      ],
      "score": 0.95,
      "timestamp": "2025-08-05T10:30:00Z",
      "model": "claude-3-sonnet-20240229"
    }
  ],
  "took_ms": 45
}
```

### Code-specific Search
```http
POST /api/v1/search/code
```

Search specifically for code snippets with language filtering.

### Search Suggestions
```http
GET /api/v1/search/suggestions?q=partial_query
```

Autocomplete suggestions for search queries.

### Recent Searches
```http
GET /api/v1/search/recent
```

Get recent search queries for quick access.

## Session Management

Manage conversation sessions with message threading and organization.

### List Sessions
```http
GET /api/v1/sessions/?skip=0&limit=50&project_id=123&search=python
```

**Parameters:**
- `skip`: Number of sessions to skip (pagination)
- `limit`: Maximum sessions to return (max 100)
- `project_id`: Filter by project ID
- `search`: Search in session summaries
- `start_date`, `end_date`: Date range filtering

### Get Session Details
```http
GET /api/v1/sessions/{session_id}?include_messages=true
```

Retrieve detailed session information with optional message inclusion.

### Get Session Messages
```http
GET /api/v1/sessions/{session_id}/messages?skip=0&limit=100
```

Get all messages for a session in chronological order.

### Get Conversation Thread
```http
GET /api/v1/sessions/{session_id}/thread/{message_uuid}
```

Get conversation thread for a specific message with parent/child relationships.

### Generate Session Summary
```http
POST /api/v1/sessions/{session_id}/generate-summary
```

Generate or regenerate an AI-powered summary for a session.

## Message Operations

CRUD operations for individual messages with context management.

### List Messages
```http
GET /api/v1/messages/?session_id=123&type=assistant&model=claude-3-sonnet-20240229
```

**Parameters:**
- `session_id`: Filter by session
- `type`: Message type (user, assistant, summary)
- `model`: Filter by AI model
- `skip`, `limit`: Pagination

### Get Message Details
```http
GET /api/v1/messages/{message_id}
```

Retrieve detailed message information including tool usage and attachments.

### Get Message by UUID
```http
GET /api/v1/messages/uuid/{claude_uuid}
```

Find message by its original Claude UUID.

### Get Message Context
```http
GET /api/v1/messages/{message_id}/context?before=3&after=3
```

Get message with surrounding conversation context.

### Update Message Cost
```http
PATCH /api/v1/messages/{message_id}/cost
```

**Request Body:**
```json
{
  "cost_usd": 0.0123
}
```

### Batch Update Costs
```http
POST /api/v1/messages/batch-update-costs
```

Update costs for multiple messages in a single request.

## Project Management

Organize conversations by projects with statistics and management capabilities.

### List Projects
```http
GET /api/v1/projects/?skip=0&limit=50&search=web_development
```

### Get Project Details
```http
GET /api/v1/projects/{project_id}
```

### Create Project
```http
POST /api/v1/projects/
```

**Request Body:**
```json
{
  "name": "Web Development Project",
  "path": "/path/to/project",
  "description": "Frontend and backend development tasks"
}
```

### Update Project
```http
PATCH /api/v1/projects/{project_id}
```

### Delete Project
```http
DELETE /api/v1/projects/{project_id}?cascade=true
```

**Parameters:**
- `cascade`: Also delete associated sessions and messages

### Get Project Statistics
```http
GET /api/v1/projects/{project_id}/stats
```

Detailed project statistics including activity timeline.

## Data Ingestion

Batch ingestion endpoints for importing conversation data.

### Batch Message Ingestion
```http
POST /api/v1/ingest/batch
```

**Authentication Required**: Yes

**Request Body:**
```json
{
  "messages": [
    {
      "uuid": "msg_uuid_123",
      "type": "user",
      "sessionId": "session_456",
      "timestamp": "2025-08-05T10:30:00Z",
      "message": {
        "content": "Hello, can you help me with Python?"
      },
      "parentUuid": null,
      "model": null,
      "costUsd": null
    }
  ],
  "overwrite_mode": false
}
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_messages": 1,
    "created": 1,
    "updated": 0,
    "skipped": 0,
    "errors": 0
  },
  "message": "Successfully ingested 1 messages",
  "errors": []
}
```

### Single Message Ingestion
```http
POST /api/v1/ingest/message
```

Convenience endpoint for ingesting a single message.

### Ingestion Status
```http
GET /api/v1/ingest/status
```

Get ingestion system health and performance metrics.

## WebSocket Real-time Updates

Real-time updates for live statistics and session monitoring.

### Session-specific Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/session/session_123');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Session update:', data);
};
```

### Global Statistics Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stats');

ws.onmessage = function(event) {
    const stats = JSON.parse(event.data);
    updateDashboard(stats);
};
```

### Available WebSocket Endpoints
- `/ws/session/{session_id}` - Session-specific updates
- `/ws/stats/{session_id}` - Session statistics updates
- `/ws/stats` - Global statistics updates

### REST Endpoints for Live Data
```http
GET /ws/session/live     # Current live session statistics
GET /ws/stats/live       # Current live global statistics
GET /ws/connections      # WebSocket connection statistics
```

## Health & Status

System health monitoring and API status endpoints.

### API Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "timestamp": "2025-08-05T10:30:00Z"
}
```

### Root Endpoint
```http
GET /
```

Basic API information and version.

### Detailed Health Status
```http
GET /health
```

Comprehensive health check including database connectivity.

## Data Schemas

### Core Data Models

#### Message Schema
```json
{
  "id": "string",              // Database ID
  "uuid": "string",            // Claude message UUID
  "type": "user|assistant|summary",
  "session_id": "string",
  "content": "string",
  "timestamp": "datetime",
  "model": "string",
  "cost_usd": "number",
  "usage": {
    "input_tokens": "number",
    "output_tokens": "number"
  },
  "tool_use": [
    {
      "name": "string",
      "input": "object",
      "result": "object"
    }
  ]
}
```

#### Session Schema
```json
{
  "id": "string",
  "session_id": "string",
  "project_id": "string",
  "message_count": "number",
  "total_cost": "number",
  "started_at": "datetime",
  "ended_at": "datetime",
  "summary": "string"
}
```

#### Project Schema
```json
{
  "id": "string",
  "name": "string",
  "path": "string",
  "description": "string",
  "created_at": "datetime",
  "message_count": "number",
  "session_count": "number",
  "total_cost": "number"
}
```

### Pagination Response Schema
```json
{
  "items": ["array of items"],
  "total": "number",
  "skip": "number",
  "limit": "number",
  "has_more": "boolean"
}
```

## Error Handling

ClaudeLens uses standard HTTP status codes and provides detailed error information.

### Standard Error Response
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-08-05T10:30:00Z"
}
```

### Common Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing or invalid API key)
- `404` - Not Found
- `422` - Unprocessable Entity (validation errors)
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

API endpoints are rate-limited to ensure fair usage and system stability.

### Rate Limits
- **Read Operations**: 1000 requests per minute
- **Write Operations**: 100 requests per minute
- **Search Operations**: 60 requests per minute
- **Batch Ingestion**: 10 requests per minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1628097600
```

## Examples

### Complete Analytics Dashboard Setup

1. **Get Summary Statistics**:
```bash
curl "http://localhost:8000/api/v1/analytics/summary?time_range=30d"
```

2. **Fetch Cost Analytics**:
```bash
curl "http://localhost:8000/api/v1/analytics/costs?project_id=123"
```

3. **Get Tool Usage Details**:
```bash
curl "http://localhost:8000/api/v1/analytics/tools/detailed"
```

4. **Search Conversations**:
```bash
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python error handling",
    "highlight": true,
    "limit": 20
  }'
```

### CLI Integration Example

```python
import httpx

class ClaudeLensAPI:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key

    async def ingest_messages(self, messages: list):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/ingest/batch",
                json={"messages": messages},
                headers=self.headers
            )
            return response.json()

    async def search(self, query: str, **filters):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/search/",
                json={"query": query, "filters": filters}
            )
            return response.json()
```

### WebSocket Integration Example

```javascript
class ClaudeLensWebSocket {
    constructor(baseUrl) {
        this.baseUrl = baseUrl.replace('http', 'ws');
    }

    connectToStats(callback) {
        const ws = new WebSocket(`${this.baseUrl}/ws/stats`);

        ws.onmessage = (event) => {
            const stats = JSON.parse(event.data);
            callback(stats);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return ws;
    }
}

// Usage
const claudeLensWS = new ClaudeLensWebSocket('ws://localhost:8000');
const ws = claudeLensWS.connectToStats((stats) => {
    updateDashboard(stats);
});
```

---

For more detailed API documentation with interactive examples, visit the auto-generated documentation at `/docs` when running ClaudeLens locally.
