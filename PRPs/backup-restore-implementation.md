name: "ClaudeLens Backup and Restore Feature Implementation PRP"
description: |
  Comprehensive implementation guide for adding enterprise-grade backup and restore functionality to ClaudeLens,
  following existing import/export patterns while extending with scheduled backups, compression, and incremental support.

---

## Goal

**Feature Goal**: Implement a complete backup and restore system that enables users to create, manage, and restore backups of their ClaudeLens conversation data with support for selective filtering, compression, scheduling, and progress tracking.

**Deliverable**: Full-stack implementation including:
- Backend API endpoints for backup/restore operations
- Service layer for backup creation, storage, and restoration
- Frontend UI for backup management and restore operations
- WebSocket-based progress tracking
- Job queue system for long-running operations

**Success Definition**: Users can successfully create full/selective backups, download them, restore from backups with conflict resolution, and schedule automatic backups with retention policies.

## User Persona

**Target User**: System administrators and power users managing ClaudeLens instances

**Use Case**: Regular backup creation for disaster recovery, data migration between instances, and testing/development workflows

**User Journey**:
1. Navigate to Backup page in Settings
2. Configure backup filters (projects, date range)
3. Initiate backup creation
4. Monitor progress via real-time updates
5. Download or restore from backup list
6. Configure automatic backup schedule

**Pain Points Addressed**:
- Risk of data loss from system failures
- No way to migrate data between environments
- Cannot safely test changes without backup
- Compliance requirements for data retention

## Why

- **Business Value**: Ensures data durability and business continuity for organizations using ClaudeLens
- **Integration**: Extends existing import/export infrastructure with enterprise backup capabilities
- **Problems Solved**: Data loss prevention, migration support, compliance with retention policies, safe testing environments

## What

Implement backup/restore system with:
- Full and selective backup creation with filtering
- Compressed backup files with checksums
- Server-side storage with configurable retention
- Streaming download/upload for large files
- Granular restore with conflict resolution
- Scheduled automatic backups
- Real-time progress tracking via WebSocket

### Success Criteria

- [ ] Create full database backup and successfully restore it
- [ ] Selective backup by project/date range works correctly
- [ ] Backup files are compressed and include checksums
- [ ] Large backups (>1GB) stream without memory issues
- [ ] Restore handles conflicts according to selected strategy
- [ ] Scheduled backups run automatically at configured times
- [ ] Progress updates display in real-time during operations
- [ ] All API endpoints match the contract specification

## All Needed Context

### Context Completeness Check

_This PRP provides complete implementation context including existing patterns, API contracts, database operations, streaming patterns, and UI components needed for one-pass implementation success._

### Documentation & References

```yaml
# MUST READ - Include these in your context window

- file: backend/app/api/api_v1/endpoints/import_export.py
  why: Existing import/export implementation showing job patterns, rate limiting, progress tracking
  pattern: Job-based async processing, WebSocket progress broadcasting, file handling
  gotcha: Uses in-memory rate limiting, asyncio.create_task for background jobs

- file: backend/app/services/export_service.py
  why: Export service patterns for streaming large datasets, progress tracking
  pattern: AsyncGenerator for memory-efficient streaming, batch processing (100 items)
  gotcha: Must handle MongoDB cursor timeouts, batch size affects memory usage

- file: backend/app/services/import_service.py
  why: Import patterns for validation, conflict detection, transaction management
  pattern: ImportTransaction for rollback support, multi-stage validation pipeline
  gotcha: Field mapping must handle different formats, transaction rollback complexity

- file: backend/app/services/file_service.py
  why: File handling patterns for secure upload/download, streaming I/O
  pattern: Async file operations with aiofiles, checksum generation, temp file management
  gotcha: File cleanup on errors, security validation for paths

- file: backend/app/models/export_job.py
  why: Job model structure for tracking long-running operations
  pattern: Status state machine, progress tracking fields, error collection
  gotcha: Status transitions must be atomic, progress updates need throttling

- file: PRPs/backup-restore-feature-prd.md
  why: Complete product requirements and user stories
  critical: Phased implementation approach, specific UI requirements

- file: PRPs/contracts/backup-restore-api-contract.md
  why: Exact API specifications and data models
  critical: Request/response schemas, validation rules, error codes

- docfile: PRPs/ai_docs/mongodb-backup-restore-patterns.md
  why: MongoDB-specific backup/restore patterns with Motor async driver
  section: Streaming collections, bulk operations, transaction support

- docfile: PRPs/ai_docs/streaming-compression-patterns.md
  why: Streaming and compression implementation patterns
  section: Zstandard integration, progress tracking, WebSocket updates

- url: https://motor.readthedocs.io/en/stable/tutorial-asyncio.html
  why: Motor async MongoDB driver patterns for bulk operations
  critical: Cursor timeout handling, transaction usage with sessions

- url: https://python-zstandard.readthedocs.io/en/stable/
  why: Zstandard compression library for optimal backup compression
  critical: Streaming compression API, compression levels (use 3 for balance)
```

