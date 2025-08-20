# AI-Powered Prompt Library API Contract

## Overview
This document defines the API contract between the backend and frontend for AI-powered prompt features in ClaudeLens. It covers AI configuration, prompt generation, and template management endpoints.

## Base Configuration
- **Base URL**: `/api/v1`
- **Content-Type**: `application/json`
- **Authentication**: Bearer token via `X-API-Key` header
- **API Version**: v1

## 1. AI Settings Management

### 1.1 Get AI Settings
Retrieves current AI configuration without exposing sensitive data.

```yaml
Endpoint: GET /api/v1/settings/ai
Authorization: Required
Response: AISettingsResponse
```

#### Response DTO
```typescript
interface AISettingsResponse {
  enabled: boolean;
  configured: boolean;
  model?: string;
  endpoint?: string;
  hasApiKey: boolean;  // Never expose actual key
  templatesConfigured: boolean;
  availableModels: string[];
  usage?: {
    requestsToday: number;
    tokensUsed: number;
    lastUsed?: string;  // ISO 8601
  };
}
```

### 1.2 Update AI Settings
Updates AI configuration including API key.

```yaml
Endpoint: PUT /api/v1/settings/ai
Authorization: Required
Body: UpdateAISettingsRequest
Response: AISettingsResponse
```

#### Request DTO
```typescript
interface UpdateAISettingsRequest {
  apiKey?: string;      // Only sent when updating, min: 20, max: 200
  model: string;        // enum: ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
  endpoint?: string;    // Optional custom endpoint, valid URL
  enabled: boolean;
}
```

#### Validation Rules
- `apiKey`: Optional, 20-200 characters, starts with "sk-"
- `model`: Required, must be from available models list
- `endpoint`: Optional, valid HTTPS URL
- `enabled`: Required boolean

### 1.3 Test AI Connection
Tests the AI configuration to ensure it's working.

```yaml
Endpoint: POST /api/v1/settings/ai/test
Authorization: Required
Response: TestConnectionResponse
```

#### Response DTO
```typescript
interface TestConnectionResponse {
  success: boolean;
  message: string;
  modelInfo?: {
    name: string;
    maxTokens: number;
    supportsFunctions: boolean;
  };
  error?: {
    code: string;
    details: string;
  };
}
```

## 2. Prompt Generation Endpoints

### 2.1 Generate Prompt Metadata
Generates AI-powered name and description for prompts.

```yaml
Endpoint: POST /api/v1/prompts/ai/generate-metadata
Authorization: Required
Body: GenerateMetadataRequest
Response: GenerateMetadataResponse
```

#### Request DTO
```typescript
interface GenerateMetadataRequest {
  context: string;         // Required, 10-5000 chars
  type: GenerationType;    // enum: ['name', 'description', 'both']
  requirements?: string;   // Optional, max 1000 chars
  templateId?: string;     // Optional template UUID
  existingPrompt?: {       // Optional context
    name?: string;
    description?: string;
    content?: string;
  };
}

enum GenerationType {
  NAME = 'name',
  DESCRIPTION = 'description',
  BOTH = 'both'
}
```

#### Response DTO
```typescript
interface GenerateMetadataResponse {
  name?: string;           // Max 100 chars
  description?: string;    // Max 500 chars
  alternatives?: {         // Alternative suggestions
    names?: string[];
    descriptions?: string[];
  };
  generationId: string;    // UUID for tracking
  tokensUsed: number;
  processingTime: number;  // milliseconds
}
```

### 2.2 Generate Prompt Content
Generates or refactors prompt content using AI.

```yaml
Endpoint: POST /api/v1/prompts/ai/generate-content
Authorization: Required
Body: GenerateContentRequest
Response: GenerateContentResponse
```

#### Request DTO
```typescript
interface GenerateContentRequest {
  operation: ContentOperation;     // Required
  requirements: string;             // Required, 10-5000 chars
  existingContent?: string;         // Required for refactor/enhance
  preserveVariables?: boolean;      // Default: true
  templateId?: string;              // Optional template UUID
  variables?: VariableDefinition[]; // Optional variable definitions
  outputFormat?: string;            // Optional format hint
}

enum ContentOperation {
  CREATE = 'create',
  REFACTOR = 'refactor',
  ENHANCE = 'enhance'
}

interface VariableDefinition {
  name: string;          // Variable name without brackets
  description?: string;  // Variable purpose
  example?: string;      // Example value
  required?: boolean;
}
```

