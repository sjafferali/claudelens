name: "AI-Powered Prompt Library Enhancement Implementation PRP"
description: |
  Production-ready implementation of OpenAI-powered prompt generation, refinement, and template management for ClaudeLens prompt library

---

## Goal

**Feature Goal**: Integrate OpenAI API capabilities into ClaudeLens prompt library to enable AI-assisted prompt generation, refinement, and intelligent template management

**Deliverable**: Complete AI integration system with configuration UI, generation endpoints, template management, and seamless prompt editor enhancements

**Success Definition**: Users can configure OpenAI API settings, generate/refine prompts using AI, and customize generation templates with full error handling and security

## User Persona

**Target User**: ClaudeLens power users and teams managing prompt libraries

**Use Case**: Creating effective prompts without extensive prompt engineering expertise

**User Journey**:
1. Configure OpenAI API settings in ClaudeLens settings page
2. Navigate to Prompts page and click "Create Prompt"
3. Use AI assistance to generate name/description from requirements
4. Generate or refine prompt content using natural language instructions
5. Test generated prompt with variables before saving

**Pain Points Addressed**:
- Time-consuming manual prompt writing
- Inconsistent prompt quality across team
- Difficulty optimizing prompts for effectiveness

## Why

- **Business Value**: Accelerate prompt creation from hours to minutes, improving team productivity
- **Integration**: Enhances existing prompt library without disrupting current workflows
- **Problems Solved**: Democratizes prompt engineering expertise, ensures consistent quality, reduces iteration time

## What

AI-powered features that integrate seamlessly into existing prompt management workflow:
- Configurable OpenAI integration with encrypted API key storage
- AI-assisted generation of prompt metadata (names, descriptions)
- Intelligent prompt content generation and refinement
- Customizable generation templates for organization standards
- Usage analytics and cost tracking

### Success Criteria

- [ ] OpenAI API settings configurable with secure key storage
- [ ] Generate button appears in prompt editor when AI is enabled
- [ ] AI can generate names, descriptions, and content from requirements
- [ ] Templates customizable for consistent generation patterns
- [ ] All AI operations have proper error handling and rate limiting
- [ ] Tests achieve >80% coverage for new AI features
- [ ] No disruption to existing prompt library functionality

## All Needed Context

### Context Completeness Check

_This PRP contains all file references, patterns, external documentation, and implementation details needed for successful one-pass implementation without prior knowledge of the codebase._

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: https://platform.openai.com/docs/api-reference/chat/create
  why: OpenAI chat completions API for prompt generation
  critical: Response format, error codes, rate limiting behavior

- url: https://github.com/openai/openai-python#async-usage
  why: Async OpenAI Python SDK patterns for FastAPI integration
  critical: AsyncOpenAI client initialization and error handling

- url: https://cookbook.openai.com/examples/how_to_handle_rate_limits
  why: Production rate limiting and retry strategies
  critical: Exponential backoff, token counting, batch processing

- file: backend/app/api/api_v1/endpoints/prompts.py
  why: Existing prompt endpoints to extend with AI features
  pattern: Route ordering, dependency injection, error handling
  gotcha: Routes must be ordered by specificity (most specific first)

- file: backend/app/services/prompt.py
  why: Prompt service patterns for business logic
  pattern: Variable extraction regex, service method structure
  gotcha: Variables use {{}} syntax, must preserve in AI generation

- file: backend/app/core/config.py
  why: Configuration management pattern for AI settings
  pattern: Pydantic settings with environment variables
  gotcha: Sensitive keys must use SecretStr type

- file: frontend/src/pages/Prompts.tsx
  why: Main prompts page to understand UI integration points
  pattern: React Query hooks, component structure
  gotcha: Uses Zustand for client state, React Query for server state

- file: frontend/src/hooks/usePrompts.ts
  why: React Query patterns for API integration
  pattern: Optimistic updates, cache invalidation
  gotcha: Must invalidate 'prompts' query key after mutations

- docfile: PRPs/ai_docs/openai-fastapi-integration.md
  why: Custom guide for production OpenAI + FastAPI patterns
  section: Async patterns and error handling

- docfile: PRPs/ai_docs/tiktoken-usage.md
  why: Token counting for cost estimation
  section: Model encodings and performance optimization