### Current Codebase Tree

```bash
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/
│   │           ├── import_export.py  # Existing import/export
│   │           └── ...
│   ├── services/
│   │   ├── export_service.py        # Export patterns
│   │   ├── import_service.py        # Import patterns
│   │   ├── file_service.py          # File handling
│   │   └── ...
│   ├── models/
│   │   ├── export_job.py            # Job tracking
│   │   └── import_job.py
│   └── schemas/
│       └── import_schemas.py        # Import/export schemas
frontend/
├── src/
│   ├── pages/
│   │   └── ImportExport.tsx         # Existing UI
│   └── components/
│       └── import-export/            # UI components
```

### Desired Codebase Tree with Files to Add

```bash
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/
│   │           ├── backup.py         # NEW: Backup management endpoints
│   │           └── restore.py        # NEW: Restore operations endpoints
│   ├── services/
│   │   ├── backup_service.py        # NEW: Backup creation/management
│   │   ├── restore_service.py       # NEW: Restore operations
│   │   ├── compression_service.py   # NEW: Compression utilities
│   │   └── backup_scheduler.py      # NEW: Scheduled backup service
│   ├── models/
│   │   ├── backup_job.py           # NEW: Backup job model
│   │   └── backup_metadata.py      # NEW: Backup metadata model
│   ├── schemas/
│   │   └── backup_schemas.py       # NEW: Backup/restore schemas
│   └── core/
│       └── backup_config.py        # NEW: Backup configuration
frontend/
├── src/
│   ├── pages/
│   │   └── Backup.tsx              # NEW: Main backup page
│   ├── components/
│   │   └── backup/                 # NEW: Backup UI components
│   │       ├── BackupList.tsx
│   │       ├── CreateBackupDialog.tsx
│   │       ├── RestoreDialog.tsx
│   │       └── BackupProgress.tsx
│   └── api/
│       └── backupApi.ts            # NEW: Backup API client
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: Motor cursor timeout for large collections
# Use batch_size and process quickly to avoid cursor timeout (default 10 minutes)
cursor = collection.find({}).batch_size(100)

# CRITICAL: Zstandard compression requires proper cleanup
# Always flush compressor to get final compressed data
final_chunk = compressor.flush()

# CRITICAL: WebSocket progress updates need throttling
# Update at most once per second to avoid overwhelming clients
last_update = time.time()
if time.time() - last_update > 1.0:
    await broadcast_progress()

# CRITICAL: File operations must handle cleanup on error
# Use try/finally or context managers for temp file cleanup
```

## Implementation Blueprint

### Data Models and Structure