#### Response DTO
```typescript
interface GenerateContentResponse {
  content: string;                    // Generated content
  variables: ExtractedVariable[];     // Variables found in content
  changesSummary?: string;           // For refactor operations
  improvements?: string[];           // List of improvements made
  generationId: string;              // UUID for tracking
  tokensUsed: number;
  processingTime: number;            // milliseconds
}

interface ExtractedVariable {
  name: string;        // Variable name
  count: number;       // Occurrences in content
  preserved: boolean;  // Whether it was preserved from original
}
```

### 2.3 Regenerate Content
Regenerates previously generated content with modifications.

```yaml
Endpoint: POST /api/v1/prompts/ai/regenerate
Authorization: Required
Body: RegenerateRequest
Response: GenerateContentResponse
```

#### Request DTO
```typescript
interface RegenerateRequest {
  generationId: string;        // Previous generation ID
  modifications?: string;      // Additional requirements
  keepOriginalRequirements?: boolean;  // Default: true
}
```

## 3. Template Management

### 3.1 List Generation Templates
Retrieves all available generation templates.

```yaml
Endpoint: GET /api/v1/settings/ai/templates
Authorization: Required
Query Parameters:
  - type?: string (metadata|content|refactor)
  - includeSystem?: boolean (default: true)
Response: TemplateListResponse
```

#### Response DTO
```typescript
interface TemplateListResponse {
  templates: AITemplate[];
  defaults: {
    metadataGeneration: string;  // Template ID
    contentGeneration: string;
    contentRefactor: string;
  };
  total: number;
}

interface AITemplate {
  id: string;                   // UUID
  type: TemplateType;
  name: string;                 // Max 100 chars
  description?: string;         // Max 500 chars
  content: string;              // Template content
  variables: TemplateVariable[];
  isSystem: boolean;            // System templates can't be deleted
  isActive: boolean;
  isDefault: boolean;
  createdAt: string;           // ISO 8601
  updatedAt: string;           // ISO 8601
  createdBy?: string;          // User ID
  usageCount: number;
}

enum TemplateType {
  METADATA = 'metadata',
  CONTENT = 'content',
  REFACTOR = 'refactor'
}

interface TemplateVariable {
  name: string;               // Variable name
  description: string;        // Variable purpose
  required: boolean;
  defaultValue?: string;
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: string;       // Regex pattern
  };
}
```

### 3.2 Get Template by ID
Retrieves a specific template.

```yaml
Endpoint: GET /api/v1/settings/ai/templates/{templateId}
Authorization: Required
Path Parameters:
  - templateId: string (UUID)
Response: AITemplate
```

### 3.3 Create Template
Creates a new generation template.

```yaml
Endpoint: POST /api/v1/settings/ai/templates
Authorization: Required
Body: CreateTemplateRequest
Response: AITemplate (201 Created)
```

#### Request DTO
```typescript
interface CreateTemplateRequest {
  type: TemplateType;             // Required
  name: string;                   // Required, 2-100 chars
  description?: string;           // Optional, max 500 chars
  content: string;                // Required, 10-10000 chars
  variables?: TemplateVariable[]; // Optional
  isActive?: boolean;             // Default: true
  makeDefault?: boolean;          // Make this the default for its type
}
```

### 3.4 Update Template
Updates an existing template.

```yaml
Endpoint: PUT /api/v1/settings/ai/templates/{templateId}
Authorization: Required
Path Parameters:
  - templateId: string (UUID)
Body: UpdateTemplateRequest
Response: AITemplate
```

#### Request DTO
```typescript
interface UpdateTemplateRequest {
  name?: string;                  // 2-100 chars
  description?: string;           // Max 500 chars
  content?: string;               // 10-10000 chars
  variables?: TemplateVariable[];
  isActive?: boolean;
  makeDefault?: boolean;
}
```

### 3.5 Delete Template
Deletes a custom template (system templates cannot be deleted).

```yaml
Endpoint: DELETE /api/v1/settings/ai/templates/{templateId}
Authorization: Required
Path Parameters:
  - templateId: string (UUID)
Response: 204 No Content
```

### 3.6 Test Template
Tests a template with sample data.

```yaml
Endpoint: POST /api/v1/settings/ai/templates/{templateId}/test
Authorization: Required
Path Parameters:
  - templateId: string (UUID)
Body: TestTemplateRequest
Response: TestTemplateResponse
```

#### Request DTO
```typescript
interface TestTemplateRequest {
  variables: Record<string, string>;  // Variable values
  context?: string;                   // Additional context
}
```

