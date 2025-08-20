name: "Import/Export Feature Implementation"
description: |
  Comprehensive implementation of data import/export functionality for ClaudeLens, enabling users to export conversations in multiple formats and import data from external sources with conflict resolution and progress tracking.

---

## Goal

**Feature Goal**: Implement a fully functional import/export system that allows users to export their conversation data in multiple formats (JSON, CSV, Markdown, PDF) and import data with validation, conflict resolution, and real-time progress tracking.

**Deliverable**: Complete import/export feature with React frontend UI, FastAPI backend endpoints, file upload/download capabilities, background job processing, and WebSocket-based progress tracking.

**Success Definition**: Users can successfully export all or filtered conversations in their chosen format, import data from files with proper validation and conflict handling, view export history, and track progress of long-running operations in real-time.

## User Persona

**Target User**: ClaudeLens users who need to:
- Backup their conversation data
- Migrate data between instances
- Analyze conversations in external tools
- Share conversation history with team members
- Archive conversations for compliance

**Use Case**: Export conversation data for backup, analysis, or migration; Import previously exported data or data from other sources

**User Journey**:
1. User navigates to Import/Export page
2. Selects export tab and configures export options (format, filters, date range)
3. Reviews preview of data to be exported
4. Initiates export and monitors progress
5. Downloads completed export file
6. For import: uploads file, maps fields, resolves conflicts, monitors import progress

**Pain Points Addressed**:
- No current UI for data export/import
- Limited export format options
- No batch export capabilities
- No import functionality
- No progress tracking for long operations

## Why

- **Data Portability**: Users need control over their data for backup, analysis, and migration
- **Compliance**: Meet GDPR data portability requirements
- **Integration**: Enable data exchange with external tools and services
- **Business Continuity**: Protect against data loss through regular exports
- **Team Collaboration**: Share conversation data across teams and instances

## What

### Functional Requirements
- Export conversations in JSON, CSV, Markdown, and PDF formats
- Import data from JSON and CSV files
- Filter exports by date range, projects, models, and tags
- Field mapping for imports with smart defaults
- Conflict resolution strategies (skip, replace, merge)
- Real-time progress tracking via WebSocket
- Export history with download links
- File validation and security scanning
- Bulk selection for export
- Compression for large exports

### Success Criteria
- [ ] Export page UI matches mockup design
- [ ] All four export formats (JSON, CSV, Markdown, PDF) working
- [ ] Import supports JSON and CSV with validation
- [ ] Progress tracking shows real-time updates
- [ ] Export history persisted and downloadable
- [ ] Conflict resolution works for duplicate imports
- [ ] File uploads validated and secure
- [ ] Large exports handled efficiently with streaming
- [ ] Dark mode support implemented

## All Needed Context

### Context Completeness Check

_This PRP contains all file paths, API patterns, UI components, and external documentation needed for implementation without prior knowledge of the ClaudeLens codebase._

### Documentation & References