```

### Current Codebase tree (key directories)

```bash
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/
│   │           ├── prompts.py          # Extend with AI endpoints
│   │           └── websocket.py
│   ├── core/
│   │   ├── config.py                   # Add AI configuration
│   │   ├── database.py
│   │   └── security.py                 # Encryption utilities
│   ├── models/
│   │   └── prompt.py                   # Extend for AI metadata
│   ├── schemas/
│   │   └── prompt.py                   # Add AI request/response schemas
│   └── services/
│       ├── prompt.py                   # Extend with AI generation
│       └── validation.py
frontend/
├── src/
│   ├── api/
│   │   └── prompts.ts                  # Add AI API calls
│   ├── components/
│   │   └── prompts/
│   │       ├── PromptEditor.tsx        # Enhance with AI buttons
│   │       └── PromptPlayground.tsx
│   ├── hooks/
│   │   └── usePrompts.ts               # Add AI generation hooks
│   ├── pages/
│   │   ├── Prompts.tsx
│   │   └── Settings.tsx                # Add AI configuration UI
│   └── store/
│       └── index.ts                    # Add AI settings store
```

### Desired Codebase tree with files to be added

```bash
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/
│   │           ├── prompts.py          # (modified)
│   │           └── ai_settings.py      # NEW: AI configuration endpoints
│   ├── core/
│   │   ├── config.py                   # (modified)
│   │   └── ai_config.py               # NEW: AI-specific configuration
│   ├── models/
│   │   ├── prompt.py                   # (modified)
│   │   ├── ai_settings.py             # NEW: AI settings models
│   │   └── generation_template.py      # NEW: Template models
│   ├── schemas/
│   │   ├── prompt.py                   # (modified)
│   │   ├── ai_generation.py           # NEW: AI generation schemas
│   │   └── ai_settings.py             # NEW: AI settings schemas
│   └── services/
│       ├── prompt.py                   # (modified)
│       ├── ai_service.py              # NEW: OpenAI integration service
│       └── template_service.py         # NEW: Template management

frontend/
├── src/
│   ├── api/
│   │   ├── prompts.ts                  # (modified)
│   │   └── ai.ts                      # NEW: AI API client
│   ├── components/
│   │   ├── prompts/
│   │   │   ├── PromptEditor.tsx        # (modified)
│   │   │   ├── AIGenerationModal.tsx   # NEW: AI generation UI
│   │   │   └── AIAssistButton.tsx      # NEW: AI assist button
│   │   └── settings/
│   │       └── AISettingsPanel.tsx     # NEW: AI configuration UI
│   ├── hooks/
│   │   ├── usePrompts.ts               # (modified)
│   │   └── useAI.ts                    # NEW: AI operation hooks
│   └── store/
│       ├── index.ts                    # (modified)
│       └── aiStore.ts                  # NEW: AI state management
```

### Known Gotchas of our codebase & Library Quirks

```python
# CRITICAL: FastAPI route ordering - most specific routes must come first
# Example: /prompts/ai/generate-metadata BEFORE /prompts/{prompt_id}

# CRITICAL: MongoDB ObjectId serialization requires custom PyObjectId class
# Import from: app.models.prompt import PyObjectId

# CRITICAL: React Query cache keys must be arrays
# Example: ['prompts', 'ai', generationId] not 'prompts-ai-generationId'

# CRITICAL: Zustand store updates must be immutable
# Use: set((state) => ({ ...state, newField: value }))

# CRITICAL: OpenAI AsyncClient requires proper cleanup
# Always use async context manager: async with AsyncOpenAI() as client

# CRITICAL: Environment variables with OPENAI_ prefix may conflict
# Use CLAUDELENS_OPENAI_API_KEY instead of OPENAI_API_KEY
```

## Implementation Blueprint

### Data models and structure

```python
# backend/app/models/ai_settings.py
from pydantic import BaseModel, Field, SecretStr
from typing import Optional, Dict
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic models"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

class AISettingsInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    api_key_encrypted: str  # Encrypted with app.core.security
    model: str = "gpt-4"
    endpoint: Optional[str] = None
    enabled: bool = False
    usage_stats: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# backend/app/schemas/ai_generation.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from enum import Enum

class GenerationType(str, Enum):
    NAME = "name"
    DESCRIPTION = "description"
    BOTH = "both"

class ContentOperation(str, Enum):
    CREATE = "create"
    REFACTOR = "refactor"
    ENHANCE = "enhance"

class GenerateMetadataRequest(BaseModel):
    context: str = Field(..., min_length=10, max_length=5000)
    type: GenerationType
    requirements: Optional[str] = Field(None, max_length=1000)
    template_id: Optional[str] = None

    @validator('context')
    def validate_context(cls, v):
        if not v.strip():
            raise ValueError('Context cannot be empty')
        return v.strip()

class GenerateContentRequest(BaseModel):
    operation: ContentOperation
    requirements: str = Field(..., min_length=10, max_length=5000)
    existing_content: Optional[str] = None
    preserve_variables: bool = True
    template_id: Optional[str] = None
