# Import/Export Feature - API Contract

## Overview

This document defines the API contract between the ClaudeLens backend and frontend for the Import/Export feature. All endpoints, data models, and validation rules specified here must be implemented consistently across both systems.

**Base URL**: `/api/v1`
**Content-Type**: `application/json` (unless specified otherwise)
**Authentication**: Bearer token in Authorization header

## Export API Endpoints

### 1. Create Export Job

Creates a new export job with specified filters and options.

**Endpoint**: `POST /api/v1/export`

**Request Body**:
```typescript
interface CreateExportRequest {
  format: 'json' | 'csv' | 'markdown' | 'pdf';
  filters?: {
    dateRange?: {
      start: string;  // ISO 8601 format
      end: string;    // ISO 8601 format
    };
    projectIds?: string[];      // Array of project IDs
    sessionIds?: string[];      // Array of session IDs
    tags?: string[];           // Array of tags
    model?: string;            // Model identifier
    costRange?: {
      min: number;             // Minimum cost in USD
      max: number;             // Maximum cost in USD
    };
    messageTypes?: ('user' | 'assistant' | 'tool_use' | 'tool_result' | 'system')[];
  };
  options?: {
    includeMessages?: boolean;   // Default: true
    includeMetadata?: boolean;   // Default: true
    includeToolCalls?: boolean;  // Default: true
    compress?: boolean;          // Default: false
    splitSizeMb?: number;        // File split size in MB (1-500)
    encryption?: {
      enabled: boolean;
      password?: string;         // Required if enabled
    };
    privacy?: {
      redactPii?: boolean;       // Default: false
      anonymizeUsers?: boolean;  // Default: false
      removeApiKeys?: boolean;   // Default: true
    };
  };
}
```

**Response** (201 Created):
```typescript
interface CreateExportResponse {
  jobId: string;                        // Unique job identifier
  status: 'queued' | 'processing';      // Initial status
  estimatedSizeBytes: number;           // Estimated file size
  estimatedDurationSeconds: number;     // Estimated processing time
  createdAt: string;                    // ISO 8601 timestamp
  expiresAt: string;                    // ISO 8601 timestamp
}
```

**Validation Rules**:
- `format`: Required, must be one of the specified values
- `filters.dateRange`: If provided, start must be before end
- `filters.costRange`: If provided, min must be <= max
- `options.splitSizeMb`: If provided, must be between 1 and 500
- `options.encryption.password`: Required if encryption.enabled is true, min 8 chars

**Error Responses**:
- 400: Invalid request parameters
- 401: Unauthorized
- 429: Rate limit exceeded

---

### 2. Get Export Job Status

Retrieves the current status and progress of an export job.

**Endpoint**: `GET /api/v1/export/{jobId}/status`

**Path Parameters**:
- `jobId`: Export job identifier

**Response** (200 OK):
```typescript
interface ExportStatusResponse {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress?: {
    current: number;      // Current processed items
    total: number;        // Total items to process
    percentage: number;   // Progress percentage (0-100)
  };
  currentItem?: string;   // Currently processing item description
  fileInfo?: {
    format: string;
    sizeBytes: number;
    conversationsCount: number;
    messagesCount: number;
  };
  errors?: Array<{
    code: string;
    message: string;
    details?: any;
  }>;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  expiresAt: string;
}
```

**Error Responses**:
- 404: Export job not found
- 401: Unauthorized

---

### 3. Download Export File

Downloads the completed export file.

**Endpoint**: `GET /api/v1/export/{jobId}/download`

**Path Parameters**:
- `jobId`: Export job identifier

**Headers**:
- `Content-Type`: `application/octet-stream`
- `Content-Disposition`: `attachment; filename="claudelens_export_{timestamp}.{ext}"`
- `Content-Length`: File size in bytes

**Response** (200 OK): Binary file data

**Error Responses**:
- 404: Export job not found or file not ready
- 401: Unauthorized
- 410: Export file expired

---

### 4. Cancel Export Job

Cancels a running export job.

**Endpoint**: `DELETE /api/v1/export/{jobId}`

**Path Parameters**:
- `jobId`: Export job identifier