```yaml
# MUST READ - Include these in your context window

- url: https://react-dropzone.js.org/
  why: File upload component for React - drag & drop functionality
  critical: useDropzone hook API, file validation, styling patterns

- url: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
  why: Security best practices for file upload implementation
  critical: File type validation, size limits, content validation

- url: https://fastapi.tiangolo.com/tutorial/request-files/
  why: FastAPI file upload patterns for import endpoint
  critical: UploadFile usage, streaming for large files, async patterns

- file: /Users/sjafferali/github/personal/claudelens/backend/app/api/api_v1/endpoints/export.py
  why: Existing export endpoint patterns - JSON/Markdown export already implemented
  pattern: StreamingResponse for file downloads, export data formatting
  gotcha: Export endpoint exists but only for single sessions, needs bulk export

- file: /Users/sjafferali/github/personal/claudelens/backend/app/services/ingest.py
  why: Bulk data processing patterns for import functionality
  pattern: Batch processing, deduplication, content hashing, stats tracking
  gotcha: Processes up to 1000 messages per batch, uses contentHash for deduplication

- file: /Users/sjafferali/github/personal/claudelens/frontend/src/components/DeletionProgressDialog.tsx
  why: WebSocket progress tracking pattern for long operations
  pattern: Real-time progress updates, stage tracking, error handling
  gotcha: Uses custom WebSocket hook for connection management

- file: /Users/sjafferali/github/personal/claudelens/plans/uiredesign/mockups/import-export-page.html
  why: Complete UI mockup with all components and interactions
  pattern: Tab navigation, file drop zone, progress bars, conflict resolution UI
  gotcha: Static HTML - needs conversion to React components with Tailwind

- file: /Users/sjafferali/github/personal/claudelens/plans/uiredesign/mockups/import-export-data-formats.md
  why: Complete data format specifications for all import/export formats
  pattern: JSON structure, CSV format, field mapping rules, validation rules
  gotcha: Size limitations per format type

- docfile: PRPs/ai_docs/mongodb-bulk-operations.md
  why: MongoDB bulk write patterns for efficient import operations
  section: Bulk Write Operations

- docfile: PRPs/ai_docs/react-query-patterns.md
  why: React Query usage for data fetching and mutations in ClaudeLens
  section: Mutation Patterns
```

### Current Codebase tree (relevant sections)

```bash
claudelens/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── api_v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── export.py        # Existing single-session export
│   │   │       │   ├── ingest.py        # Message ingestion endpoint
│   │   │       │   └── sessions.py      # Session endpoints
│   │   │       └── api.py               # Router registration
│   │   ├── models/
│   │   │   ├── session.py               # Session model
│   │   │   ├── message.py               # Message model
│   │   │   └── project.py               # Project model
│   │   ├── services/
│   │   │   ├── ingest.py                # Bulk data processing
│   │   │   ├── websocket_manager.py     # WebSocket connections
│   │   │   └── validation.py            # Message validation
│   │   └── schemas/
│   │       └── ingest.py                # Pydantic schemas
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts                # API client class
│   │   ├── components/
│   │   │   ├── common/                  # Button, Card, etc.
│   │   │   ├── ui/                      # dialog, progress, select
│   │   │   └── DeletionProgressDialog.tsx # Progress pattern
│   │   ├── pages/
│   │   │   └── Sessions.tsx             # Sessions page reference
│   │   ├── store/
│   │   │   └── index.ts                 # Zustand store
│   │   └── App.tsx                      # Routes
│   └── package.json
└── plans/
    └── uiredesign/
        └── mockups/
            ├── import-export-page.html
            └── import-export-data-formats.md
```

### Desired Codebase tree with files to be added and responsibility of file

```bash
claudelens/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── api_v1/
│   │   │       └── endpoints/
│   │   │           ├── import_export.py  # NEW: Combined import/export endpoints
│   │   │           └── export_history.py # NEW: Export history management
│   │   ├── services/
│   │   │   ├── import_service.py        # NEW: Import processing logic
│   │   │   ├── export_service.py        # NEW: Bulk export logic
│   │   │   └── file_validation.py       # NEW: File security/validation
│   │   ├── schemas/
│   │   │   ├── import_export.py         # NEW: Import/export schemas
│   │   │   └── export_formats.py        # NEW: Format-specific schemas
│   │   └── utils/
│   │       ├── csv_converter.py         # NEW: CSV conversion utilities
│   │       └── pdf_generator.py         # NEW: PDF generation utilities
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── importExport.ts          # NEW: Import/export API methods
│   │   ├── components/
│   │   │   └── ImportExport/           # NEW: Import/export components
│   │   │       ├── ExportTab.tsx       # Export configuration UI
│   │   │       ├── ImportTab.tsx       # Import upload & mapping UI
│   │   │       ├── ExportHistory.tsx   # Export history table
│   │   │       ├── FileDropZone.tsx    # Drag & drop component
│   │   │       ├── FormatSelector.tsx  # Export format selection
│   │   │       ├── ConflictResolver.tsx # Import conflict UI
│   │   │       └── ProgressTracker.tsx # Progress bar component
│   │   ├── pages/
│   │   │   └── ImportExport.tsx        # NEW: Main import/export page
│   │   ├── hooks/
│   │   │   └── useImportExport.ts      # NEW: Import/export hooks
│   │   └── store/
│   │       └── importExportStore.ts    # NEW: Import/export state
└── PRPs/
    └── ai_docs/
        ├── mongodb-bulk-operations.md   # NEW: MongoDB patterns doc
        └── react-query-patterns.md      # NEW: React Query patterns doc
```