```

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE backend/app/core/ai_config.py
  - IMPLEMENT: AI configuration with encryption for API keys
  - FOLLOW pattern: backend/app/core/config.py (Settings class structure)
  - NAMING: AISettings class with pydantic-settings
  - PLACEMENT: Core configuration module
  - CRITICAL: Use SecretStr for api_key, validate model names

Task 2: CREATE backend/app/services/ai_service.py
  - IMPLEMENT: OpenAI integration service with async methods
  - FOLLOW pattern: backend/app/services/prompt.py (async service structure)
  - NAMING: AIService class with generate_metadata, generate_content methods
  - DEPENDENCIES: openai, tiktoken for token counting
  - PLACEMENT: Service layer
  - CRITICAL: Implement exponential backoff, proper error handling

Task 3: CREATE backend/app/api/api_v1/endpoints/ai_settings.py
  - IMPLEMENT: REST endpoints for AI configuration
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/prompts.py (FastAPI patterns)
  - NAMING: get_ai_settings, update_ai_settings, test_connection
  - DEPENDENCIES: Import AIService from Task 2
  - PLACEMENT: API endpoints layer
  - CRITICAL: Never expose raw API key in responses

Task 4: MODIFY backend/app/api/api_v1/endpoints/prompts.py
  - ADD: AI generation endpoints after line 50 (before generic routes)
  - IMPLEMENT: /prompts/ai/generate-metadata, /prompts/ai/generate-content
  - FOLLOW pattern: Existing endpoint structure with dependency injection
  - PRESERVE: All existing endpoints and their ordering
  - CRITICAL: Routes must be before /{prompt_id} routes

Task 5: CREATE frontend/src/api/ai.ts
  - IMPLEMENT: TypeScript API client for AI operations
  - FOLLOW pattern: frontend/src/api/prompts.ts (axios configuration)
  - NAMING: generateMetadata, generateContent, updateAISettings functions
  - DEPENDENCIES: Import shared axios instance
  - PLACEMENT: API client layer

Task 6: CREATE frontend/src/hooks/useAI.ts
  - IMPLEMENT: React Query hooks for AI operations
  - FOLLOW pattern: frontend/src/hooks/usePrompts.ts (mutation patterns)
  - NAMING: useGenerateMetadata, useGenerateContent, useAISettings
  - DEPENDENCIES: @tanstack/react-query
  - CRITICAL: Proper cache invalidation, optimistic updates

Task 7: CREATE frontend/src/components/prompts/AIAssistButton.tsx
  - IMPLEMENT: AI assistance button component for prompt editor
  - FOLLOW pattern: frontend/src/components/prompts/PromptEditor.tsx (component structure)
  - NAMING: AIAssistButton with onClick handler
  - DEPENDENCIES: useAI hooks from Task 6
  - PLACEMENT: Import into PromptEditor.tsx

Task 8: CREATE frontend/src/components/settings/AISettingsPanel.tsx
  - IMPLEMENT: Settings panel for AI configuration
  - FOLLOW pattern: Existing settings components
  - NAMING: AISettingsPanel with form validation
  - DEPENDENCIES: useAISettings hook
  - PLACEMENT: Import into Settings page

Task 9: CREATE backend/tests/test_services_ai.py
  - IMPLEMENT: Comprehensive tests for AI service
  - FOLLOW pattern: backend/tests/test_services_cost_calculation.py (mock patterns)
  - NAMING: test_generate_metadata_success, test_rate_limit_handling
  - MOCK: OpenAI API calls with unittest.mock
  - COVERAGE: Success, failure, rate limits, token counting

Task 10: CREATE frontend/src/components/__tests__/AIAssistButton.test.tsx
  - IMPLEMENT: React component tests
  - FOLLOW pattern: frontend/src/components/__tests__/SearchBar.test.tsx
  - NAMING: Standard React Testing Library patterns
  - MOCK: API calls and hooks
  - COVERAGE: User interactions, loading states, error handling
```

### Implementation Patterns & Key Details

