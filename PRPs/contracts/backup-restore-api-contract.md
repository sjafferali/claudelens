# Backup and Restore API Contract

## API Version
- **Version**: 1.0.0
- **Base URL**: `/api/v1`
- **Content-Type**: `application/json`
- **Authentication**: Bearer token via `X-API-Key` header

## 1. Backup Management Endpoints

### 1.1 Create Backup

**Endpoint**: `POST /api/v1/backups`

**Description**: Creates a new backup job with optional filters and configuration

**Request Body**:
```typescript
interface CreateBackupRequest {
  name: string;                    // Required, 3-100 chars, alphanumeric + spaces/dashes
  description?: string;            // Optional, max 500 chars
  type: BackupType;                // Required: 'full' | 'selective'
  filters?: BackupFilters;         // Optional, filtering criteria
  options?: BackupOptions;         // Optional, backup configuration
}

interface BackupFilters {
  projects?: string[];             // Array of project IDs to include
  sessions?: string[];             // Array of session IDs to include
  date_range?: {
    start: string;                 // ISO 8601 date-time
    end: string;                   // ISO 8601 date-time
  };
  include_patterns?: string[];     // Glob patterns to include
  exclude_patterns?: string[];     // Glob patterns to exclude
  min_message_count?: number;      // Min messages per session (1-10000)
  max_message_count?: number;      // Max messages per session (1-10000)
}

interface BackupOptions {
  compress?: boolean;              // Default: true
  compression_level?: number;      // 1-9, default: 6
  encrypt?: boolean;               // Default: false
  include_metadata?: boolean;      // Default: true
  include_analytics?: boolean;     // Default: false
  split_size_mb?: number;          // Split large backups, 100-5000 MB
}

enum BackupType {
  FULL = 'full',
  SELECTIVE = 'selective'
}
```

**Response** (202 Accepted):
```typescript
interface CreateBackupResponse {
  job_id: string;                  // UUID of the backup job
  backup_id: string;               // UUID of the backup (once created)
  status: JobStatus;               // 'pending' | 'in_progress' | 'completed' | 'failed'
  created_at: string;              // ISO 8601 timestamp
  estimated_size_bytes?: number;   // Estimated backup size
  estimated_duration_seconds?: number; // Estimated completion time
  message: string;                 // Human-readable status message
}
```

**Validation Rules**:
- `name`: Required, 3-100 characters, must match `/^[a-zA-Z0-9\s\-_]+$/`
- `description`: Optional, max 500 characters
- `type`: Required, must be one of the enum values
- `date_range.start`: Must be before `date_range.end`
- `date_range.end`: Must not be in the future
- `compression_level`: Must be between 1-9
- `split_size_mb`: Must be between 100-5000
- At least one filter must be specified for 'selective' type

**Error Responses**:
- `400 Bad Request`: Invalid request body or validation failure
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: User lacks permission to create backups
- `429 Too Many Requests`: Rate limit exceeded (10 backups/hour)
- `507 Insufficient Storage`: Not enough storage space

### 1.2 List Backups

**Endpoint**: `GET /api/v1/backups`

**Description**: Retrieves paginated list of backups with optional filtering

**Query Parameters**:
```typescript
interface ListBackupsParams {
  page?: number;                   // Default: 1, min: 1
  size?: number;                   // Default: 20, min: 1, max: 100
  sort?: string;                   // Format: "field,direction" e.g., "created_at,desc"
  type?: BackupType;               // Filter by backup type
  status?: BackupStatus;           // Filter by status
  created_after?: string;          // ISO 8601 date-time
  created_before?: string;         // ISO 8601 date-time
  min_size?: number;               // Minimum size in bytes
  max_size?: number;               // Maximum size in bytes
  search?: string;                 // Search in name/description
}
```

