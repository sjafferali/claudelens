name: "Import/Export Feature Implementation PRP"
description: |
  Comprehensive implementation guide for ClaudeLens data import/export functionality with multi-format support,
  real-time progress tracking, and intelligent conflict resolution.

---

## Goal

**Feature Goal**: Implement a complete data import/export system that enables users to export conversation data in multiple formats (JSON, CSV, Markdown, PDF) and import previously exported data with intelligent conflict resolution and real-time progress tracking.

**Deliverable**: REST API endpoints for export/import operations, WebSocket-based progress tracking, background job processing for large datasets, and React UI components for user interaction.

**Success Definition**: Users can successfully export all or filtered conversations, download files in chosen format, import data with conflict resolution, and monitor progress in real-time via WebSocket updates.

## User Persona

**Target User**: ClaudeLens power users, data analysts, and administrators

**Use Case**: Exporting conversation history for backup, analysis in external tools, or migration; importing historical data from other systems or restoring backups

**User Journey**:
1. User navigates to Import/Export page
2. Selects export format and filters (or chooses file to import)
3. Initiates operation and sees real-time progress
4. Downloads completed export or reviews import results
5. Manages export history and re-downloads previous exports

**Pain Points Addressed**:
- Lack of data portability for backup and analysis
- No bulk import capability for historical conversations
- Missing GDPR compliance for data export requirements
- Unable to analyze conversations in external BI tools

## Why

- **Business Value**: Enables data portability, GDPR compliance, and platform migration capabilities
- **Integration**: Extends existing ingest and export endpoints with comprehensive multi-format support
- **Problems Solved**: Data lock-in concerns, compliance requirements, bulk data operations, external analysis needs

## What

Users will be able to:
- Export conversations in JSON, CSV, Markdown, and PDF formats
- Apply filters (date range, projects, tags, cost range) before export
- Import previously exported data with field mapping
- Resolve conflicts intelligently (skip, replace, merge strategies)
- Track progress in real-time via WebSocket
- Download exports from history for 30 days
- Encrypt exports with password protection

### Success Criteria

- [ ] All 4 export formats working with proper data structure
- [ ] File streaming for exports > 10MB without memory issues
- [ ] WebSocket progress updates every 0.5-2 seconds during operations
- [ ] Import validation catches format errors before processing
- [ ] Conflict resolution correctly handles duplicates
- [ ] Export history persists for 30 days with re-download capability
- [ ] Rate limiting prevents abuse (10 exports/hour, 5 imports/hour)

## All Needed Context

### Context Completeness Check

_This PRP contains all patterns, examples, and gotchas needed for an engineer unfamiliar with ClaudeLens to successfully implement the import/export feature._

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile
  why: Multipart file upload handling with UploadFile, validation patterns
  critical: Always use async file operations, validate size/type before processing

- url: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
  why: Streaming large files without memory overflow
  critical: Use AsyncGenerator for chunks, proper Content-Disposition headers

- file: backend/app/api/api_v1/endpoints/export.py
  why: Existing export endpoint pattern with StreamingResponse
  pattern: _generate_markdown_export async generator, header configuration
  gotcha: Must use async generator, not regular generator

- file: backend/app/api/api_v1/endpoints/ingest.py
  why: Batch processing pattern with validation and statistics
  pattern: BatchIngestRequest/Response schemas, error handling, stats tracking
  gotcha: Max 1000 items per batch, background task scheduling

- file: backend/app/api/api_v1/endpoints/websocket.py
  why: WebSocket implementation for real-time updates
  pattern: ConnectionManager, event broadcasting, progress tracking
  gotcha: Use WeakSet for connections, handle disconnections gracefully

- file: backend/app/services/websocket_manager.py
  why: WebSocket manager pattern for progress broadcasting
  pattern: broadcast_deletion_progress method structure
  gotcha: Throttle updates to avoid overwhelming clients

- file: frontend/src/components/DeletionProgressDialog.tsx
  why: Progress dialog UI pattern with WebSocket integration
  pattern: Stage-based progress, error handling, completion states
  gotcha: Cleanup WebSocket on unmount, handle connection failures

- file: frontend/src/hooks/useWebSocket.ts
  why: WebSocket hook pattern for real-time updates
  pattern: Auto-reconnection, message routing, connection state
  gotcha: Max 5 reconnect attempts, 3-second interval

- docfile: PRPs/ai_docs/streaming-file-operations.md
  why: Critical patterns for memory-efficient file operations
  section: All sections - streaming, validation, batch processing