```python
# backend/app/services/ai_service.py - Critical patterns
import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from cryptography.fernet import Fernet
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

class AIService:
    def __init__(self, db):
        self.db = db
        self.encryption_key = os.getenv("CLAUDELENS_ENCRYPTION_KEY")
        self.fernet = Fernet(self.encryption_key.encode())

    async def _get_client(self) -> AsyncOpenAI:
        """Get configured OpenAI client with decrypted API key"""
        settings = await self.db.ai_settings.find_one()
        if not settings or not settings.get("enabled"):
            raise ValueError("AI features not configured")

        # CRITICAL: Decrypt API key only when needed
        api_key = self.fernet.decrypt(settings["api_key_encrypted"]).decode()
        return AsyncOpenAI(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_metadata(
        self, request: GenerateMetadataRequest
    ) -> Dict[str, Any]:
        """Generate prompt metadata with retry logic"""
        # PATTERN: Token counting before API call
        encoding = tiktoken.encoding_for_model("gpt-4")
        prompt_tokens = len(encoding.encode(request.context))

        # GOTCHA: Check token limits before calling API
        if prompt_tokens > 4000:
            raise ValueError("Context too long, please reduce")

        async with await self._get_client() as client:
            # PATTERN: Structured prompt for consistent output
            system_prompt = """Generate concise, professional metadata for prompts.
            Return JSON with 'name' and/or 'description' fields."""

            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.context}
                ],
                response_format={"type": "json_object"},  # Force JSON output
                temperature=0.7,
                max_tokens=500
            )

            # CRITICAL: Log usage for cost tracking
            await self._log_usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                operation="generate_metadata"
            )

            return json.loads(response.choices[0].message.content)

# frontend/src/hooks/useAI.ts - React Query patterns
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { generateMetadata, generateContent, getAISettings } from '@/api/ai';
import toast from 'react-hot-toast';

export const useGenerateMetadata = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: generateMetadata,
    onSuccess: (data) => {
      // PATTERN: Show success feedback
      toast.success('Metadata generated successfully');
      // CRITICAL: Don't invalidate prompts query yet (user needs to save)
    },
    onError: (error: any) => {
      // PATTERN: User-friendly error messages
      const message = error.response?.data?.message || 'Generation failed';
      toast.error(message);

      // GOTCHA: Check for rate limit errors specifically
      if (error.response?.status === 429) {
        const resetTime = error.response.headers['x-ratelimit-reset'];
        toast.error(`Rate limit exceeded. Try again at ${new Date(resetTime * 1000).toLocaleTimeString()}`);
      }
    },
    retry: false  // Don't auto-retry on frontend (backend handles retries)
  });
};

// frontend/src/components/prompts/AIAssistButton.tsx - UI Integration
import { Button } from '@/components/ui/Button';
import { Sparkles } from 'lucide-react';
import { useAISettings } from '@/hooks/useAI';

export const AIAssistButton: React.FC<{ onGenerate: () => void }> = ({ onGenerate }) => {
  const { data: settings } = useAISettings();

  // PATTERN: Only show if AI is configured and enabled
  if (!settings?.enabled) return null;

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onGenerate}
      className="gap-1"
      title="Generate with AI"
    >
      <Sparkles className="h-4 w-4" />
      Generate
    </Button>
  );
};
```

### Integration Points

```yaml
DATABASE:
  - collections:
    - "ai_settings" - Store encrypted API keys and configuration
    - "generation_templates" - Custom prompt templates
    - "generation_logs" - Track usage and costs
  - indexes:
    - "db.ai_settings.createIndex({ 'user_id': 1 }, { unique: true })"
    - "db.generation_logs.createIndex({ 'created_at': -1 })"

CONFIG:
  - add to: backend/app/core/config.py
  - variables:
    - "CLAUDELENS_OPENAI_API_KEY = os.getenv('CLAUDELENS_OPENAI_API_KEY')"
    - "CLAUDELENS_ENCRYPTION_KEY = os.getenv('CLAUDELENS_ENCRYPTION_KEY')"
    - "AI_RATE_LIMIT_PER_MINUTE = int(os.getenv('AI_RATE_LIMIT_PER_MINUTE', '10'))"

ROUTES:
  - add to: backend/app/api/api_v1/api.py
  - pattern: "api_router.include_router(ai_settings.router, prefix='/settings', tags=['ai'])"
  - pattern: "Add AI routes BEFORE generic prompt routes in prompts.py"

FRONTEND:
  - add to: frontend/src/store/index.ts
  - pattern: "aiSettings: AISettingsSlice"
  - add to: frontend/src/pages/Settings.tsx
  - pattern: "Import and render <AISettingsPanel />"
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Backend validation
cd backend
poetry run ruff check app/services/ai_service.py --fix
poetry run ruff check app/api/api_v1/endpoints/ai_settings.py --fix
poetry run mypy app/services/ai_service.py
poetry run mypy app/api/api_v1/endpoints/ai_settings.py
poetry run ruff format app/

# Frontend validation
cd frontend
npm run lint
npm run type-check
npm run format

# Expected: Zero errors. Fix all issues before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Backend tests
cd backend
poetry run pytest tests/test_services_ai.py -v
poetry run pytest tests/test_endpoints_ai.py -v
poetry run pytest --cov=app.services.ai_service --cov-report=term-missing

# Frontend tests
cd frontend
npm run test -- AIAssistButton
npm run test -- useAI
npm run test:coverage

# Expected: All tests pass with >80% coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Start services
docker-compose up -d mongodb
cd backend && poetry run uvicorn app.main:app --reload &
cd frontend && npm run dev &

# Test AI configuration
curl -X PUT http://localhost:8000/api/v1/settings/ai \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"apiKey": "sk-test", "model": "gpt-4", "enabled": true}'

# Test connection
curl -X POST http://localhost:8000/api/v1/settings/ai/test \
  -H "X-API-Key: your-api-key"

# Test metadata generation
curl -X POST http://localhost:8000/api/v1/prompts/ai/generate-metadata \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"context": "Technical documentation summarizer", "type": "both"}'

# Test content generation
curl -X POST http://localhost:8000/api/v1/prompts/ai/generate-content \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"operation": "create", "requirements": "Summarize technical docs"}'

# Expected: Successful responses with generated content
```