#### Response DTO
```typescript
interface TestTemplateResponse {
  renderedPrompt: string;      // The final prompt sent to AI
  isValid: boolean;
  errors?: string[];
  warnings?: string[];
}
```

## 4. Generation Analytics

### 4.1 Get Generation Statistics
Retrieves AI generation usage statistics.

```yaml
Endpoint: GET /api/v1/analytics/ai-generation
Authorization: Required
Query Parameters:
  - startDate?: string (ISO 8601)
  - endDate?: string (ISO 8601)
  - groupBy?: string (day|week|month)
Response: GenerationAnalyticsResponse
```

#### Response DTO
```typescript
interface GenerationAnalyticsResponse {
  summary: {
    totalGenerations: number;
    totalTokensUsed: number;
    estimatedCost: number;      // In USD
    successRate: number;        // Percentage
    averageTokensPerRequest: number;
  };
  byType: {
    metadata: GenerationTypeStat;
    content: GenerationTypeStat;
    refactor: GenerationTypeStat;
  };
  timeline: TimelineEntry[];
  topTemplates: TemplateUsage[];
}

interface GenerationTypeStat {
  count: number;
  tokensUsed: number;
  averageProcessingTime: number;  // milliseconds
  acceptanceRate: number;         // Percentage
}

interface TimelineEntry {
  date: string;           // ISO 8601
  generations: number;
  tokensUsed: number;
  cost: number;
}

interface TemplateUsage {
  templateId: string;
  templateName: string;
  usageCount: number;
  successRate: number;
}
```

## 5. Error Responses

All endpoints follow a consistent error response format:

```typescript
interface ErrorResponse {
  timestamp: string;      // ISO 8601
  status: number;         // HTTP status code
  error: string;          // Error category
  message: string;        // User-friendly message
  path: string;           // Request path
  requestId?: string;     // For tracking
  errors?: ValidationError[];  // Field-specific errors
}

interface ValidationError {
  field: string;         // Field name
  message: string;       // Validation message
  code?: string;         // Error code
  rejectedValue?: any;   // The invalid value
}
```

### Common Error Scenarios

| Status | Error | Scenario |
|--------|-------|----------|
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | AI features not enabled or quota exceeded |
| 404 | Not Found | Template or resource not found |
| 409 | Conflict | Duplicate template name or concurrent modification |
| 422 | Unprocessable Entity | Valid JSON but semantic errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | OpenAI API unavailable |
| 503 | Service Unavailable | AI service temporarily unavailable |

## 6. Rate Limiting

AI generation endpoints are subject to rate limiting:

```yaml
Rate Limits:
  Per User:
    - 10 requests per minute
    - 100 requests per hour
    - 50,000 tokens per day

  Global:
    - 100 requests per minute
    - 10 concurrent AI requests
```

Rate limit headers included in responses:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp (Unix epoch)
- `X-AI-Tokens-Used`: Tokens used in this request
- `X-AI-Tokens-Remaining`: Daily tokens remaining

## 7. Backend Implementation Notes

### Python/FastAPI Implementation
```python
# Pydantic models for validation
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Enum
from datetime import datetime

class GenerationType(str, Enum):
    NAME = "name"
    DESCRIPTION = "description"
    BOTH = "both"

class GenerateMetadataRequest(BaseModel):
    context: str = Field(..., min_length=10, max_length=5000)
    type: GenerationType
    requirements: Optional[str] = Field(None, max_length=1000)
    template_id: Optional[str] = Field(None, regex="^[a-f0-9-]{36}$")

    @validator('context')
    def validate_context(cls, v):
        if not v.strip():
            raise ValueError('Context cannot be empty')
        return v

# Service layer for AI operations
class AIService:
    async def generate_metadata(
        self,
        request: GenerateMetadataRequest,
        user_id: str
    ) -> GenerateMetadataResponse:
        # Check AI settings
        # Build prompt from template
        # Call OpenAI API
        # Process and validate response
        # Log generation
        # Return formatted response
        pass

# Repository for template management
class TemplateRepository:
    async def find_by_type(
        self,
        type: TemplateType,
        include_system: bool = True
    ) -> List[AITemplate]:
        pass
```

### MongoDB Indexes
```javascript
// ai_settings collection
db.ai_settings.createIndex({ "user_id": 1 }, { unique: true })

// generation_templates collection
db.generation_templates.createIndex({ "type": 1, "is_active": 1 })
db.generation_templates.createIndex({ "name": 1 }, { unique: true })

// generation_logs collection
db.generation_logs.createIndex({ "user_id": 1, "created_at": -1 })
db.generation_logs.createIndex({ "generation_id": 1 }, { unique: true })
```