**Response** (200 OK):
```typescript
interface PagedBackupsResponse {
  items: BackupMetadata[];
  pagination: {
    total_items: number;
    total_pages: number;
    current_page: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
  };
  summary: {
    total_size_bytes: number;
    total_backups: number;
    backups_by_type: Record<BackupType, number>;
    oldest_backup: string;         // ISO 8601
    newest_backup: string;          // ISO 8601
  };
}

interface BackupMetadata {
  _id: string;                     // Backup ID
  name: string;
  description?: string;
  filename: string;
  filepath: string;
  created_at: string;               // ISO 8601
  created_by?: string;              // User ID who created it
  size_bytes: number;
  compressed_size_bytes?: number;
  type: BackupType;
  status: BackupStatus;
  filters?: BackupFilters;
  contents: BackupContents;
  checksum: string;                // SHA-256 hash
  version: string;                  // Backup format version
  download_url?: string;            // Pre-signed download URL (expires in 1 hour)
  can_restore: boolean;             // Whether backup can be restored
  error_message?: string;           // If status is 'failed' or 'corrupted'
}

interface BackupContents {
  projects_count: number;
  sessions_count: number;
  messages_count: number;
  prompts_count: number;
  ai_settings_count: number;
  total_documents: number;
  date_range?: {
    earliest: string;               // ISO 8601
    latest: string;                 // ISO 8601
  };
}

enum BackupStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CORRUPTED = 'corrupted',
  DELETING = 'deleting'
}
```

### 1.3 Get Backup Details

**Endpoint**: `GET /api/v1/backups/{backup_id}`

**Description**: Retrieves detailed information about a specific backup

**Path Parameters**:
- `backup_id`: UUID of the backup

**Response** (200 OK):
```typescript
interface BackupDetailResponse extends BackupMetadata {
  storage_location: string;
  encryption?: {
    enabled: boolean;
    algorithm?: string;
    key_id?: string;
  };
  compression?: {
    enabled: boolean;
    algorithm: string;
    level: number;
    original_size_bytes: number;
    compressed_size_bytes: number;
    compression_ratio: number;
  };
  restore_history: RestoreAttempt[];
  validation_status?: {
    validated_at: string;           // ISO 8601
    is_valid: boolean;
    errors?: string[];
    warnings?: string[];
  };
}

interface RestoreAttempt {
  _id: string;
  restored_at: string;              // ISO 8601
  restored_by: string;
  status: 'success' | 'failed' | 'partial';
  documents_restored: number;
  error_message?: string;
}
```

### 1.4 Download Backup

**Endpoint**: `GET /api/v1/backups/{backup_id}/download`

**Description**: Downloads the backup file as a binary stream

**Path Parameters**:
- `backup_id`: UUID of the backup

**Response** (200 OK):
- **Headers**:
  - `Content-Type: application/gzip` or `application/x-tar`
  - `Content-Disposition: attachment; filename="backup-{timestamp}.tar.gz"`
  - `Content-Length: {size_in_bytes}`
  - `X-Checksum: {sha256_hash}`
- **Body**: Binary stream of the backup file

**Error Responses**:
- `404 Not Found`: Backup not found
- `410 Gone`: Backup file no longer exists on disk

### 1.5 Delete Backup

**Endpoint**: `DELETE /api/v1/backups/{backup_id}`

**Description**: Deletes a backup and its associated files

**Path Parameters**:
- `backup_id`: UUID of the backup

**Query Parameters**:
- `force`: boolean - Force delete even if backup is in use (default: false)

**Response** (200 OK):
```typescript
interface DeleteBackupResponse {
  message: string;
  backup_id: string;
  deleted_at: string;               // ISO 8601
  freed_bytes: number;
  files_deleted: number;
}
```

### 1.6 Get Backup Job Status

**Endpoint**: `GET /api/v1/backups/jobs/{job_id}`

**Description**: Retrieves the status of a backup job

**Path Parameters**:
- `job_id`: UUID of the backup job

**Response** (200 OK):
```typescript
interface BackupJobStatus {
  job_id: string;
  backup_id?: string;               // Available once backup is created
  status: JobStatus;
  progress: {
    current_step: string;
    total_steps: number;
    completed_steps: number;
    percentage: number;             // 0-100
    current_operation: string;
    documents_processed: number;
    documents_total?: number;
    bytes_written: number;
    elapsed_seconds: number;
    estimated_remaining_seconds?: number;
  };
  started_at: string;               // ISO 8601
  updated_at: string;               // ISO 8601
  completed_at?: string;            // ISO 8601
  error?: {
    message: string;
    code: string;
    details?: any;
  };
}
```

## 2. Restore Operations Endpoints

### 2.1 Create Restore Job

**Endpoint**: `POST /api/v1/restore`

**Description**: Initiates a restore operation from a backup