**Response** (200 OK):
```typescript
interface CancelExportResponse {
  jobId: string;
  status: 'cancelled';
  message: string;
}
```

**Error Responses**:
- 404: Export job not found
- 400: Job cannot be cancelled (already completed)
- 401: Unauthorized

---

### 5. List Export Jobs

Lists all export jobs for the current user.

**Endpoint**: `GET /api/v1/export`

**Query Parameters**:
- `page`: Page number (default: 0)
- `size`: Page size (default: 20, max: 100)
- `sort`: Sort field and direction (e.g., "createdAt,desc")
- `status`: Filter by status

**Response** (200 OK):
```typescript
interface PagedExportJobsResponse {
  content: Array<{
    jobId: string;
    status: string;
    format: string;
    createdAt: string;
    completedAt?: string;
    fileInfo?: {
      sizeBytes: number;
      conversationsCount: number;
    };
  }>;
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
}
```

---

## Import API Endpoints

### 1. Upload and Validate Import File

Uploads a file and validates its format and content.

**Endpoint**: `POST /api/v1/import/validate`

**Content-Type**: `multipart/form-data`

**Request Body**:
```typescript
interface ValidateImportRequest {
  file: File;           // Binary file data
  options?: {
    dryRun?: boolean;   // Default: true
  };
}
```

**Response** (200 OK):
```typescript
interface ValidateImportResponse {
  fileId: string;              // Temporary file identifier
  valid: boolean;              // Overall validation result
  format: string;              // Detected file format
  fileInfo: {
    sizeBytes: number;
    conversationsCount: number;
    messagesCount: number;
    dateRange?: {
      start: string;
      end: string;
    };
  };
  fieldMapping: {
    detectedFields: string[];   // Fields found in file
    mappingSuggestions: Record<string, string>; // Suggested mappings
  };
  validationWarnings: Array<{
    field?: string;
    message: string;
    severity: 'warning' | 'info';
  }>;
  validationErrors: Array<{
    field?: string;
    message: string;
    line?: number;
  }>;
}
```

**Validation Rules**:
- File size: Max 100MB
- Supported formats: JSON, CSV, Markdown
- File must be readable and properly formatted

**Error Responses**:
- 400: Invalid file format or size exceeded
- 401: Unauthorized
- 422: File validation failed

---

### 2. Check Import Conflicts

Analyzes potential conflicts before import execution.

**Endpoint**: `POST /api/v1/import/conflicts`

**Request Body**:
```typescript
interface CheckConflictsRequest {
  fileId: string;                        // From validation response
  fieldMapping: Record<string, string>;  // Field mappings
}
```

**Response** (200 OK):
```typescript
interface ConflictsResponse {
  conflictsCount: number;
  conflicts: Array<{
    existingId: string;
    importId: string;
    title: string;
    existingData: {
      messagesCount: number;
      lastUpdated: string;
      costUsd: number;
    };
    importData: {
      messagesCount: number;
      lastUpdated: string;
      costUsd: number;
    };
    suggestedAction: 'skip' | 'replace' | 'merge';
  }>;
}
```

**Error Responses**:
- 404: File not found or expired
- 400: Invalid field mapping
- 401: Unauthorized

---

### 3. Execute Import

Executes the import with specified conflict resolution.

**Endpoint**: `POST /api/v1/import/execute`

**Request Body**:
```typescript
interface ExecuteImportRequest {
  fileId: string;                        // From validation response
  fieldMapping: Record<string, string>;  // Field mappings
  conflictResolution: {
    defaultStrategy: 'skip' | 'replace' | 'merge';
    specificResolutions?: Record<string, 'skip' | 'replace' | 'merge'>;
  };
  options?: {
    createBackup?: boolean;      // Default: true
    validateReferences?: boolean; // Default: true
    calculateCosts?: boolean;    // Default: true
  };
}
```

**Response** (202 Accepted):
```typescript
interface ExecuteImportResponse {
  jobId: string;                        // Import job identifier
  status: 'processing';
  estimatedDurationSeconds: number;
}
```

**Validation Rules**:
- `fileId`: Must reference a valid, non-expired file
- `fieldMapping`: All required fields must be mapped
- `conflictResolution.defaultStrategy`: Required