## 8. Frontend Implementation Notes

### TypeScript/React Implementation
```typescript
// API client configuration
import axios from 'axios';

const aiApi = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': getApiKey()
  }
});

// React Query hooks
import { useMutation, useQuery } from '@tanstack/react-query';

export const useGenerateMetadata = () => {
  return useMutation({
    mutationFn: (request: GenerateMetadataRequest) =>
      aiApi.post('/prompts/ai/generate-metadata', request),
    onError: (error) => {
      // Handle rate limiting, show user feedback
    }
  });
};

// Zod validation schemas
import { z } from 'zod';

const GenerateMetadataSchema = z.object({
  context: z.string().min(10).max(5000),
  type: z.enum(['name', 'description', 'both']),
  requirements: z.string().max(1000).optional(),
  templateId: z.string().uuid().optional()
});

// Zustand store for AI state
interface AIStore {
  settings: AISettingsResponse | null;
  isGenerating: boolean;
  generationError: string | null;

  generateMetadata: (request: GenerateMetadataRequest) => Promise<void>;
  updateSettings: (settings: UpdateAISettingsRequest) => Promise<void>;
}
```

## 9. Security Considerations

### API Key Storage
- Backend: Encrypt API keys using AES-256-GCM
- Never include API keys in logs or error messages
- Implement key rotation mechanism
- Audit all API key access

### Request Validation
- Sanitize all input to prevent prompt injection
- Validate template content for malicious patterns
- Implement request signing for sensitive operations
- Rate limit by IP and user

### Data Privacy
- Don't log full prompt content by default
- Implement data retention policies (30 days)
- Allow users to delete their generation history
- Anonymize data in analytics

## 10. Testing Requirements

### Integration Tests
```python
# Test AI generation flow
async def test_generate_metadata():
    # Mock OpenAI response
    # Test successful generation
    # Test rate limiting
    # Test error handling
    # Test template application
```

### Contract Tests
```typescript
// Validate API responses match contract
describe('AI API Contract', () => {
  it('should return valid metadata response', async () => {
    const response = await generateMetadata(request);
    expect(response).toMatchSchema(GenerateMetadataResponseSchema);
  });
});
```

## 11. Migration & Rollout

### Database Migrations
1. Create new collections: `ai_settings`, `generation_templates`, `generation_logs`
2. Add indexes for performance
3. Seed default templates
4. Add feature flags

### Feature Flags
```typescript
interface FeatureFlags {
  aiPromptGeneration: boolean;
  aiTemplates: boolean;
  aiAnalytics: boolean;
}
```

### Rollout Phases
1. **Phase 1**: Deploy backend with feature flag off
2. **Phase 2**: Enable for internal testing
3. **Phase 3**: Beta rollout to 10% of users
4. **Phase 4**: Full rollout with monitoring

## 12. Monitoring & Observability

### Metrics to Track
- AI API latency (p50, p95, p99)
- Generation success rate
- Token usage per user
- Template usage frequency
- Error rates by type

### Logging
```python
logger.info("AI generation started", extra={
    "user_id": user_id,
    "generation_type": request.type,
    "template_id": request.template_id,
    "request_id": request_id
})
```

### Alerts
- High error rate (>5%)
- Unusual token usage
- API key failures
- Rate limit breaches

---

**Contract Version**: 1.0.0
**Last Updated**: 2024-01-20
**Status**: Ready for Implementation
**Authors**: Backend & Frontend Teams

## Appendix: Example API Calls

### Complete Flow Example
```bash
# 1. Configure AI settings
curl -X PUT http://localhost:8000/api/v1/settings/ai \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "apiKey": "sk-...",
    "model": "gpt-4",
    "enabled": true
  }'

# 2. Test connection
curl -X POST http://localhost:8000/api/v1/settings/ai/test \
  -H "X-API-Key: your-api-key"

# 3. Generate metadata
curl -X POST http://localhost:8000/api/v1/prompts/ai/generate-metadata \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "A prompt for summarizing technical documentation",
    "type": "both",
    "requirements": "Make it concise and professional"
  }'

# 4. Generate content
curl -X POST http://localhost:8000/api/v1/prompts/ai/generate-content \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create",
    "requirements": "Create a prompt for technical documentation summary",
    "preserveVariables": true
  }'
```
