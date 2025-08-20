# ClaudeLens MCP Implementation Details

## Technical Architecture

### Overview

The ClaudeLens MCP Server is built using the FastMCP framework, providing a high-level abstraction over the Model Context Protocol. It acts as a bridge between Claude Desktop and the ClaudeLens backend API.

### Component Architecture

```
┌──────────────────────────────────────────────┐
│                Claude Desktop                 │
│  ┌──────────────────────────────────────┐    │
│  │         MCP Client Protocol          │    │
│  └──────────────────────────────────────┘    │
└────────────────┬─────────────────────────────┘
                 │ stdio/JSON-RPC
                 ↓
┌──────────────────────────────────────────────┐
│            MCP Server (FastMCP)               │
│  ┌──────────────────────────────────────┐    │
│  │           Lifespan Manager           │    │
│  ├──────────────────────────────────────┤    │
│  │      Resources    │    Tools         │    │
│  ├──────────────────────────────────────┤    │
│  │           Prompts Manager            │    │
│  └──────────────────────────────────────┘    │
└────────────────┬─────────────────────────────┘
                 │ HTTP/REST
                 ↓
┌──────────────────────────────────────────────┐
│          ClaudeLens API Client               │
│  ┌──────────────────────────────────────┐    │
│  │      Connection Pool (httpx)         │    │
│  ├──────────────────────────────────────┤    │
│  │      Request/Response Handler        │    │
│  └──────────────────────────────────────┘    │
└────────────────┬─────────────────────────────┘
                 │ HTTP
                 ↓
┌──────────────────────────────────────────────┐
│         ClaudeLens Backend (FastAPI)         │
│  ┌──────────────────────────────────────┐    │
│  │    Export Endpoints (Enhanced)       │    │
│  ├──────────────────────────────────────┤    │
│  │    Core API Endpoints                │    │
│  └──────────────────────────────────────┘    │
└────────────────┬─────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────┐
│              MongoDB Database                │
└──────────────────────────────────────────────┘
```

## Core Components

### 1. MCP Server (`claudelens_mcp/server.py`)

The main server implementation using FastMCP framework.

#### Initialization
```python
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with API client."""
    api_client = ClaudeLensAPIClient(
        base_url=CLAUDELENS_API_URL,
        api_key=CLAUDELENS_API_KEY
    )
    try:
        yield AppContext(api_client=api_client)
    finally:
        await api_client.close()

mcp = FastMCP(
    "ClaudeLens MCP",
    instructions="...",
    lifespan=app_lifespan
)
```

#### Resource Implementation
Resources are decorated functions that return JSON-serializable data:

```python
@mcp.resource("claudelens://sessions/{session_id}")
async def get_session_resource(ctx: Context, session_id: str) -> str:
    api_client = ctx.request_context.lifespan_context.api_client
    session = await api_client.get_session(session_id)
    return json.dumps(session, indent=2, default=str)
```

#### Tool Implementation
Tools use Pydantic models for parameters and perform actions:

```python
class SearchParameters(BaseModel):
    query: str = Field(description="Search query text")
    limit: int = Field(default=20, description="Max results")

@mcp.tool()
async def search_messages(ctx: Context, params: SearchParameters) -> str:
    api_client = ctx.request_context.lifespan_context.api_client
    result = await api_client.search_messages(
        query=params.query,
        limit=params.limit
    )
    return json.dumps(result, indent=2, default=str)
```

### 2. API Client (`claudelens_mcp/api_client.py`)

Async HTTP client for ClaudeLens backend communication.

#### Features
- Connection pooling with httpx
- Automatic retry logic
- Type-safe request/response handling
- Optional authentication support

#### Implementation Pattern
```python
class ClaudeLensAPIClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_v1_url = f"{self.base_url}/api/v1"
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def list_sessions(self, **params) -> Dict[str, Any]:
        response = await self.client.get(
            f"{self.api_v1_url}/sessions",
            params=params
        )
        response.raise_for_status()
        return response.json()
```

### 3. Backend Export Endpoints (`backend/app/api/api_v1/endpoints/export.py`)

Enhanced endpoints optimized for MCP consumption.

#### Session Export Endpoint
```python
@router.get("/sessions/{session_id}/export")
async def export_session_for_mcp(
    session_id: str,
    db: CommonDeps,
    format: str = "json",
    include_metadata: bool = True,
    include_costs: bool = True,
    flatten_threads: bool = False
) -> Union[Dict[str, Any], StreamingResponse]:
    # Process messages into structured format
    # Build thread relationships
    # Return optimized data structure
```

#### Structured Conversations Endpoint
```python
@router.get("/conversations/structured")
async def get_structured_conversations(
    db: CommonDeps,
    project_id: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    # Group sessions by project
    # Create hierarchical structure
    # Return organized data
```

## Data Flow

### 1. Resource Access Flow
```
Claude Desktop → MCP Server → API Client → Backend → MongoDB
                     ↓            ↓           ↓         ↓
              Parse URI    HTTP Request   Query DB   Return Data
                     ↑            ↑           ↑         ↑
              JSON Response  Parse Response  Format  Raw Data
```

### 2. Tool Execution Flow
```
Claude Desktop → MCP Server → Validate Parameters → API Client
                     ↓                                  ↓
              Tool Function                      Backend API Call
                     ↓                                  ↓
              Process Result ← Format Response ← API Response
```