**Error Responses**:
- 404: File not found or expired
- 400: Invalid configuration
- 401: Unauthorized
- 409: Unresolved conflicts

---

### 4. Get Import Progress

Retrieves the current progress of an import job.

**Endpoint**: `GET /api/v1/import/{jobId}/progress`

**Path Parameters**:
- `jobId`: Import job identifier

**Response** (200 OK):
```typescript
interface ImportProgressResponse {
  jobId: string;
  status: 'processing' | 'completed' | 'failed' | 'partial';
  progress: {
    processed: number;
    total: number;
    percentage: number;
    currentItem?: string;
  };
  statistics: {
    imported: number;
    skipped: number;
    failed: number;
    merged: number;
    replaced: number;
  };
  errors?: Array<{
    itemId: string;
    error: string;
    details?: string;
  }>;
  completedAt?: string;
}
```

**Error Responses**:
- 404: Import job not found
- 401: Unauthorized

---

### 5. Rollback Import

Rolls back a completed or partially completed import.

**Endpoint**: `POST /api/v1/import/{jobId}/rollback`

**Path Parameters**:
- `jobId`: Import job identifier

**Response** (200 OK):
```typescript
interface RollbackResponse {
  jobId: string;
  status: 'rolled_back';
  itemsReverted: number;
  message: string;
}
```

**Error Responses**:
- 404: Import job not found
- 400: Import cannot be rolled back (no backup or too old)
- 401: Unauthorized

---

## WebSocket Events

### Connection

**URL**: `wss://api.claudelens.com/ws`

**Authentication**: Pass Bearer token as query parameter or in first message

### Export Progress Events

**Subscribe to Export**:
```typescript
interface SubscribeExportMessage {
  type: 'subscribe';
  channel: 'export';
  jobId: string;
}
```

**Export Progress Update**:
```typescript
interface ExportProgressEvent {
  type: 'export_progress';
  jobId: string;
  progress: {
    current: number;
    total: number;
    percentage: number;
    currentItem?: string;
  };
  timestamp: string;
}
```

**Export Complete**:
```typescript
interface ExportCompleteEvent {
  type: 'export_complete';
  jobId: string;
  downloadUrl: string;
  expiresAt: string;
  timestamp: string;
}
```

**Export Failed**:
```typescript
interface ExportFailedEvent {
  type: 'export_failed';
  jobId: string;
  error: {
    code: string;
    message: string;
  };
  timestamp: string;
}
```

### Import Progress Events

**Subscribe to Import**:
```typescript
interface SubscribeImportMessage {
  type: 'subscribe';
  channel: 'import';
  jobId: string;
}
```

**Import Progress Update**:
```typescript
interface ImportProgressEvent {
  type: 'import_progress';
  jobId: string;
  progress: {
    current: number;
    total: number;
    percentage: number;
    currentItem?: string;
  };
  statistics: {
    imported: number;
    skipped: number;
    failed: number;
  };
  timestamp: string;
}
```

**Import Complete**:
```typescript
interface ImportCompleteEvent {
  type: 'import_complete';
  jobId: string;
  statistics: {
    imported: number;
    skipped: number;
    failed: number;
    merged: number;
    replaced: number;
  };
  timestamp: string;
}
```

---

## Common Data Models

### Exported Conversation Format

```typescript
interface ExportedConversation {
  id: string;
  externalId?: string;
  title: string;
  summary?: string;
  projectId?: string;
  projectName?: string;
  createdAt: string;       // ISO 8601
  updatedAt: string;       // ISO 8601
  durationSeconds?: number;
  model: string;
  costUsd: number;
  messageCount: number;
  tags: string[];
  metadata: {
    browser?: string;
    platform?: string;
    userAgent?: string;
    customFields?: Record<string, any>;
  };
  messages: ExportedMessage[];
  branches?: ConversationBranch[];
  parentConversationId?: string;
}
```

### Exported Message Format

```typescript
interface ExportedMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'tool_use' | 'tool_result';
  content: string;
  timestamp: string;      // ISO 8601
  tokens?: {
    input: number;
    output: number;
  };
  costUsd?: number;
  model?: string;
  toolName?: string;
  toolInput?: any;
  attachments?: Array<{
    id: string;
    type: string;
    name: string;
    url?: string;
    content?: string;
  }>;
  metadata?: Record<string, any>;
}
```