- docfile: PRPs/contracts/import-export-api-contract.md
  why: Complete API specification with types and validation rules
  section: All endpoints and data models

- docfile: plans/uiredesign/mockups/import-export-page.html
  why: UI mockup showing component structure and interactions
  section: Tab navigation, format selection, progress indicators
```

### Current Codebase tree (key directories)

```bash
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/
│   │           ├── export.py           # Existing export endpoint
│   │           ├── ingest.py           # Batch ingest pattern
│   │           └── websocket.py        # WebSocket implementation
│   ├── models/
│   │   ├── session.py                  # Session model
│   │   └── message.py                  # Message model
│   ├── schemas/
│   │   ├── ingest.py                   # Ingest schemas
│   │   └── websocket.py                # WebSocket event schemas
│   └── services/
│       └── websocket_manager.py        # WebSocket manager
frontend/
├── src/
│   ├── api/
│   │   └── client.ts                   # API client with axios
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   └── LoadingSkeleton.tsx
│   │   └── ui/
│   │       ├── dialog.tsx
│   │       └── progress.tsx
│   ├── hooks/
│   │   └── useWebSocket.ts
│   └── pages/
│       └── Dashboard.tsx
```

### Desired Codebase tree with files to be added and responsibility

```bash
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/
│   │           ├── import_export.py    # NEW: Main import/export endpoints
│   ├── models/
│   │   ├── export_job.py              # NEW: Export job tracking model
│   │   └── import_job.py              # NEW: Import job tracking model
│   ├── schemas/
│   │   ├── export.py                   # NEW: Export request/response schemas
│   │   └── import.py                   # NEW: Import schemas with validation
│   ├── services/
│   │   ├── export_service.py          # NEW: Export business logic
│   │   ├── import_service.py          # NEW: Import with conflict resolution
│   │   └── file_service.py            # NEW: File handling and storage
│   └── utils/
│       ├── csv_generator.py           # NEW: CSV export generation
│       └── pdf_generator.py           # NEW: PDF export generation
frontend/
├── src/
│   ├── api/
│   │   └── import-export.ts           # NEW: Import/export API client
│   ├── components/
│   │   ├── import-export/
│   │   │   ├── ExportPanel.tsx        # NEW: Export configuration UI
│   │   │   ├── ImportPanel.tsx        # NEW: Import with drag-drop
│   │   │   ├── ExportHistory.tsx      # NEW: Export history table
│   │   │   ├── ConflictResolver.tsx   # NEW: Conflict resolution UI
│   │   │   └── ProgressDialog.tsx     # NEW: Import/export progress
│   ├── hooks/
│   │   ├── useExport.ts               # NEW: Export operations hook
│   │   └── useImport.ts               # NEW: Import operations hook
│   └── pages/
│       └── ImportExport.tsx           # NEW: Main import/export page
```

### Known Gotchas of our codebase & Library Quirks

```python
# CRITICAL: Motor (MongoDB async driver) has connection pool limits
# Max 100 connections by default, batch operations to avoid exhaustion

# CRITICAL: FastAPI UploadFile reads entire file into memory if not handled properly
# Always stream in chunks: await file.read(8192)  # 8KB chunks

# CRITICAL: WebSocket disconnections must be handled gracefully
# Use WeakSet for connections to avoid memory leaks

# CRITICAL: Pydantic v2 field_validator syntax changed
# Use @field_validator('field_name', mode='before') not @validator

# CRITICAL: Frontend WebSocket reconnection can cause duplicate messages
# Track message IDs to deduplicate on client side

# CRITICAL: TanStack Query v5 syntax differs from v4
# Use queryKey array format, not string
```

## Implementation Blueprint

### Data models and structure

Create the core data models for tracking import/export jobs with proper validation.

```python
# backend/app/models/export_job.py
from datetime import datetime, UTC
from typing import Optional, Literal
from bson import ObjectId
from pydantic import BaseModel, Field
from app.models.base import PyObjectId