```python
# backend/app/models/backup_metadata.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.common import PyObjectId

class BackupMetadata(BaseModel):
    """Backup metadata stored in MongoDB."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    filename: str
    filepath: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    size_bytes: int
    compressed_size_bytes: Optional[int] = None
    type: str  # 'full', 'incremental', 'selective'
    status: str  # 'pending', 'in_progress', 'completed', 'failed', 'corrupted'
    filters: Optional[Dict[str, Any]] = None
    contents: Dict[str, int]  # counts by collection
    checksum: str
    version: str = "1.0.0"
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str}

# backend/app/schemas/backup_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    SELECTIVE = "selective"

class BackupFilters(BaseModel):
    """Filters for selective backup."""
    projects: Optional[List[str]] = None
    sessions: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    min_message_count: Optional[int] = Field(None, ge=1, le=10000)
    max_message_count: Optional[int] = Field(None, ge=1, le=10000)

class CreateBackupRequest(BaseModel):
    """Request to create a backup."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: BackupType
    filters: Optional[BackupFilters] = None
    options: Optional[Dict[str, Any]] = None

    @validator('name')
    def validate_name(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Name must be alphanumeric with spaces, dashes, or underscores')
        return v

class RestoreMode(str, Enum):
    FULL = "full"
    SELECTIVE = "selective"
    MERGE = "merge"

class ConflictResolution(str, Enum):
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    MERGE = "merge"

class CreateRestoreRequest(BaseModel):
    """Request to restore from backup."""
    backup_id: str
    mode: RestoreMode
    target: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None
    selections: Optional[Dict[str, Any]] = None
```

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE backend/app/models/backup_metadata.py and backup_job.py
  - IMPLEMENT: BackupMetadata and BackupJob Pydantic models
  - FOLLOW pattern: backend/app/models/export_job.py (status tracking, progress fields)
  - NAMING: Use existing PyObjectId pattern for MongoDB IDs
  - PLACEMENT: Models directory with other domain models

Task 2: CREATE backend/app/schemas/backup_schemas.py
  - IMPLEMENT: Request/response schemas matching API contract
  - FOLLOW pattern: backend/app/schemas/import_schemas.py (validation patterns)
  - NAMING: CreateBackupRequest, BackupResponse, RestoreRequest patterns
  - DEPENDENCIES: Import enums and base models from Task 1
  - PLACEMENT: Schemas directory with validation logic

Task 3: CREATE backend/app/services/compression_service.py
  - IMPLEMENT: StreamingCompressor class with zstandard
  - FOLLOW pattern: PRPs/ai_docs/streaming-compression-patterns.md
  - NAMING: compress_stream, decompress_stream async methods
  - CRITICAL: Use compression level 3 for balance, always flush at end
  - PLACEMENT: Services layer for reusability

Task 4: CREATE backend/app/services/backup_service.py
  - IMPLEMENT: BackupService class with create_backup, list_backups, delete_backup
  - FOLLOW pattern: backend/app/services/export_service.py (streaming, progress tracking)
  - NAMING: Async methods following service conventions
  - DEPENDENCIES: Import compression from Task 3, use Motor for MongoDB
  - CRITICAL: Stream data in batches of 100, handle cursor timeouts
  - PLACEMENT: Service layer following existing patterns

Task 5: CREATE backend/app/services/restore_service.py
  - IMPLEMENT: RestoreService with restore_backup, preview_backup methods
  - FOLLOW pattern: backend/app/services/import_service.py (validation, transactions)
  - NAMING: restore_from_backup, validate_backup, handle_conflicts
  - DEPENDENCIES: Import decompression from Task 3
  - CRITICAL: Use transactions for atomic restore, map old IDs to new
  - PLACEMENT: Service layer with transaction support

Task 6: CREATE backend/app/api/api_v1/endpoints/backup.py
  - IMPLEMENT: REST endpoints for backup operations matching API contract
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/import_export.py
  - NAMING: create_backup, list_backups, download_backup, delete_backup
  - DEPENDENCIES: Import services from Tasks 4-5, schemas from Task 2
  - CRITICAL: Rate limiting (10 backups/hour), streaming responses
  - PLACEMENT: API endpoints directory

Task 7: CREATE backend/app/api/api_v1/endpoints/restore.py
  - IMPLEMENT: REST endpoints for restore operations
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/import_export.py
  - NAMING: create_restore, upload_restore, preview_backup
  - DEPENDENCIES: Import RestoreService from Task 5
  - CRITICAL: Handle multipart uploads, validate file types
  - PLACEMENT: API endpoints directory