### Conversation Branch Format

```typescript
interface ConversationBranch {
  id: string;
  parentMessageId: string;
  createdAt: string;
  messages: ExportedMessage[];
}
```

---

## Error Response Format

All error responses follow this standard format:

```typescript
interface ErrorResponse {
  timestamp: string;      // ISO 8601
  status: number;         // HTTP status code
  error: string;          // Error type
  message: string;        // Human-readable message
  path: string;           // Request path
  errors?: Array<{        // Field-specific errors
    field: string;
    message: string;
    code?: string;
  }>;
  requestId?: string;     // For support reference
}
```

---

## Status Codes

### Success Codes
- **200 OK**: Successful GET, PUT requests
- **201 Created**: Successful POST creating new resource
- **202 Accepted**: Request accepted for async processing
- **204 No Content**: Successful DELETE

### Client Error Codes
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate)
- **410 Gone**: Resource expired
- **422 Unprocessable Entity**: Validation failed
- **429 Too Many Requests**: Rate limit exceeded

### Server Error Codes
- **500 Internal Server Error**: Unexpected server error
- **502 Bad Gateway**: Service temporarily unavailable
- **503 Service Unavailable**: System maintenance
- **504 Gateway Timeout**: Request timeout

---

## Rate Limiting

All endpoints are subject to rate limiting:

- **Export creation**: 10 requests per hour per user
- **Import execution**: 5 requests per hour per user
- **Status checks**: 60 requests per minute per user
- **File downloads**: 20 requests per hour per user

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## CORS Configuration

For frontend integration:

```yaml
allowed_origins:
  - https://app.claudelens.com
  - http://localhost:3000  # Development
allowed_methods:
  - GET
  - POST
  - PUT
  - DELETE
  - OPTIONS
allowed_headers:
  - Content-Type
  - Authorization
  - X-Request-ID
exposed_headers:
  - X-RateLimit-*
  - Content-Disposition
max_age: 3600
```

---

## Authentication

All requests must include a valid Bearer token:

```http
Authorization: Bearer <token>
```

Token requirements:
- Valid JWT signed by auth service
- Contains user ID and permissions
- Not expired
- Includes export/import scopes

---

## Implementation Notes

### Backend (FastAPI)

1. **Entity Mapping**: Use Pydantic models matching the TypeScript interfaces
2. **Validation**: Implement all validation rules using Pydantic validators
3. **Database**: Store job metadata in MongoDB, files in S3-compatible storage
4. **Background Jobs**: Use Celery or similar for async processing
5. **WebSocket**: Use FastAPI's WebSocket support for real-time updates

### Frontend (React/TypeScript)

1. **Type Safety**: Generate TypeScript types from this contract
2. **API Client**: Use axios or fetch with proper error handling
3. **State Management**: Use TanStack Query for API state
4. **WebSocket**: Use native WebSocket API or Socket.io client
5. **File Handling**: Use FormData for multipart uploads

### Testing

1. **Contract Tests**: Validate all endpoints match this specification
2. **Integration Tests**: Test complete export/import flows
3. **Load Tests**: Verify performance with large datasets
4. **Error Tests**: Validate all error scenarios
5. **WebSocket Tests**: Test real-time event delivery

---

## Security Considerations

1. **Input Validation**: Sanitize all user inputs
2. **File Security**: Scan uploads for malware
3. **Encryption**: Use AES-256 for file encryption
4. **Access Control**: Verify user owns resources
5. **Audit Logging**: Log all export/import operations
6. **Data Privacy**: Implement PII detection and redaction
7. **Rate Limiting**: Prevent abuse and DoS attacks

---

## Versioning

This API follows semantic versioning:
- Current version: 1.0.0
- Version in URL: `/api/v1/`
- Breaking changes require new major version
- Deprecation notice: 3 months minimum

---

## Support

For API issues or questions:
- Documentation: https://docs.claudelens.com/api/import-export
- Support: support@claudelens.com
- Status: https://status.claudelens.com