### Known Gotchas of our codebase & Library Quirks

```python
# CRITICAL: MongoDB Decimal128 for monetary values
# Always use Decimal128 for cost fields
from bson import Decimal128
cost_decimal = Decimal128(str(cost_value))

# CRITICAL: PyObjectId custom type for MongoDB ObjectIds
# Use this for all MongoDB _id fields
from app.models.py_object_id import PyObjectId

# CRITICAL: Content hashing for deduplication
# Messages use SHA-256 hash of content for deduplication
import hashlib
content_hash = hashlib.sha256(content.encode()).hexdigest()

# CRITICAL: Batch size limits
# MongoDB bulk operations limited to 1000 documents per batch
BATCH_SIZE = 1000

# CRITICAL: WebSocket connection management
# Use WeakSet for automatic cleanup of closed connections
from weakref import WeakSet
connections: WeakSet = WeakSet()

# CRITICAL: React Query cache invalidation
# Must invalidate queries after mutations
queryClient.invalidateQueries({ queryKey: ['sessions'] })

# CRITICAL: Tailwind CSS custom properties
# Use CSS variables from globals.css (primary-c, secondary-c, etc.)
# Dark mode handled via data-theme attribute on html element
```

## Implementation Blueprint

### Data models and structure

Create the core data models for import/export operations:

```python
# backend/app/schemas/import_export.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    PDF = "pdf"

class ConflictStrategy(str, Enum):
    SKIP = "skip"
    REPLACE = "replace"
    MERGE = "merge"

class ExportRequest(BaseModel):
    format: ExportFormat
    session_ids: Optional[List[str]] = None
    project_ids: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    include_metadata: bool = True
    include_costs: bool = True
    compress: bool = False

class ImportRequest(BaseModel):
    conflict_strategy: ConflictStrategy = ConflictStrategy.SKIP
    validate_only: bool = False
    field_mapping: Optional[Dict[str, str]] = None

class ExportJob(BaseModel):
    id: str
    status: str  # pending, processing, completed, failed
    format: ExportFormat
    created_at: datetime
    completed_at: Optional[datetime]
    file_url: Optional[str]
    file_size: Optional[int]
    error: Optional[str]
    progress: int = 0
    total_items: int = 0

class ImportValidation(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, int]  # conversations, messages, etc.
    conflicts: List[Dict[str, Any]] = []
```

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE backend/app/services/export_service.py
  - IMPLEMENT: ExportService class with bulk export methods
  - FOLLOW pattern: backend/app/services/ingest.py (service structure, batch processing)
  - NAMING: ExportService class, async def export_sessions(), export_to_json(), export_to_csv()
  - DEPENDENCIES: Import models from schemas/import_export.py
  - PLACEMENT: Service layer in backend/app/services/
  - CRITICAL: Use MongoDB aggregation for efficient bulk queries

Task 2: CREATE backend/app/utils/csv_converter.py
  - IMPLEMENT: CSV conversion utilities for sessions and messages
  - FOLLOW pattern: Use csv.DictWriter for consistent output
  - NAMING: sessions_to_csv(), messages_to_csv() functions
  - DEPENDENCIES: Import from models/session.py, models/message.py
  - PLACEMENT: Utility module in backend/app/utils/
  - CRITICAL: Handle nested JSON fields, preserve data types