Task 8: MODIFY backend/app/api/api_v1/api.py
  - INTEGRATE: Register new backup and restore routers
  - FIND pattern: Existing router registrations
  - ADD: api_router.include_router(backup_router, prefix="/backup", tags=["backup"])
  - ADD: api_router.include_router(restore_router, prefix="/restore", tags=["restore"])
  - PRESERVE: All existing router registrations

Task 9: CREATE frontend/src/api/backupApi.ts
  - IMPLEMENT: TypeScript API client for backup/restore operations
  - FOLLOW pattern: frontend/src/api/client.ts (axios configuration)
  - NAMING: createBackup, listBackups, restoreBackup functions
  - DEPENDENCIES: Use existing apiClient instance
  - PLACEMENT: API directory with other clients

Task 10: CREATE frontend/src/components/backup/BackupList.tsx
  - IMPLEMENT: Table component showing backups with actions
  - FOLLOW pattern: frontend/src/components/import-export/ExportPanel.tsx
  - NAMING: BackupList, BackupRow, BackupActions components
  - DEPENDENCIES: Use React Query for data fetching
  - PLACEMENT: New backup components directory

Task 11: CREATE frontend/src/components/backup/CreateBackupDialog.tsx
  - IMPLEMENT: Modal dialog for backup creation with filters
  - FOLLOW pattern: frontend/src/components/import-export/ExportConfigModal.tsx
  - NAMING: CreateBackupDialog with form validation
  - DEPENDENCIES: Use existing UI components from frontend/src/components/ui/
  - PLACEMENT: Backup components directory

Task 12: CREATE frontend/src/pages/Backup.tsx
  - IMPLEMENT: Main backup management page
  - FOLLOW pattern: frontend/src/pages/ImportExport.tsx (tabbed interface)
  - NAMING: BackupPage with state management
  - DEPENDENCIES: Import components from Tasks 10-11
  - PLACEMENT: Pages directory

Task 13: MODIFY frontend/src/App.tsx
  - INTEGRATE: Add route for backup page
  - FIND pattern: Existing route definitions
  - ADD: <Route path="/backup" element={<BackupPage />} />
  - PRESERVE: All existing routes

Task 14: CREATE tests/test_services_backup.py
  - IMPLEMENT: Unit tests for backup service
  - FOLLOW pattern: backend/tests/test_services_export.py
  - NAMING: test_create_backup, test_compression, test_streaming
  - COVERAGE: All service methods, error cases, edge conditions
  - PLACEMENT: Backend tests directory

Task 15: CREATE tests/test_endpoints_backup.py
  - IMPLEMENT: API endpoint tests
  - FOLLOW pattern: backend/tests/test_endpoints_import_export.py
  - NAMING: test_create_backup_endpoint, test_download_backup
  - COVERAGE: All endpoints, validation, rate limiting
  - PLACEMENT: Backend tests directory

Task 16: CREATE backend/app/services/backup_scheduler.py
  - IMPLEMENT: Scheduled backup service (Phase 2)
  - PATTERN: Use APScheduler or similar for cron-like scheduling
  - NAMING: ScheduledBackupService with schedule_backup, cancel_schedule
  - DEPENDENCIES: Import BackupService from Task 4
  - PLACEMENT: Services directory
```

### Implementation Patterns & Key Details

```python
# Streaming backup creation pattern
async def create_backup(self, request: CreateBackupRequest) -> str:
    """Create backup with streaming and compression."""
    # PATTERN: Job creation first (follow export_service.py)
    job_id = str(ObjectId())
    await self.db.backup_jobs.insert_one({
        "_id": ObjectId(job_id),
        "status": "pending",
        "created_at": datetime.utcnow(),
        "progress": {"current": 0, "total": 100}
    })

    # PATTERN: Background task execution
    asyncio.create_task(self._process_backup(job_id, request))
    return job_id