### Level 4: Creative & Domain-Specific Validation

```bash
# Test rate limiting behavior
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/v1/prompts/ai/generate-metadata \
    -H "X-API-Key: your-api-key" \
    -H "Content-Type: application/json" \
    -d '{"context": "Test prompt", "type": "name"}' &
done
wait
# Expected: Some requests return 429 with rate limit headers

# Test token counting accuracy
echo '{"text": "Your long prompt content here..."}' | \
  curl -X POST http://localhost:8000/api/v1/debug/count-tokens \
    -H "Content-Type: application/json" \
    -d @-

# Test variable preservation
curl -X POST http://localhost:8000/api/v1/prompts/ai/generate-content \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "refactor",
    "existing_content": "You are a {{role}} helping with {{task}}",
    "requirements": "Make more concise",
    "preserve_variables": true
  }'
# Expected: Response maintains {{role}} and {{task}} variables

# Security validation
# Test with invalid API key
curl -X PUT http://localhost:8000/api/v1/settings/ai \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"apiKey": "invalid-key", "model": "gpt-4", "enabled": true}'

# Test API key exposure prevention
curl -X GET http://localhost:8000/api/v1/settings/ai \
  -H "X-API-Key: your-api-key" | grep -v "sk-"
# Expected: No actual API key in response

# Performance testing
ab -n 100 -c 10 \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -T application/json \
  -p test_payload.json \
  http://localhost:8000/api/v1/prompts/ai/generate-metadata
# Expected: p95 < 3 seconds, no failures
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] Backend tests pass: `poetry run pytest tests/ -v`
- [ ] Frontend tests pass: `npm run test`
- [ ] No linting errors: `poetry run ruff check app/`
- [ ] No type errors: `poetry run mypy app/`
- [ ] No frontend errors: `npm run lint && npm run type-check`

### Feature Validation

- [ ] AI settings configurable through UI
- [ ] API key encrypted in database
- [ ] Test connection validates OpenAI access
- [ ] Generate buttons appear in prompt editor when AI enabled
- [ ] Metadata generation produces valid names/descriptions
- [ ] Content generation preserves variables when requested
- [ ] Rate limiting prevents abuse
- [ ] Error messages are user-friendly
- [ ] Templates customizable and working

### Code Quality Validation

- [ ] Follows existing ClaudeLens patterns
- [ ] Proper error handling with custom exceptions
- [ ] Async/await used correctly throughout
- [ ] React Query cache properly managed
- [ ] No hardcoded values (all in config)
- [ ] Proper TypeScript types everywhere
- [ ] Security: API keys never exposed
- [ ] Logging at appropriate levels

### Documentation & Deployment

- [ ] API documentation updated in OpenAPI schema
- [ ] Environment variables documented in .env.example
- [ ] Migration scripts for new database collections
- [ ] README updated with AI feature description
- [ ] Cost implications documented

---

## Anti-Patterns to Avoid

- ❌ Don't expose OpenAI API keys in responses or logs
- ❌ Don't skip encryption for API key storage
- ❌ Don't ignore rate limiting (will get banned)
- ❌ Don't forget to count tokens before API calls
- ❌ Don't use synchronous OpenAI client in async context
- ❌ Don't hardcode model names or limits
- ❌ Don't cache AI-generated content indefinitely
- ❌ Don't skip variable preservation in refactoring
- ❌ Don't allow unlimited generation requests per user