Task 3: CREATE backend/app/utils/pdf_generator.py
  - IMPLEMENT: PDF generation using reportlab or weasyprint
  - FOLLOW pattern: Markdown conversion then PDF generation
  - NAMING: generate_pdf_from_sessions() function
  - DEPENDENCIES: Install reportlab or weasyprint
  - PLACEMENT: Utility module in backend/app/utils/
  - CRITICAL: Support code syntax highlighting, proper formatting

Task 4: CREATE backend/app/services/import_service.py
  - IMPLEMENT: ImportService class for data import with validation
  - FOLLOW pattern: backend/app/services/ingest.py (bulk operations, deduplication)
  - NAMING: ImportService class, async def import_data(), validate_import()
  - DEPENDENCIES: Import validation from services/validation.py
  - PLACEMENT: Service layer in backend/app/services/
  - CRITICAL: Use contentHash for deduplication, batch size = 1000

Task 5: CREATE backend/app/services/file_validation.py
  - IMPLEMENT: File upload security validation
  - FOLLOW pattern: OWASP file upload security guidelines
  - NAMING: validate_file(), check_file_type(), scan_content()
  - DEPENDENCIES: python-magic for MIME type detection
  - PLACEMENT: Service layer in backend/app/services/
  - CRITICAL: Whitelist file types, size limits, content validation

Task 6: CREATE backend/app/api/api_v1/endpoints/import_export.py
  - IMPLEMENT: FastAPI endpoints for import/export operations
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/export.py (StreamingResponse)
  - NAMING: /export/bulk, /import, /import/validate endpoints
  - DEPENDENCIES: Import services from Task 1 and 4
  - PLACEMENT: API endpoints in backend/app/api/api_v1/endpoints/
  - CRITICAL: Use BackgroundTasks for long operations, WebSocket for progress

Task 7: MODIFY backend/app/api/api_v1/api.py
  - INTEGRATE: Register new import_export router
  - FIND pattern: existing router.include_router() calls
  - ADD: Import and register import_export router
  - PRESERVE: Existing router registrations
  - CRITICAL: Use prefix="/import-export" for new endpoints

Task 8: CREATE frontend/src/components/ImportExport/FileDropZone.tsx
  - IMPLEMENT: Drag & drop file upload component using react-dropzone
  - FOLLOW pattern: plans/uiredesign/mockups/import-export-page.html (drop zone UI)
  - NAMING: FileDropZone component with onFileAccepted prop
  - DEPENDENCIES: npm install react-dropzone
  - PLACEMENT: Component in frontend/src/components/ImportExport/
  - CRITICAL: File validation, size limits, visual feedback

Task 9: CREATE frontend/src/components/ImportExport/FormatSelector.tsx
  - IMPLEMENT: Export format selection grid
  - FOLLOW pattern: plans/uiredesign/mockups/import-export-page.html (format cards)
  - NAMING: FormatSelector component with onFormatSelect prop
  - DEPENDENCIES: Use existing Card component from common/
  - PLACEMENT: Component in frontend/src/components/ImportExport/
  - CRITICAL: Visual selection state, format descriptions

Task 10: CREATE frontend/src/components/ImportExport/ProgressTracker.tsx
  - IMPLEMENT: WebSocket-based progress tracking component
  - FOLLOW pattern: frontend/src/components/DeletionProgressDialog.tsx
  - NAMING: ProgressTracker with jobId prop
  - DEPENDENCIES: Use existing useWebSocket hook
  - PLACEMENT: Component in frontend/src/components/ImportExport/
  - CRITICAL: Real-time updates, error handling, completion state