### 3. Search Flow
```
User Query → MCP Tool → API Client → Search Endpoint
                ↓           ↓              ↓
          Parse Params  HTTP POST    MongoDB Text Search
                ↑           ↑              ↑
          Format Results  Response   Aggregation Pipeline
```

## Message Processing

### Content Extraction
Messages in ClaudeLens can have various formats. The MCP server handles all formats:

```python
def extract_message_content(msg):
    if msg.get("message"):
        message_data = msg["message"]
        if isinstance(message_data, dict):
            if "text" in message_data:
                return message_data["text"]
            elif "content" in message_data:
                content = message_data["content"]
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Extract from content blocks
                    text_parts = []
                    for block in content:
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    return "\n".join(text_parts)
    return str(message_data)
```

### Thread Navigation
The server maintains parent-child relationships for branching conversations:

```python
# Build message map for thread structure
message_map = {}
for msg in messages:
    if msg.get("uuid"):
        message_map[msg["uuid"]] = processed_msg

# Build parent-child relationships
for msg in processed_messages:
    if msg.get("parent_uuid") and msg["parent_uuid"] in message_map:
        parent = message_map[msg["parent_uuid"]]
        if "children" not in parent:
            parent["children"] = []
        parent["children"].append(msg["uuid"])
```

## Search Implementation

### MongoDB Text Search
The backend uses MongoDB text indexes for efficient searching:

```python
# Text index creation
await db.messages.create_index([("message.text", "text")])

# Search aggregation pipeline
pipeline = [
    {"$match": {"$text": {"$search": query}}},
    {"$addFields": {"score": {"$meta": "textScore"}}},
    {"$sort": {"score": -1}},
    {"$skip": skip},
    {"$limit": limit}
]
```

### Regex Search Support
For advanced pattern matching:

```python
if is_regex:
    pipeline = [
        {"$match": {
            "message.text": {"$regex": query, "$options": "i"}
        }},
        {"$skip": skip},
        {"$limit": limit}
    ]
```

## Performance Optimizations

### 1. Connection Pooling
The API client maintains a connection pool for efficient HTTP communication:

```python
self.client = httpx.AsyncClient(
    headers=self.headers,
    timeout=30.0,
    limits=httpx.Limits(
        max_keepalive_connections=10,
        max_connections=20
    )
)
```

### 2. Pagination
All list operations support pagination to handle large datasets:

```python
async def list_sessions(
    self,
    skip: int = 0,
    limit: int = 20
) -> Dict[str, Any]:
    # Paginated retrieval
```

### 3. Selective Field Retrieval
Export endpoints allow selective inclusion of data:

```python
include_metadata: bool = True
include_costs: bool = True
flatten_threads: bool = False
```

### 4. Streaming Exports
Large exports can be streamed to avoid memory issues:

```python
return StreamingResponse(
    _generate_markdown_export(export_data),
    media_type="text/markdown"
)
```

## Error Handling

### Graceful Degradation
All operations include error handling with informative messages:

```python
try:
    result = await api_client.operation()
    return json.dumps(result)
except Exception as e:
    return f"Error performing operation: {str(e)}"
```

### Validation
Input validation using Pydantic models:

```python
class SearchParameters(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(ge=1, le=100, default=20)
```

## Security Considerations

### 1. Authentication
Optional API key support:

```python
if api_key:
    self.headers["X-API-Key"] = api_key
```

### 2. Input Sanitization
All user inputs are validated and sanitized:

```python
if not ObjectId.is_valid(session_id):
    raise HTTPException(status_code=400, detail="Invalid session ID")
```

### 3. Rate Limiting
Backend implements rate limiting:

```python
app.add_middleware(RateLimitMiddleware, calls=500, period=60)
```

## Testing

### Test Suite (`test_mcp_server.py`)
Comprehensive testing of all components:

1. **Backend Connectivity**
```python
response = await client.get(f"{api_url}/health")
```

2. **API Client Testing**
```python
sessions_result = await client.list_sessions(limit=5)
```

3. **MCP Server Validation**
```python
from claudelens_mcp.server import mcp
# Validate resources, tools, prompts
```

## Configuration

### Environment Variables
```env
CLAUDELENS_API_URL=http://localhost:8080
CLAUDELENS_API_KEY=optional-api-key
```

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "claudelens": {
      "command": "uv",
      "args": ["run", "claudelens-mcp"],
      "env": {
        "CLAUDELENS_API_URL": "http://localhost:8080"
      }
    }
  }
}
```

## Future Enhancements

### Planned Features
1. **WebSocket Support** - Real-time session updates
2. **Caching Layer** - Redis integration for frequently accessed data
3. **Advanced Analytics** - ML-based pattern recognition
4. **Batch Operations** - Bulk export and processing
5. **Custom Filters** - User-defined search filters

### Extension Points
The architecture supports easy extension:

- New resources: Add `@mcp.resource()` decorated functions
- New tools: Add `@mcp.tool()` decorated functions
- New endpoints: Extend API client and backend
- Custom prompts: Add `@mcp.prompt()` templates

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### MCP Protocol Inspection
```bash
# Run server with debug output
PYTHONPATH=. python -m mcp.server.stdio claudelens_mcp.server:mcp
```

### API Request Monitoring
```python
# In API client
logger.debug(f"Request: {method} {url}")
logger.debug(f"Response: {response.status_code}")
```

## Conclusion

The ClaudeLens MCP implementation provides a robust, scalable bridge between Claude Desktop and the ClaudeLens analytics platform. The modular architecture ensures easy maintenance and extension while maintaining high performance and reliability.