**Request Body**:
```typescript
interface CreateRestoreRequest {
  backup_id: string;                // Required, UUID of backup to restore
  mode: RestoreMode;                // Required: 'full' | 'selective' | 'merge'
  target?: RestoreTarget;           // Optional, where to restore
  options?: RestoreOptions;         // Optional, restore configuration
  selections?: RestoreSelections;   // Required for 'selective' mode
}

enum RestoreMode {
  FULL = 'full',                    // Restore everything
  SELECTIVE = 'selective',          // Restore selected items
  MERGE = 'merge'                   // Merge with existing data
}

interface RestoreTarget {
  project_id?: string;              // Target project (creates new if not specified)
  project_name?: string;            // Name for new project
  project_name_suffix?: string;     // Suffix to add to project names (default: "_restored")
}

interface RestoreOptions {
  overwrite_existing?: boolean;     // Default: false
  skip_duplicates?: boolean;        // Default: true
  maintain_ids?: boolean;           // Default: false, keep original IDs
  validate_before_restore?: boolean; // Default: true
  dry_run?: boolean;                // Default: false, preview only
  on_conflict?: ConflictResolution; // Default: 'skip'
}

enum ConflictResolution {
  SKIP = 'skip',
  OVERWRITE = 'overwrite',
  RENAME = 'rename',
  MERGE = 'merge'
}

interface RestoreSelections {
  projects?: string[];              // Project IDs to restore
  sessions?: string[];              // Session IDs to restore
  messages?: string[];              // Message IDs to restore
  prompts?: string[];               // Prompt IDs to restore
  date_range?: {
    start: string;                  // ISO 8601
    end: string;                    // ISO 8601
  };
  exclude_projects?: string[];      // Projects to exclude
  exclude_sessions?: string[];      // Sessions to exclude
}
```

**Response** (202 Accepted):
```typescript
interface CreateRestoreResponse {
  job_id: string;                   // UUID of restore job
  status: JobStatus;
  mode: RestoreMode;
  estimated_documents: number;
  estimated_duration_seconds: number;
  validation_results?: {
    is_valid: boolean;
    warnings: string[];
    errors: string[];
    conflicts: ConflictInfo[];
  };
}

interface ConflictInfo {
  type: 'project' | 'session' | 'message' | 'prompt';
  existing_id: string;
  backup_id: string;
  existing_name?: string;
  backup_name?: string;
  resolution: ConflictResolution;
}
```

### 2.2 Upload and Restore Backup

**Endpoint**: `POST /api/v1/restore/upload`

**Description**: Uploads an external backup file and optionally restores it

**Request** (multipart/form-data):
```typescript
interface UploadRestoreRequest {
  file: File;                       // The backup file (required)
  auto_restore?: boolean;           // Start restore immediately (default: false)
  restore_options?: string;         // JSON string of RestoreOptions
}
```

**Response** (202 Accepted):
```typescript
interface UploadRestoreResponse {
  upload_id: string;                // UUID of upload
  backup_id?: string;               // UUID of created backup entry
  status: UploadStatus;
  file_info: {
    filename: string;
    size_bytes: number;
    mime_type: string;
    checksum: string;
  };
  validation: {
    format_valid: boolean;
    version: string;
    compatibility: 'compatible' | 'needs_migration' | 'incompatible';
    contents_summary?: BackupContents;
    errors?: string[];
    warnings?: string[];
  };
  restore_job_id?: string;          // If auto_restore was true
}

enum UploadStatus {
  UPLOADING = 'uploading',
  VALIDATING = 'validating',
  READY = 'ready',
  RESTORING = 'restoring',
  FAILED = 'failed'
}
```

### 2.3 Preview Backup Contents

**Endpoint**: `GET /api/v1/restore/preview/{backup_id}`

**Description**: Preview backup contents before restoration

**Path Parameters**:
- `backup_id`: UUID of the backup

**Query Parameters**:
- `detailed`: boolean - Include detailed item lists (default: false)
- `check_conflicts`: boolean - Check for conflicts with existing data (default: true)