class ExportJob(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    status: Literal['queued', 'processing', 'completed', 'failed', 'cancelled']
    format: Literal['json', 'csv', 'markdown', 'pdf']
    filters: dict = Field(default_factory=dict)
    options: dict = Field(default_factory=dict)
    progress: dict = Field(default_factory=lambda: {
        "current": 0, "total": 0, "percentage": 0
    })
    file_info: Optional[dict] = None
    statistics: dict = Field(default_factory=dict)
    errors: list[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: datetime  # 30 days from creation

# backend/app/schemas/export.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Literal

class CreateExportRequest(BaseModel):
    format: Literal['json', 'csv', 'markdown', 'pdf']
    filters: Optional[dict] = Field(default_factory=dict)
    options: Optional[dict] = Field(default_factory=dict)

    @field_validator('options', mode='before')
    @classmethod
    def validate_options(cls, v):
        if v and v.get('splitSizeMb'):
            if not 1 <= v['splitSizeMb'] <= 500:
                raise ValueError('splitSizeMb must be between 1 and 500')
        return v

class ExportStatusResponse(BaseModel):
    job_id: str = Field(alias="jobId")
    status: str
    progress: Optional[dict] = None
    file_info: Optional[dict] = Field(None, alias="fileInfo")
    errors: list[dict] = Field(default_factory=list)
    created_at: str = Field(alias="createdAt")
    expires_at: str = Field(alias="expiresAt")

    class Config:
        populate_by_name = True
```

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE backend/app/models/export_job.py and import_job.py
  - IMPLEMENT: ExportJob, ImportJob models with PyObjectId
  - FOLLOW pattern: backend/app/models/session.py (field types, UTC datetime)
  - NAMING: PascalCase for classes, snake_case for fields
  - PLACEMENT: Models directory with other database models
  - GOTCHA: Use PyObjectId for MongoDB _id field compatibility

Task 2: CREATE backend/app/schemas/export.py and import.py
  - IMPLEMENT: Request/Response schemas matching API contract
  - FOLLOW pattern: backend/app/schemas/ingest.py (validation, field_validator)
  - NAMING: CreateExportRequest, ExportStatusResponse, etc.
  - DEPENDENCIES: Import models from Task 1
  - PLACEMENT: Schemas directory following existing organization
  - CRITICAL: Use field_validator with mode='before' for Pydantic v2

Task 3: CREATE backend/app/services/file_service.py
  - IMPLEMENT: FileService class for streaming operations
  - FOLLOW pattern: PRPs/ai_docs/streaming-file-operations.md
  - NAMING: async def save_upload_streaming, generate_export_file
  - CRITICAL: 8KB chunk size for file I/O, use aiofiles for async
  - PLACEMENT: Services directory with dependency injection pattern

Task 4: CREATE backend/app/services/export_service.py
  - IMPLEMENT: ExportService with format generators
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/export.py (_generate_markdown_export)
  - NAMING: async def create_export_job, process_export, generate_json_export
  - DEPENDENCIES: FileService from Task 3, models from Task 1
  - CRITICAL: Use AsyncGenerator for streaming, batch database queries

Task 5: CREATE backend/app/services/import_service.py
  - IMPLEMENT: ImportService with conflict resolution
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/ingest.py (batch processing)
  - NAMING: async def validate_import_file, detect_conflicts, execute_import
  - DEPENDENCIES: FileService from Task 3, schemas from Task 2
  - CRITICAL: Max 1000 items per batch, implement rollback mechanism

Task 6: CREATE backend/app/api/api_v1/endpoints/import_export.py
  - IMPLEMENT: All endpoints from API contract
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/export.py (StreamingResponse)
  - NAMING: POST /export, GET /export/{job_id}/status, etc.
  - DEPENDENCIES: Services from Tasks 4-5, schemas from Task 2
  - PLACEMENT: API endpoints directory with custom router
  - CRITICAL: Use BackgroundTasks for async processing

Task 7: MODIFY backend/app/api/api_v1/api.py
  - INTEGRATE: Register new import_export router
  - FIND pattern: Existing router.include_router calls
  - ADD: router.include_router(import_export.router, prefix="/api/v1", tags=["import-export"])
  - PRESERVE: All existing router registrations

Task 8: CREATE backend/app/utils/csv_generator.py and pdf_generator.py
  - IMPLEMENT: Format-specific generators
  - FOLLOW pattern: PRPs/ai_docs/streaming-file-operations.md (CSV section)
  - NAMING: async def generate_csv_streaming, generate_pdf
  - CRITICAL: Use csv.writer with StringIO buffer, ReportLab for PDF
  - PLACEMENT: New utils directory for format generators

Task 9: MODIFY backend/app/schemas/websocket.py
  - ADD: ImportProgressEvent, ExportProgressEvent schemas
  - FOLLOW pattern: Existing DeletionProgressEvent
  - NAMING: Follow existing event naming conventions
  - CRITICAL: Include all fields from API contract

Task 10: MODIFY backend/app/services/websocket_manager.py
  - ADD: broadcast_import_progress, broadcast_export_progress methods
  - FOLLOW pattern: Existing broadcast_deletion_progress
  - CRITICAL: Throttle updates to max 2/second

Task 11: CREATE frontend/src/api/import-export.ts
  - IMPLEMENT: API client functions for all endpoints
  - FOLLOW pattern: frontend/src/api/client.ts (axios configuration)
  - NAMING: exportConversations, getExportStatus, importFile, etc.
  - CRITICAL: Handle multipart/form-data for file uploads

Task 12: CREATE frontend/src/hooks/useExport.ts and useImport.ts
  - IMPLEMENT: TanStack Query hooks for operations
  - FOLLOW pattern: frontend/src/hooks/useProjects.ts
  - NAMING: useCreateExport, useExportStatus, useImportFile
  - DEPENDENCIES: API functions from Task 11
  - CRITICAL: Use queryKey arrays, not strings

Task 13: CREATE frontend/src/components/import-export/*.tsx
  - IMPLEMENT: All UI components from mockup
  - FOLLOW pattern: frontend/src/components/DeletionProgressDialog.tsx
  - NAMING: ExportPanel, ImportPanel, ConflictResolver, etc.
  - DEPENDENCIES: Hooks from Task 12, UI components
  - CRITICAL: Handle WebSocket cleanup on unmount

Task 14: CREATE frontend/src/pages/ImportExport.tsx
  - IMPLEMENT: Main page with tab navigation
  - FOLLOW pattern: plans/uiredesign/mockups/import-export-page.html
  - NAMING: ImportExportPage component
  - DEPENDENCIES: Components from Task 13
  - PLACEMENT: Pages directory with routing

Task 15: MODIFY frontend/src/App.tsx
  - ADD: Route for import/export page
  - FIND pattern: Existing route definitions
  - ADD: <Route path="/import-export" element={<ImportExportPage />} />
  - PRESERVE: All existing routes

Task 16: CREATE tests for all new backend services
  - IMPLEMENT: Unit tests for export/import services
  - FOLLOW pattern: backend/tests/test_endpoints_ingest.py
  - NAMING: test_export_service.py, test_import_service.py
  - COVERAGE: All service methods, error cases, edge cases
  - CRITICAL: Mock file I/O and database operations

Task 17: CREATE tests for frontend components
  - IMPLEMENT: Component tests with Vitest
  - FOLLOW pattern: frontend/src/components/__tests__/*.test.tsx
  - NAMING: ExportPanel.test.tsx, ImportPanel.test.tsx
  - COVERAGE: User interactions, error states, loading states
  - CRITICAL: Mock WebSocket and API calls
```

### Implementation Patterns & Key Details

```python
# Service method pattern for export generation
async def generate_json_export(
    self,
    job_id: str,
    session_ids: list[str],
    progress_callback: Callable
) -> AsyncGenerator[bytes, None]:
    """
    PATTERN: Streaming generator with progress tracking
    GOTCHA: Must use AsyncGenerator, not Generator
    CRITICAL: Batch database queries to avoid connection pool exhaustion
    """
    yield b'{"conversations":['

    first = True
    tracker = ExportProgressTracker(job_id, len(session_ids), progress_callback)

    # Process in batches of 100 to avoid connection pool exhaustion
    for batch_start in range(0, len(session_ids), 100):
        batch_ids = session_ids[batch_start:batch_start + 100]

        # Batch query for efficiency
        sessions = await self.db.sessions.find(
            {"_id": {"$in": batch_ids}}
        ).to_list(length=100)

        for session in sessions:
            if not first:
                yield b','
            first = False

            # Include messages for each session
            messages = await self.db.messages.find(
                {"session_id": str(session["_id"])}
            ).to_list(length=None)

            export_data = {
                "id": str(session["_id"]),
                "title": session.get("title", ""),
                "messages": [self._format_message(m) for m in messages],
                # ... other fields
            }

            yield json.dumps(export_data).encode('utf-8')
            await tracker.increment()

    yield b']}'
    await tracker.complete()

# WebSocket progress pattern
async def broadcast_export_progress(
    self,
    job_id: str,
    current: int,
    total: int,
    message: str = "",
    completed: bool = False,
    error: Optional[str] = None
) -> None:
    """
    PATTERN: Throttled progress broadcasting
    CRITICAL: Check time since last update to avoid overwhelming clients
    """
    event = {
        "type": "export_progress",
        "job_id": job_id,
        "progress": {
            "current": current,
            "total": total,
            "percentage": round((current / total * 100) if total > 0 else 0, 2)
        },
        "message": message,
        "completed": completed,
        "error": error,
        "timestamp": datetime.now(UTC).isoformat()
    }

    # Broadcast to all connections watching this export
    await self._broadcast_to_connections(
        self.export_connections.get(job_id, set()),
        event
    )

# Frontend WebSocket hook usage
const useExportProgress = (exportId: string | null) => {
  const [progress, setProgress] = useState<ExportProgress | null>(null);

  const { sendMessage, lastMessage } = useWebSocket(
    exportId ? `/ws/export/${exportId}` : null,
    {
      onOpen: () => {
        sendMessage({ type: 'subscribe', channel: 'export', jobId: exportId });
      },
      shouldReconnect: () => true,
      reconnectInterval: 3000,
      reconnectAttempts: 5,
    }
  );

  useEffect(() => {
    if (lastMessage?.type === 'export_progress') {
      setProgress(lastMessage as ExportProgress);
    }
  }, [lastMessage]);

  return progress;
};
```

### Integration Points

```yaml
DATABASE:
  - collections: "export_jobs", "import_jobs"
  - indexes:
    - "CREATE INDEX idx_export_user_created ON export_jobs(user_id, created_at DESC)"
    - "CREATE INDEX idx_export_expires ON export_jobs(expires_at)"
    - "CREATE INDEX idx_import_user_created ON import_jobs(user_id, created_at DESC)"

CONFIG:
  - add to: backend/app/core/config.py
  - pattern: |
      MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', '104857600'))  # 100MB
      EXPORT_EXPIRY_DAYS = int(os.getenv('EXPORT_EXPIRY_DAYS', '30'))
      TEMP_DIR = os.getenv('TEMP_DIR', '/tmp/claudelens')

ROUTES:
  - add to: backend/app/api/api_v1/api.py
  - pattern: |
      from app.api.api_v1.endpoints import import_export
      api_router.include_router(
          import_export.router,
          prefix="",
          tags=["import-export"]
      )

FRONTEND_ROUTES:
  - add to: frontend/src/App.tsx
  - pattern: |
      import { ImportExportPage } from './pages/ImportExport';
      <Route path="/import-export" element={<ImportExportPage />} />

SIDEBAR:
  - add to: frontend/src/components/layout/Sidebar.tsx
  - pattern: |
      {
        path: '/import-export',
        label: 'Import/Export',
        icon: Download,
      }
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Backend validation
cd backend
poetry run ruff check app/api/api_v1/endpoints/import_export.py --fix
poetry run ruff check app/services/export_service.py app/services/import_service.py --fix
poetry run ruff check app/models/export_job.py app/models/import_job.py --fix
poetry run ruff check app/schemas/export.py app/schemas/import.py --fix
poetry run mypy app/services/export_service.py app/services/import_service.py
poetry run ruff format app/

# Frontend validation
cd ../frontend
npm run lint
npm run type-check
npm run format:check

# Expected: Zero errors. Fix any issues before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Backend tests
cd backend
poetry run pytest tests/test_export_service.py -v
poetry run pytest tests/test_import_service.py -v
poetry run pytest tests/test_endpoints_import_export.py -v

# Test with coverage
poetry run pytest tests/ --cov=app.services --cov=app.api.api_v1.endpoints.import_export --cov-report=term-missing

# Frontend tests
cd ../frontend
npm test -- src/components/import-export/
npm test -- src/hooks/useExport.test.ts src/hooks/useImport.test.ts
npm run test:coverage

# Expected: All tests pass with >80% coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Start backend with test database
cd backend
docker compose -f docker-compose.test.yml up -d
poetry run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 5

# Test export endpoint
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "format": "json",
    "filters": {
      "dateRange": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-12-31T23:59:59Z"
      }
    }
  }' | jq .

# Test import with file
curl -X POST http://localhost:8000/api/v1/import/validate \
  -H "X-API-Key: test-api-key" \
  -F "file=@test_export.json" | jq .

# Test WebSocket connection
wscat -c ws://localhost:8000/ws \
  -H "X-API-Key: test-api-key" \
  -x '{"type": "subscribe", "channel": "export", "jobId": "test_job_123"}'

# Test file download (replace JOB_ID with actual)
curl -X GET http://localhost:8000/api/v1/export/{JOB_ID}/download \
  -H "X-API-Key: test-api-key" \
  -o downloaded_export.json

# Cleanup
kill $BACKEND_PID
docker compose -f docker-compose.test.yml down

# Expected: All endpoints return proper responses, WebSocket connects
```

### Level 4: End-to-End Testing

```bash
# Full stack test
cd /path/to/claudelens
docker compose up -d

# Wait for services
sleep 10

# Run E2E tests with Playwright
cd frontend
npx playwright test tests/e2e/import-export.spec.ts

# Test large file handling (create 50MB test file)
python -c "
import json
data = {'conversations': [{'id': str(i), 'messages': ['test'] * 100} for i in range(10000)]}
with open('large_test.json', 'w') as f:
    json.dump(data, f)
"

# Upload large file
curl -X POST http://localhost:8000/api/v1/import/validate \
  -H "X-API-Key: your-api-key" \
  -F "file=@large_test.json" \
  --max-time 60 | jq .

# Monitor memory usage during export
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"format": "csv"}' &

# Check memory (should stay under 200MB for export service)
docker stats claudelens --no-stream

# Test rate limiting (should fail after 10 requests)
for i in {1..15}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/v1/export \
    -H "Content-Type: application/json" \
    -H "X-API-Key: your-api-key" \
    -d '{"format": "json"}' \
    -w "\nStatus: %{http_code}\n"
  sleep 1
done

# Expected: Memory stays low, rate limiting kicks in after 10 requests
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] Backend tests pass: `poetry run pytest tests/ -v`
- [ ] Frontend tests pass: `npm test`
- [ ] No linting errors: `poetry run ruff check app/` and `npm run lint`
- [ ] No type errors: `poetry run mypy app/` and `npm run type-check`
- [ ] WebSocket connections work and reconnect properly
- [ ] File uploads handle sizes up to 100MB without OOM
- [ ] Exports stream properly for files > 10MB

### Feature Validation

- [ ] JSON export includes all conversation data with proper structure
- [ ] CSV export generates valid spreadsheet-compatible files
- [ ] Markdown export is human-readable with proper formatting
- [ ] PDF export creates print-ready documents
- [ ] Import validates file format and shows errors
- [ ] Conflict resolution correctly identifies duplicates
- [ ] Progress updates arrive every 0.5-2 seconds via WebSocket
- [ ] Export history persists and allows re-download
- [ ] Rate limiting prevents abuse (10 exports/hour, 5 imports/hour)

### Code Quality Validation

- [ ] Follows existing patterns from export.py and ingest.py
- [ ] Uses AsyncGenerator for streaming, not regular generators
- [ ] Implements proper error handling with try-finally for cleanup
- [ ] WebSocket connections use WeakSet to prevent memory leaks
- [ ] Database operations batch queries (max 100 items)
- [ ] File operations use 8KB chunks for streaming
- [ ] All new files placed in correct directories per structure
- [ ] Import statements follow existing conventions

### Documentation & Deployment

- [ ] API endpoints match specification in import-export-api-contract.md
- [ ] Environment variables documented (MAX_UPLOAD_SIZE, EXPORT_EXPIRY_DAYS)
- [ ] WebSocket events follow existing schema patterns
- [ ] UI components follow mockup design
- [ ] Error messages are user-friendly and actionable

---

## Anti-Patterns to Avoid

- ❌ Don't load entire files into memory - always stream
- ❌ Don't skip chunk size limits - use 8KB for files, 100 for DB
- ❌ Don't forget to cleanup temp files - use try-finally
- ❌ Don't send WebSocket updates too frequently - throttle to 2/sec
- ❌ Don't use synchronous file operations - always use aiofiles
- ❌ Don't ignore connection pool limits - batch database operations
- ❌ Don't forget WebSocket reconnection handling - max 5 attempts
- ❌ Don't hardcode file paths - use config for temp directory

## Confidence Score

**Implementation Success Likelihood: 9/10**

This PRP provides comprehensive implementation guidance with:
- Complete API specifications and data models
- Detailed task breakdown with dependencies
- Specific code patterns from existing codebase
- Critical gotchas and library quirks documented
- Full validation suite from syntax to E2E testing
- Memory-efficient streaming patterns for large files

The single point deducted is for potential complexity in PDF generation which may require additional iteration based on specific formatting requirements.