async def _process_backup(self, job_id: str, request: CreateBackupRequest):
    """Process backup in background with progress updates."""
    try:
        # CRITICAL: Stream data in batches to avoid memory issues
        compressor = StreamingCompressor(level=3)

        # PATTERN: Progress tracking with WebSocket updates
        progress_tracker = BackupProgressTracker(job_id)

        async with aiofiles.open(backup_path, 'wb') as f:
            async for compressed_chunk in compressor.compress_stream(
                self._stream_collections(request.filters)
            ):
                await f.write(compressed_chunk)
                await progress_tracker.update_progress()

        # CRITICAL: Always update job status
        await self.db.backup_jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "completed"}}
        )
    except Exception as e:
        await self.db.backup_jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "failed", "error": str(e)}}
        )

# Restore with transaction pattern
async def restore_backup(self, request: RestoreRequest) -> str:
    """Restore backup with transaction support."""
    # PATTERN: Validate before restore (follow import_service.py)
    validation_result = await self.validate_backup(request.backup_id)
    if not validation_result.is_valid:
        raise ValidationError(validation_result.errors)

    # CRITICAL: Use transaction for atomic restore
    async with await self.client.start_session() as session:
        async with session.start_transaction():
            # PATTERN: Stream and decompress
            async for batch in self._stream_backup_data(request.backup_id):
                await self._restore_batch(batch, request.options, session)

    return restore_job_id

# WebSocket progress pattern
@router.websocket("/ws/backup/{job_id}")
async def backup_progress(websocket: WebSocket, job_id: str):
    """Stream backup progress via WebSocket."""
    # PATTERN: Follow websocket.py patterns
    await websocket.accept()

    try:
        while True:
            # Get progress from database
            job = await db.backup_jobs.find_one({"_id": ObjectId(job_id)})

            if job:
                await websocket.send_json({
                    "status": job["status"],
                    "progress": job["progress"],
                    "timestamp": datetime.utcnow().isoformat()
                })

            if job["status"] in ["completed", "failed"]:
                break

            await asyncio.sleep(1)  # Throttle updates
    except WebSocketDisconnect:
        pass
```

### Integration Points

```yaml
DATABASE:
  - collection: "backup_jobs"
  - collection: "backup_metadata"
  - indexes: "CREATE INDEX idx_backup_created ON backup_metadata(created_at)"
  - indexes: "CREATE INDEX idx_backup_status ON backup_jobs(status)"

CONFIG:
  - add to: backend/app/core/config.py
  - pattern: |
      BACKUP_STORAGE_PATH = os.getenv("BACKUP_STORAGE_PATH", "/var/claudelens/backups")
      BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
      BACKUP_MAX_SIZE_GB = int(os.getenv("BACKUP_MAX_SIZE_GB", "100"))

ROUTES:
  - add to: backend/app/api/api_v1/api.py
  - pattern: |
      from app.api.api_v1.endpoints import backup, restore
      api_router.include_router(backup.router, prefix="/backups", tags=["backup"])
      api_router.include_router(restore.router, prefix="/restore", tags=["restore"])

DEPENDENCIES:
  - add to: backend/pyproject.toml
  - packages: |
      zstandard = "^0.22.0"  # Compression library
      apscheduler = "^3.10.0"  # For scheduled backups (Phase 2)

FRONTEND_ROUTES:
  - add to: frontend/src/App.tsx
  - pattern: |
      import { BackupPage } from '@/pages/Backup';
      <Route path="/backup" element={<BackupPage />} />
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Backend validation
cd backend
poetry run ruff check app/services/backup_service.py --fix
poetry run ruff check app/api/api_v1/endpoints/backup.py --fix
poetry run mypy app/services/backup_service.py
poetry run black app/services/ app/api/

# Frontend validation
cd frontend
npm run lint
npm run format
npm run type-check

# Expected: Zero errors. Fix any issues before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Backend tests
cd backend
poetry run pytest tests/test_services_backup.py -v
poetry run pytest tests/test_services_restore.py -v
poetry run pytest tests/test_endpoints_backup.py -v
poetry run pytest tests/test_endpoints_restore.py -v

# Coverage check
poetry run pytest tests/ --cov=app/services --cov=app/api --cov-report=term-missing