Task 11: CREATE frontend/src/components/ImportExport/ConflictResolver.tsx
  - IMPLEMENT: UI for resolving import conflicts
  - FOLLOW pattern: plans/uiredesign/mockups/import-export-page.html (conflict UI)
  - NAMING: ConflictResolver with conflicts and onResolve props
  - DEPENDENCIES: Use Dialog component from ui/
  - PLACEMENT: Component in frontend/src/components/ImportExport/
  - CRITICAL: Show data comparison, bulk resolution options

Task 12: CREATE frontend/src/components/ImportExport/ExportTab.tsx
  - IMPLEMENT: Complete export configuration tab
  - FOLLOW pattern: plans/uiredesign/mockups/import-export-page.html (export section)
  - NAMING: ExportTab component
  - DEPENDENCIES: Import FormatSelector, ProgressTracker components
  - PLACEMENT: Component in frontend/src/components/ImportExport/
  - CRITICAL: Date range picker, filter options, preview

Task 13: CREATE frontend/src/components/ImportExport/ImportTab.tsx
  - IMPLEMENT: Complete import configuration tab
  - FOLLOW pattern: plans/uiredesign/mockups/import-export-page.html (import section)
  - NAMING: ImportTab component
  - DEPENDENCIES: Import FileDropZone, ConflictResolver components
  - PLACEMENT: Component in frontend/src/components/ImportExport/
  - CRITICAL: Field mapping, validation feedback

Task 14: CREATE frontend/src/components/ImportExport/ExportHistory.tsx
  - IMPLEMENT: Export history table with download links
  - FOLLOW pattern: frontend/src/pages/Sessions.tsx (table layout)
  - NAMING: ExportHistory component
  - DEPENDENCIES: Use existing table patterns
  - PLACEMENT: Component in frontend/src/components/ImportExport/
  - CRITICAL: Pagination, download functionality, expiry status

Task 15: CREATE frontend/src/api/importExport.ts
  - IMPLEMENT: API client methods for import/export
  - FOLLOW pattern: frontend/src/api/client.ts (ApiClient class methods)
  - NAMING: exportSessions(), importFile(), getExportHistory()
  - DEPENDENCIES: Extend existing ApiClient
  - PLACEMENT: API module in frontend/src/api/
  - CRITICAL: FormData for file uploads, streaming for downloads

Task 16: CREATE frontend/src/hooks/useImportExport.ts
  - IMPLEMENT: React Query hooks for import/export operations
  - FOLLOW pattern: Existing custom hooks in the codebase
  - NAMING: useExport, useImport, useExportHistory hooks
  - DEPENDENCIES: Import from @tanstack/react-query
  - PLACEMENT: Hooks directory in frontend/src/hooks/
  - CRITICAL: Optimistic updates, cache invalidation

Task 17: CREATE frontend/src/store/importExportStore.ts
  - IMPLEMENT: Zustand store slice for import/export state
  - FOLLOW pattern: frontend/src/store/index.ts (store structure)
  - NAMING: useImportExportStore with activeJobs, history state
  - DEPENDENCIES: Import from zustand
  - PLACEMENT: Store module in frontend/src/store/
  - CRITICAL: Persist export history, track active jobs

Task 18: CREATE frontend/src/pages/ImportExport.tsx
  - IMPLEMENT: Main import/export page with tab navigation
  - FOLLOW pattern: plans/uiredesign/mockups/import-export-page.html
  - NAMING: ImportExport page component
  - DEPENDENCIES: Import all ImportExport components
  - PLACEMENT: Page component in frontend/src/pages/
  - CRITICAL: Tab state management, responsive layout

Task 19: MODIFY frontend/src/App.tsx
  - INTEGRATE: Add route for import/export page
  - FIND pattern: existing Route components
  - ADD: Route path="/import-export" element={<ImportExport />}
  - PRESERVE: Existing routes
  - CRITICAL: Import ImportExport component