**Response** (200 OK):
```typescript
interface BackupPreviewResponse {
  backup_id: string;
  created_at: string;
  contents: {
    projects: ProjectPreview[];
    sessions_summary: {
      total: number;
      by_project: Record<string, number>;
      date_range?: {
        earliest: string;
        latest: string;
      };
    };
    messages_summary: {
      total: number;
      by_type: Record<string, number>;
      average_per_session: number;
    };
    prompts: PromptPreview[];
  };
  restore_analysis: {
    can_restore: boolean;
    has_conflicts: boolean;
    conflicts_count: number;
    conflicts?: ConflictInfo[];
    estimated_time_seconds: number;
    required_space_bytes: number;
    recommendations: string[];
  };
}

interface ProjectPreview {
  _id: string;
  name: string;
  description?: string;
  sessions_count: number;
  messages_count: number;
  created_at: string;
  updated_at: string;
  exists_in_system: boolean;
}

interface PromptPreview {
  _id: string;
  name: string;
  category?: string;
  tags?: string[];
  usage_count: number;
  exists_in_system: boolean;
}
```

### 2.4 Get Restore Job Status

**Endpoint**: `GET /api/v1/restore/jobs/{job_id}`

**Description**: Retrieves the status of a restore job

**Path Parameters**:
- `job_id`: UUID of the restore job

**Response** (200 OK):
```typescript
interface RestoreJobStatus {
  job_id: string;
  status: JobStatus;
  mode: RestoreMode;
  backup_id: string;
  progress: {
    current_operation: string;
    collections_processed: string[];
    collections_remaining: string[];
    documents_restored: number;
    documents_skipped: number;
    documents_failed: number;
    documents_total?: number;
    percentage: number;
    elapsed_seconds: number;
    estimated_remaining_seconds?: number;
  };
  started_at: string;
  updated_at: string;
  completed_at?: string;
  results?: {
    projects_restored: number;
    sessions_restored: number;
    messages_restored: number;
    prompts_restored: number;
    total_documents: number;
    skipped_duplicates: number;
    failed_documents: number;
    id_mappings?: Record<string, string>; // old_id -> new_id
  };
  errors?: RestoreError[];
}

interface RestoreError {
  timestamp: string;
  collection: string;
  document_id?: string;
  error_code: string;
  message: string;
  details?: any;
}
```

### 2.5 Cancel Restore Job

**Endpoint**: `POST /api/v1/restore/jobs/{job_id}/cancel`

**Description**: Cancels an in-progress restore job

**Path Parameters**:
- `job_id`: UUID of the restore job

**Response** (200 OK):
```typescript
interface CancelRestoreResponse {
  job_id: string;
  status: 'cancelled';
  cancelled_at: string;
  documents_restored: number;
  rollback_available: boolean;
  message: string;
}
```

## 3. Backup Configuration Endpoints

### 3.1 Get Backup Settings

**Endpoint**: `GET /api/v1/settings/backup`

**Description**: Retrieves current backup configuration

**Response** (200 OK):
```typescript
interface BackupSettings {
  storage: {
    backend: 'filesystem' | 's3' | 'azure';
    filesystem?: {
      base_directory: string;
      max_size_gb?: number;
      current_usage_gb: number;
    };
    s3?: {
      bucket: string;
      region: string;
      prefix?: string;
    };
  };
  retention: {
    enabled: boolean;
    max_backups?: number;
    max_age_days?: number;
    max_total_size_gb?: number;
    auto_cleanup: boolean;
    cleanup_schedule?: string;      // Cron expression
  };
  compression: {
    enabled: boolean;
    algorithm: 'gzip' | 'brotli' | 'zstd';
    level: number;                  // 1-9
  };
  encryption: {
    enabled: boolean;
    algorithm?: 'aes-256-gcm' | 'aes-256-cbc';
    key_management?: 'local' | 'vault' | 'kms';
  };
  scheduling: {
    enabled: boolean;
    schedules: BackupSchedule[];
  };
  notifications: {
    enabled: boolean;
    email_recipients?: string[];
    webhook_url?: string;
    notify_on: string[];            // ['success', 'failure', 'warning']
  };
}

interface BackupSchedule {
  _id: string;
  name: string;
  enabled: boolean;
  schedule: string;                 // Cron expression
  type: BackupType;
  filters?: BackupFilters;
  options?: BackupOptions;
  last_run?: string;
  next_run?: string;
}
```

### 3.2 Update Backup Settings

**Endpoint**: `PUT /api/v1/settings/backup`

**Description**: Updates backup configuration