# Frontend tests
cd frontend
npm run test:coverage

# Expected: All tests pass with >80% coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Start backend
cd backend
poetry run uvicorn app.main:app --reload &
BACKEND_PID=$!

# Wait for startup
sleep 5

# Test backup creation
curl -X POST http://localhost:8000/api/v1/backups \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "Test Backup",
    "type": "full",
    "options": {"compress": true}
  }' | jq .

# Test backup list
curl http://localhost:8000/api/v1/backups \
  -H "X-API-Key: your-api-key" | jq .

# Test WebSocket progress
wscat -c ws://localhost:8000/ws/backup/{job_id}

# Test restore preview
curl http://localhost:8000/api/v1/restore/preview/{backup_id} \
  -H "X-API-Key: your-api-key" | jq .

# Cleanup
kill $BACKEND_PID

# Expected: All endpoints respond correctly, WebSocket streams progress
```

### Level 4: End-to-End Testing

```bash
# Full backup/restore cycle test
cd backend
poetry run python -m pytest tests/test_integration_backup_restore.py -v

# Performance test with large dataset
poetry run python scripts/test_backup_performance.py

# Test with Docker
docker-compose up -d
sleep 10

# Create backup via UI
open http://localhost:3000/backup

# Test file download
BACKUP_ID=$(curl -s http://localhost:8000/api/v1/backups | jq -r '.items[0]._id')
curl -O http://localhost:8000/api/v1/backups/$BACKUP_ID/download

# Verify backup integrity
sha256sum backup_*.tar.gz

# Test restore
curl -X POST http://localhost:8000/api/v1/restore \
  -H "Content-Type: application/json" \
  -d "{\"backup_id\": \"$BACKUP_ID\", \"mode\": \"full\"}"

# Expected: Complete cycle works, files are valid, data restored correctly
```

## Final Validation Checklist

### Technical Validation

- [ ] All validation levels pass without errors
- [ ] Backend tests: `poetry run pytest tests/ -v` (all pass)
- [ ] Frontend tests: `npm run test:ci` (all pass)
- [ ] No linting errors: `poetry run ruff check app/`
- [ ] No type errors: `poetry run mypy app/`
- [ ] API contract compliance verified

### Feature Validation

- [ ] Full backup creation and download works
- [ ] Selective backup with filters works correctly
- [ ] Compression reduces file size by >50%
- [ ] Large backups (>1GB) stream without memory issues
- [ ] Restore successfully recreates all data
- [ ] Conflict resolution strategies work as specified
- [ ] Progress updates display in real-time
- [ ] Rate limiting prevents abuse (10 backups/hour)

### Code Quality Validation

- [ ] Follows existing ClaudeLens patterns
- [ ] Uses snake_case for Python, PascalCase for React components
- [ ] Proper error handling with specific exceptions
- [ ] Async/await used consistently
- [ ] WebSocket updates throttled appropriately
- [ ] Temporary files cleaned up on error
- [ ] MongoDB transactions used for atomic operations

### Documentation & Deployment

- [ ] Environment variables documented in config
- [ ] API endpoints documented in OpenAPI spec
- [ ] Backup file format documented
- [ ] Recovery procedures documented
- [ ] Docker image builds successfully

---

## Anti-Patterns to Avoid

- ❌ Don't load entire backup into memory - use streaming
- ❌ Don't skip transaction support for restore operations
- ❌ Don't forget to clean up temporary files on error
- ❌ Don't send WebSocket updates more than once per second
- ❌ Don't use compression level >3 unless specifically needed
- ❌ Don't ignore MongoDB cursor timeouts on large collections
- ❌ Don't create backups without checksums for integrity
- ❌ Don't allow path traversal in file operations

---

## Implementation Confidence Score: 9/10

This PRP provides comprehensive implementation guidance with:
- Complete API specifications from contract
- Existing codebase patterns to follow
- MongoDB and streaming best practices documented
- Detailed task breakdown with dependencies
- Validation procedures at multiple levels
- Known gotchas and solutions identified

The implementation can proceed with high confidence following this blueprint.