Task 20: MODIFY frontend/src/components/layout/Sidebar.tsx
  - INTEGRATE: Add navigation link for import/export
  - FIND pattern: existing navigation items
  - ADD: Import/Export menu item with icon
  - PRESERVE: Existing navigation structure
  - CRITICAL: Use appropriate icon from lucide-react

Task 21: CREATE PRPs/ai_docs/mongodb-bulk-operations.md
  - DOCUMENT: MongoDB bulk operation patterns for ClaudeLens
  - INCLUDE: Bulk write examples, batch processing, error handling
  - PLACEMENT: Documentation in PRPs/ai_docs/
  - CRITICAL: Include specific examples from the codebase

Task 22: CREATE PRPs/ai_docs/react-query-patterns.md
  - DOCUMENT: React Query patterns used in ClaudeLens
  - INCLUDE: Mutation examples, cache invalidation, optimistic updates
  - PLACEMENT: Documentation in PRPs/ai_docs/
  - CRITICAL: Include specific examples from the codebase

Task 23: CREATE backend/app/api/api_v1/endpoints/export_history.py
  - IMPLEMENT: Export history CRUD endpoints
  - FOLLOW pattern: Standard FastAPI CRUD patterns
  - NAMING: GET /export-history, DELETE /export-history/{id}
  - DEPENDENCIES: MongoDB for persistence
  - PLACEMENT: API endpoints directory
  - CRITICAL: Include pagination, filtering by user

Task 24: CREATE tests for all new components and services
  - IMPLEMENT: Unit tests for services, components, and endpoints
  - FOLLOW pattern: Existing test patterns in the codebase
  - NAMING: test_*.py for backend, *.test.tsx for frontend
  - DEPENDENCIES: pytest for backend, vitest for frontend
  - PLACEMENT: Adjacent to code being tested
  - CRITICAL: Test file validation, conflict resolution, progress tracking
```

### Implementation Patterns & Key Details

```python
# Backend: Export Service Pattern
# backend/app/services/export_service.py
from typing import AsyncGenerator
import json
import csv
from io import StringIO

class ExportService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def export_sessions_to_json(
        self,
        session_ids: list[str] | None = None,
        include_metadata: bool = True
    ) -> AsyncGenerator[str, None]:
        # PATTERN: Stream JSON data for memory efficiency
        pipeline = self._build_aggregation_pipeline(session_ids)

        yield '{"version":"1.0.0","conversations":['
        first = True

        async for session in self.db.sessions.aggregate(pipeline):
            if not first:
                yield ','
            first = False

            # CRITICAL: Convert Decimal128 to float for JSON serialization
            session_data = self._serialize_session(session)
            yield json.dumps(session_data)

        yield ']}'

    async def export_to_csv(self, session_ids: list[str]) -> str:
        # PATTERN: Use StringIO for in-memory CSV generation
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
        writer.writeheader()

        # GOTCHA: Flatten nested structures for CSV
        async for session in self._get_sessions(session_ids):
            flat_session = self._flatten_for_csv(session)
            writer.writerow(flat_session)

        return output.getvalue()

# Backend: Import Service Pattern
# backend/app/services/import_service.py
from pymongo import ReplaceOne
from app.services.validation import MessageValidator

class ImportService:
    BATCH_SIZE = 1000  # MongoDB batch limit

    async def import_data(
        self,
        data: dict,
        conflict_strategy: ConflictStrategy
    ) -> ImportStats:
        # PATTERN: Validate before processing
        validation = await self.validate_import(data)
        if not validation.valid:
            raise ValidationError(validation.errors)

        # PATTERN: Process in batches for memory efficiency
        for batch in self._batch_conversations(data['conversations']):
            operations = []

            for conv in batch:
                # CRITICAL: Generate contentHash for deduplication
                conv['contentHash'] = self._generate_hash(conv)

                if conflict_strategy == ConflictStrategy.SKIP:
                    # Check existence before adding
                    if not await self._exists(conv['id']):
                        operations.append(self._create_operation(conv))
                elif conflict_strategy == ConflictStrategy.REPLACE:
                    operations.append(ReplaceOne(
                        filter={'id': conv['id']},
                        replacement=conv,
                        upsert=True
                    ))

            if operations:
                await self.db.conversations.bulk_write(operations)