**Request Body**:
```typescript
interface UpdateBackupSettingsRequest {
  storage?: Partial<BackupSettings['storage']>;
  retention?: Partial<BackupSettings['retention']>;
  compression?: Partial<BackupSettings['compression']>;
  encryption?: Partial<BackupSettings['encryption']>;
  scheduling?: Partial<BackupSettings['scheduling']>;
  notifications?: Partial<BackupSettings['notifications']>;
}
```

**Response** (200 OK):
```typescript
interface UpdateBackupSettingsResponse {
  message: string;
  updated_fields: string[];
  settings: BackupSettings;
  validation_warnings?: string[];
}
```

## 4. Backup Statistics Endpoints

### 4.1 Get Backup Statistics

**Endpoint**: `GET /api/v1/backups/statistics`

**Description**: Retrieves backup usage statistics and analytics

**Query Parameters**:
- `period`: 'day' | 'week' | 'month' | 'year' (default: 'month')
- `from`: ISO 8601 date-time
- `to`: ISO 8601 date-time

**Response** (200 OK):
```typescript
interface BackupStatistics {
  summary: {
    total_backups: number;
    total_size_bytes: number;
    average_size_bytes: number;
    largest_backup_bytes: number;
    oldest_backup: string;
    newest_backup: string;
    success_rate: number;           // Percentage
  };
  by_type: Record<BackupType, {
    count: number;
    total_size_bytes: number;
    average_size_bytes: number;
  }>;
  by_status: Record<BackupStatus, number>;
  timeline: {
    period: string;
    data: TimelineData[];
  };
  storage_usage: {
    used_bytes: number;
    available_bytes?: number;
    quota_bytes?: number;
    percentage_used?: number;
  };
  restore_statistics: {
    total_restores: number;
    successful_restores: number;
    failed_restores: number;
    average_restore_time_seconds: number;
  };
}

interface TimelineData {
  date: string;
  backups_created: number;
  backups_deleted: number;
  total_size_bytes: number;
  restores_performed: number;
}
```

## 5. Error Response Format

All error responses follow this standard format:

```typescript
interface ErrorResponse {
  error: {
    code: string;                   // Machine-readable error code
    message: string;                // Human-readable error message
    details?: any;                  // Additional error details
    timestamp: string;              // ISO 8601
    path: string;                   // API path that generated the error
    request_id?: string;            // Request tracking ID
  };
  validation_errors?: ValidationError[];
}

interface ValidationError {
  field: string;                    // Field path (e.g., "filters.date_range.start")
  message: string;                  // Validation error message
  code: string;                     // Validation error code
  value?: any;                     // The invalid value
}
```

## 6. Common Error Codes

| HTTP Status | Error Code | Description |
|------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Request body is malformed or invalid |
| 400 | `VALIDATION_FAILED` | Request validation failed |
| 400 | `INVALID_BACKUP_TYPE` | Invalid backup type specified |
| 400 | `INVALID_DATE_RANGE` | Date range is invalid |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | User lacks required permissions |
| 404 | `BACKUP_NOT_FOUND` | Specified backup does not exist |
| 404 | `JOB_NOT_FOUND` | Specified job does not exist |
| 409 | `BACKUP_IN_PROGRESS` | Another backup is already in progress |
| 409 | `RESTORE_IN_PROGRESS` | Another restore is already in progress |
| 410 | `BACKUP_FILE_MISSING` | Backup file no longer exists |
| 413 | `FILE_TOO_LARGE` | Upload file exceeds size limit |
| 422 | `INCOMPATIBLE_VERSION` | Backup version is incompatible |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Internal server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |
| 507 | `INSUFFICIENT_STORAGE` | Not enough storage space |

## 7. WebSocket Events (Real-time Updates)

### Backup Progress Events

**Channel**: `/ws/backups/{job_id}`

**Events**:
```typescript
interface BackupProgressEvent {
  type: 'backup.progress';
  job_id: string;
  backup_id?: string;
  progress: {
    percentage: number;
    current_operation: string;
    documents_processed: number;
    bytes_written: number;
  };
  timestamp: string;
}

interface BackupCompletedEvent {
  type: 'backup.completed';
  job_id: string;
  backup_id: string;
  size_bytes: number;
  duration_seconds: number;
  timestamp: string;
}

interface BackupFailedEvent {
  type: 'backup.failed';
  job_id: string;
  error: {
    code: string;
    message: string;
  };
  timestamp: string;
}
```

### Restore Progress Events

**Channel**: `/ws/restore/{job_id}`

**Events**:
```typescript
interface RestoreProgressEvent {
  type: 'restore.progress';
  job_id: string;
  progress: {
    percentage: number;
    current_collection: string;
    documents_restored: number;
    documents_skipped: number;
  };
  timestamp: string;
}

interface RestoreCompletedEvent {
  type: 'restore.completed';
  job_id: string;
  documents_restored: number;
  duration_seconds: number;
  timestamp: string;
}
```

## 8. Rate Limiting

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| POST /api/v1/backups | 10 requests | 1 hour |
| POST /api/v1/restore | 5 requests | 1 hour |
| POST /api/v1/restore/upload | 3 requests | 1 hour |
| GET /api/v1/backups/*/download | 20 requests | 1 hour |
| All other endpoints | 100 requests | 1 minute |

## 9. Implementation Notes

### Backend (Python/FastAPI)

1. **Service Layer**:
   - `BackupService`: Handles backup creation, listing, deletion
   - `RestoreService`: Handles restore operations
   - `StorageService`: Abstracts storage backend (filesystem, S3, etc.)
   - `ValidationService`: Validates backups and handles integrity checks

2. **Background Jobs**:
   - Use Celery or similar for async backup/restore operations
   - Implement progress tracking via Redis or database
   - Stream large datasets to avoid memory issues

3. **Data Streaming**:
   - Use MongoDB aggregation pipelines with cursor for large datasets
   - Implement chunked reading/writing for files
   - Use compression streams for on-the-fly compression

4. **Security**:
   - Validate all file paths to prevent directory traversal
   - Implement checksum verification for all backups
   - Use secure temporary directories for uploads
   - Sanitize filenames and paths

### Frontend (React/TypeScript)

1. **API Client**:
   ```typescript
   class BackupAPIClient {
     async createBackup(request: CreateBackupRequest): Promise<CreateBackupResponse>
     async listBackups(params: ListBackupsParams): Promise<PagedBackupsResponse>
     async downloadBackup(backupId: string): Promise<Blob>
     async restoreBackup(request: CreateRestoreRequest): Promise<CreateRestoreResponse>
     async getJobStatus(jobId: string): Promise<BackupJobStatus | RestoreJobStatus>
   }
   ```

2. **React Query Hooks**:
   ```typescript
   useBackupList(params: ListBackupsParams)
   useCreateBackup()
   useRestoreBackup()
   useBackupJobStatus(jobId: string)
   useRestorePreview(backupId: string)
   ```

3. **WebSocket Integration**:
   ```typescript
   useBackupProgress(jobId: string)
   useRestoreProgress(jobId: string)
   ```

4. **UI Components**:
   - `BackupWizard`: Multi-step backup creation
   - `RestoreWizard`: Multi-step restore with preview
   - `BackupTable`: Sortable, filterable backup list
   - `ProgressMonitor`: Real-time progress display
   - `ConflictResolver`: Interactive conflict resolution

## 10. Testing Requirements

### Unit Tests
- Validation logic for all request DTOs
- Backup filter application
- Compression/decompression
- Checksum calculation
- File streaming handlers

### Integration Tests
- End-to-end backup creation and download
- Restore with conflict resolution
- Upload and validation flow
- WebSocket event streaming
- Rate limiting enforcement

### Performance Tests
- Large backup creation (>1GB)
- Concurrent backup operations
- Restore of 100k+ documents
- Memory usage during streaming

### Security Tests
- Path traversal prevention
- File upload validation
- API authentication/authorization
- Rate limiting effectiveness

## 11. Migration Guide

### From Version 0.x to 1.0
- Backup format changes require migration tool
- Run migration script before first restore
- Old backups remain readable but should be recreated

## 12. Compliance Considerations

### GDPR
- Backups contain personal data - handle accordingly
- Implement data retention policies
- Support right to erasure in backups

### HIPAA
- Enable encryption for healthcare deployments
- Audit log all backup/restore operations
- Implement access controls

## Document Information

- **Version**: 1.0.0
- **Last Updated**: January 2025
- **Status**: Ready for Implementation
- **Authors**: ClaudeLens Team
- **Review Status**: Approved for Development

---

This contract serves as the definitive agreement between frontend and backend teams for the backup/restore feature implementation. Any deviations must be documented and communicated to both teams.