# Frontend: File Upload Pattern
// frontend/src/components/ImportExport/FileDropZone.tsx
import { useDropzone } from 'react-dropzone';

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileAccepted }) => {
    const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
        accept: {
            'application/json': ['.json'],
            'text/csv': ['.csv'],
        },
        maxSize: 100 * 1024 * 1024, // 100MB
        onDrop: async (acceptedFiles) => {
            if (acceptedFiles.length > 0) {
                // PATTERN: Validate file content, not just extension
                const file = acceptedFiles[0];
                const content = await file.text();

                try {
                    const parsed = JSON.parse(content);
                    onFileAccepted(file, parsed);
                } catch (error) {
                    toast.error('Invalid file format');
                }
            }
        }
    });

    return (
        <div {...getRootProps()} className={`drop-zone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            {/* Drop zone UI */}
        </div>
    );
};

// Frontend: Progress Tracking Pattern
// frontend/src/components/ImportExport/ProgressTracker.tsx
export const ProgressTracker: React.FC<{ jobId: string }> = ({ jobId }) => {
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState('initializing');

    // PATTERN: WebSocket for real-time updates
    useWebSocket(`/ws/export/${jobId}`, {
        onMessage: (event) => {
            const data = JSON.parse(event.data);
            setProgress(data.progress);
            setStatus(data.status);

            if (data.status === 'completed') {
                // Trigger download
                window.location.href = data.downloadUrl;
            }
        }
    });

    return (
        <div className="progress-container">
            <Progress value={progress} />
            <span>{status}</span>
        </div>
    );
};
```

### Integration Points

```yaml
DATABASE:
  - collection: "export_jobs"
    schema: "Store export job metadata and status"
  - index: "CREATE INDEX idx_export_jobs_user ON export_jobs(user_id, created_at DESC)"

CONFIG:
  - add to: backend/app/core/config.py
  - pattern: |
      EXPORT_MAX_SIZE_MB = int(os.getenv('EXPORT_MAX_SIZE_MB', '100'))
      EXPORT_RETENTION_DAYS = int(os.getenv('EXPORT_RETENTION_DAYS', '30'))
      IMPORT_BATCH_SIZE = int(os.getenv('IMPORT_BATCH_SIZE', '1000'))

ROUTES:
  - add to: backend/app/api/api_v1/api.py
  - pattern: |
      from app.api.api_v1.endpoints import import_export
      api_router.include_router(
          import_export.router,
          prefix="/import-export",
          tags=["import-export"]
      )

WEBSOCKET:
  - add to: backend/app/api/websocket.py
  - pattern: "WebSocket endpoint for progress tracking /ws/export/{job_id}"

FRONTEND_ROUTES:
  - add to: frontend/src/App.tsx
  - pattern: |
      import { ImportExport } from './pages/ImportExport';
      <Route path="/import-export" element={<ImportExport />} />
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Backend validation
cd backend
ruff check app/api/api_v1/endpoints/import_export.py --fix
ruff check app/services/import_service.py app/services/export_service.py --fix
mypy app/services/import_service.py app/services/export_service.py
ruff format app/

# Frontend validation
cd frontend
npm run lint
npm run type-check

# Expected: Zero errors. Fix any issues before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Backend tests
cd backend
poetry run pytest app/services/tests/test_import_service.py -v
poetry run pytest app/services/tests/test_export_service.py -v
poetry run pytest app/api/api_v1/endpoints/tests/test_import_export.py -v

# Frontend tests
cd frontend
npm run test -- --run ImportExport
npm run test -- --run FileDropZone
npm run test -- --run ProgressTracker

# Expected: All tests pass with good coverage.
```

### Level 3: Integration Testing (System Validation)

```bash
# Start backend with import/export endpoints
cd backend
poetry run uvicorn app.main:app --reload &
BACKEND_PID=$!

# Test export endpoint
curl -X POST http://localhost:8000/api/v1/import-export/export \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "format": "json",
    "session_ids": null,
    "include_metadata": true
  }' | jq .

# Test import validation
curl -X POST http://localhost:8000/api/v1/import-export/import/validate \
  -H "X-API-Key: ${API_KEY}" \
  -F "file=@test_export.json" | jq .

# Test WebSocket progress
wscat -c ws://localhost:8000/ws/export/test-job-id

# Frontend integration
cd frontend
npm run dev &
FRONTEND_PID=$!

# Test file upload
curl -X POST http://localhost:5173/api/v1/import-export/import \
  -F "file=@test_data.json" \
  -F "conflict_strategy=merge"

# Cleanup
kill $BACKEND_PID $FRONTEND_PID

# Expected: All endpoints responding, WebSocket connected, file upload working
```

### Level 4: End-to-End Testing

```bash
# Full export flow test
python -m pytest e2e/test_export_flow.py -v

# Full import flow test
python -m pytest e2e/test_import_flow.py -v

# Performance test for large export
python scripts/test_bulk_export.py --sessions 1000

# Security validation
# File upload security test
python scripts/test_file_upload_security.py

# Load test export endpoint
locust -f tests/load/export_load_test.py --users 10 --spawn-rate 2 --time 60s

# Browser automation test
npm run test:e2e -- ImportExportFlow

# Expected: All flows complete successfully, performance within limits
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] Backend tests pass: `poetry run pytest app/ -v`
- [ ] Frontend tests pass: `npm run test`
- [ ] No linting errors: `ruff check app/` and `npm run lint`
- [ ] No type errors: `mypy app/` and `npm run type-check`
- [ ] WebSocket connections stable
- [ ] File uploads validated and secure
- [ ] Export formats (JSON, CSV, Markdown, PDF) working
- [ ] Import with conflict resolution working

### Feature Validation

- [ ] Export page UI matches mockup from import-export-page.html
- [ ] All export formats generating correctly
- [ ] Import accepts JSON and CSV files
- [ ] Field mapping UI functional
- [ ] Conflict resolution strategies working (skip, replace, merge)
- [ ] Progress tracking shows real-time updates
- [ ] Export history persisted and downloadable
- [ ] File size limits enforced
- [ ] Dark mode working correctly
- [ ] Responsive design on mobile

### Code Quality Validation

- [ ] Follows existing ClaudeLens patterns
- [ ] File placement matches desired structure
- [ ] MongoDB operations use proper Decimal128 for costs
- [ ] Content hashing implemented for deduplication
- [ ] Batch processing respects 1000 document limit
- [ ] WebSocket cleanup using WeakSet
- [ ] React Query cache invalidation working
- [ ] Error handling comprehensive
- [ ] Security best practices followed

### Documentation & Deployment

- [ ] API documentation updated
- [ ] Environment variables documented
- [ ] Migration instructions provided if needed
- [ ] Performance metrics acceptable
- [ ] Security scan passed

---

## Anti-Patterns to Avoid

- ❌ Don't load entire export into memory - use streaming
- ❌ Don't skip file content validation - validate beyond extension
- ❌ Don't process all imports at once - use batching
- ❌ Don't ignore MongoDB Decimal128 for monetary values
- ❌ Don't forget WebSocket cleanup with WeakSet
- ❌ Don't hardcode export file paths - use configured storage
- ❌ Don't allow unrestricted file uploads - enforce limits
- ❌ Don't skip conflict resolution - always handle duplicates
- ❌ Don't forget to invalidate React Query cache after mutations
- ❌ Don't ignore dark mode - use CSS variables consistently
