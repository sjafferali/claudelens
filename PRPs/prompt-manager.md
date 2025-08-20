name: "Prompt Manager Implementation PRP"
description: "Comprehensive implementation guide for ClaudeLens Prompt Manager feature"

---

## Goal

**Feature Goal**: Implement a fully functional prompt management system for ClaudeLens that allows users to create, organize, version, and share prompt templates with variable substitution and collaborative features

**Deliverable**: Complete prompt management module with:
- MongoDB collections for prompts and folders
- FastAPI CRUD endpoints with pagination and search
- React UI with folder tree, grid/list views, and editor panel
- Variable template system with {{variable}} syntax
- Version control with semantic versioning
- Import/export functionality for JSON/CSV/Markdown

**Success Definition**: Users can successfully create, organize, test, and share prompt templates through an intuitive UI that follows ClaudeLens design patterns, with all CRUD operations working and data persisting to MongoDB

## User Persona

**Target User**: ClaudeLens power users who work with Claude AI frequently and need to manage reusable prompt templates

**Use Case**:
- Create and organize prompt templates for different tasks (coding, writing, analysis)
- Use variables to customize prompts without rewriting
- Share prompts with team members
- Track prompt performance and version history

**User Journey**:
1. User navigates to Prompt Manager from sidebar
2. Browses existing prompts or creates new one
3. Organizes prompts in folders with tags
4. Tests prompt with variables in playground
5. Shares prompt with team or exports for backup

**Pain Points Addressed**:
- Scattered prompts across different files/notes
- No version control for prompt iterations
- Difficulty sharing effective prompts with team
- Manual variable replacement in prompts

## Why

- **Business Value**: Increases productivity by reducing time spent recreating prompts, enables team knowledge sharing
- **Integration**: Extends ClaudeLens analytics by tracking prompt usage and effectiveness
- **Problems Solved**: Eliminates prompt duplication, enables prompt optimization through version tracking, facilitates team collaboration

## What

### User-Visible Behavior
- Sidebar navigation item "Prompt Manager" with icon and count badge
- Dual-pane interface: folder tree on left, prompt grid/list on right
- Create/Edit prompt in slide-out panel with live preview
- Test prompts in playground with variable substitution
- Import/Export prompts in multiple formats

### Technical Requirements
- RESTful API with pagination, filtering, and search
- Real-time search with debouncing
- Optimistic UI updates with cache invalidation
- WebSocket updates for collaborative features
- Secure sharing with access control

### Success Criteria
- [ ] All CRUD operations work for prompts and folders
- [ ] Variable substitution system correctly identifies and replaces {{variables}}
- [ ] Search returns results within 300ms for 1000+ prompts
- [ ] Version history maintains last 10 versions per prompt
- [ ] Import/Export handles JSON, CSV, and Markdown formats
- [ ] UI responsive on mobile, tablet, and desktop
- [ ] All validation tests pass (backend and frontend)

## All Needed Context

### Context Completeness Check
_This PRP contains all patterns, file references, and implementation details needed for someone unfamiliar with ClaudeLens to implement the prompt manager feature successfully._

### Documentation & References

```yaml
# External Documentation
- url: https://github.com/dair-ai/Prompt-Engineering-Guide#prompt-engineering-guide
  why: Comprehensive guide on prompt engineering best practices
  critical: Template structure recommendations and variable handling patterns

- url: https://github.com/promptfoo/promptfoo#testing-llm-prompts
  why: Reference for prompt testing and validation approaches
  critical: A/B testing patterns and evaluation metrics

# ClaudeLens Pattern Files - MUST FOLLOW
- file: backend/app/models/project.py
  why: MongoDB model pattern with Pydantic schemas
  pattern: PyObjectId handling, timestamp fields, model_config setup
  gotcha: Must use ObjectId for MongoDB, field aliases for API responses

- file: backend/app/services/project.py
  why: Service layer pattern with dependency injection
  pattern: CRUD methods, aggregation pipelines, cascade deletion
  gotcha: Services receive database in constructor, handle ObjectId conversion

- file: backend/app/api/api_v1/endpoints/projects.py
  why: FastAPI endpoint patterns with pagination
  pattern: PaginatedResponse wrapper, query parameter validation, error handling
  gotcha: Use CommonDeps for database injection, handle NotFoundError

- file: backend/app/schemas/project.py
  why: Schema separation pattern (Base, Create, Update, Response)
  pattern: Field validation, datetime serialization, optional fields
  gotcha: Different schemas for list vs detail views

- file: frontend/src/pages/Projects.tsx
  why: React page structure with list/detail routing
  pattern: Nested routing, URL state management, loading states
  gotcha: Use useParams for routing, useSearchParams for filters

- file: frontend/src/hooks/useProjects.ts
  why: React Query patterns for data fetching
  pattern: useQuery/useMutation, cache invalidation, error handling
  gotcha: Query keys must include all parameters, 30-second stale time

- file: frontend/src/api/projects.ts
  why: API client structure with TypeScript
  pattern: Axios client, query parameter building, type safety
  gotcha: Use URLSearchParams for consistent query strings

- file: frontend/src/components/common/Card.tsx
  why: UI component patterns for consistent styling
  pattern: Compound components, semantic naming, Tailwind classes
  gotcha: Use bg-layer-* for backgrounds, text-*-c for text colors

# Mockup Reference
- file: plans/uiredesign/mockups/prompt-manager.html
  why: Complete UI mockup with all features
  pattern: Folder tree, grid/list views, editor panel, modals
  critical: Shows exact layout, component structure, and interactions

# Best Practices Document
- file: plans/uiredesign/mockups/prompt-organization-best-practices.md
  why: Detailed organization patterns and UI/UX decisions
  pattern: Folder hierarchy, tagging strategy, metadata structure
  critical: Data model definition and naming conventions
```

### Current Codebase Tree (Relevant Sections)

```bash
claudelens/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── project.py      # Reference model pattern
│   │   │   └── session.py      # Reference model pattern
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── project.py      # Reference service pattern
│   │   │   └── session.py      # Reference service pattern
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── project.py      # Reference schema pattern
│   │   │   └── session.py      # Reference schema pattern
│   │   └── api/
│   │       └── api_v1/
│   │           ├── api.py       # Router registration
│   │           └── endpoints/
│   │               ├── projects.py  # Reference endpoint pattern
│   │               └── sessions.py  # Reference endpoint pattern
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Projects.tsx     # Reference page pattern
    │   │   └── Sessions.tsx     # Reference page pattern
    │   ├── hooks/
    │   │   ├── useProjects.ts   # Reference hook pattern
    │   │   └── useSessions.ts   # Reference hook pattern
    │   ├── api/
    │   │   ├── projects.ts      # Reference API pattern
    │   │   └── sessions.ts      # Reference API pattern
    │   └── components/
    │       └── common/          # Reusable UI components
```

### Desired Codebase Tree with New Files

```bash
claudelens/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── prompt.py        # NEW: Prompt and Folder models
│   │   ├── services/
│   │   │   └── prompt.py        # NEW: Prompt service with CRUD
│   │   ├── schemas/
│   │   │   └── prompt.py        # NEW: Prompt schemas (Base, Create, Update, etc.)
│   │   └── api/
│   │       └── api_v1/
│   │           └── endpoints/
│   │               └── prompts.py  # NEW: Prompt API endpoints
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   └── Prompts.tsx       # NEW: Main prompt manager page
    │   ├── hooks/
    │   │   └── usePrompts.ts     # NEW: Prompt data fetching hooks
    │   ├── api/
    │   │   ├── types.ts          # UPDATE: Add prompt types
    │   │   └── prompts.ts        # NEW: Prompt API client
    │   └── components/
    │       └── prompts/          # NEW: Prompt-specific components
    │           ├── PromptEditor.tsx     # Prompt editor panel
    │           ├── PromptCard.tsx       # Grid view card
    │           ├── PromptList.tsx       # List view component
    │           ├── FolderTree.tsx       # Folder navigation
    │           ├── PromptPlayground.tsx # Testing interface
    │           └── VariableChips.tsx    # Variable display
```

### Known Gotchas & Library Quirks

```python
# MongoDB ObjectId Handling
# CRITICAL: Always use PyObjectId for MongoDB _id fields
# The custom PyObjectId validator handles string <-> ObjectId conversion

# FastAPI Async Requirements
# CRITICAL: All endpoint functions must be async
# Database operations use Motor (async MongoDB driver)

# React Query Cache Keys
# CRITICAL: Query keys must be arrays with all parameters
# Changes to any parameter should create new query key

# Tailwind Dark Mode
# CRITICAL: Use semantic color classes (bg-layer-*, text-*-c)
# These automatically adapt to dark/light theme

# Variable Template Regex
# CRITICAL: Use /\{\{(\w+)\}\}/g to match {{variable}} syntax
# Must handle nested variables and special characters
```

## Implementation Blueprint

### Data Models and Structure

```python
# backend/app/models/prompt.py
from datetime import datetime
from typing import Optional, List, Dict
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict
from app.models import PyObjectId

class FolderInDB(BaseModel):
    """Folder for organizing prompts"""
    id: PyObjectId = Field(alias="_id", default_factory=PyObjectId)
    name: str
    parent_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class PromptVersionInDB(BaseModel):
    """Version history for prompts"""
    version: str  # Semantic version
    content: str
    variables: List[str]
    change_log: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str

class PromptInDB(BaseModel):
    """Prompt template stored in database"""
    id: PyObjectId = Field(alias="_id", default_factory=PyObjectId)
    name: str
    description: Optional[str] = None
    content: str  # Template with {{variables}}
    variables: List[str] = []  # Extracted variable names
    tags: List[str] = []
    folder_id: Optional[PyObjectId] = None
    version: str = "1.0.0"
    versions: List[PromptVersionInDB] = []

    # Sharing settings
    visibility: str = "private"  # private, team, public
    shared_with: List[str] = []  # User IDs
    public_url: Optional[str] = None

    # Statistics
    use_count: int = 0
    last_used_at: Optional[datetime] = None
    avg_response_time: Optional[float] = None
    success_rate: Optional[float] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID
    is_starred: bool = False

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
```

### Implementation Tasks (Ordered by Dependencies)

```yaml
Task 1: CREATE backend/app/models/prompt.py
  - IMPLEMENT: PromptInDB, FolderInDB, PromptVersionInDB models
  - FOLLOW pattern: backend/app/models/project.py (PyObjectId usage, ConfigDict)
  - NAMING: InDB suffix for database models, datetime fields with _at suffix
  - PLACEMENT: Models directory with other domain models

Task 2: CREATE backend/app/schemas/prompt.py
  - IMPLEMENT: PromptBase, PromptCreate, PromptUpdate, Prompt, PromptDetail schemas
  - FOLLOW pattern: backend/app/schemas/project.py (Base/Create/Update pattern)
  - NAMING: Consistent with schema naming conventions
  - DEPENDENCIES: Import PyObjectId from models
  - PLACEMENT: Schemas directory with validation logic

Task 3: CREATE backend/app/services/prompt.py
  - IMPLEMENT: PromptService class with CRUD operations
  - FOLLOW pattern: backend/app/services/project.py (service structure, error handling)
  - NAMING: Async methods - create_prompt, get_prompt, update_prompt, delete_prompt
  - DEPENDENCIES: Import models and schemas from Tasks 1-2
  - PLACEMENT: Services directory for business logic

Task 4: CREATE backend/app/api/api_v1/endpoints/prompts.py
  - IMPLEMENT: FastAPI endpoints for prompts and folders
  - FOLLOW pattern: backend/app/api/api_v1/endpoints/projects.py (pagination, filters)
  - NAMING: RESTful routes - GET /prompts, POST /prompts, etc.
  - DEPENDENCIES: Import service from Task 3, CommonDeps for DB
  - PLACEMENT: API endpoints directory

Task 5: MODIFY backend/app/api/api_v1/api.py
  - INTEGRATE: Register prompt router with API
  - FIND pattern: Existing router.include_router calls
  - ADD: api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
  - PRESERVE: Existing router registrations

Task 6: CREATE frontend/src/api/prompts.ts
  - IMPLEMENT: Prompt API client with TypeScript types
  - FOLLOW pattern: frontend/src/api/projects.ts (axios client, query params)
  - NAMING: promptsApi object with method names matching endpoints
  - DEPENDENCIES: Import types from api/types.ts
  - PLACEMENT: API directory with other API clients

Task 7: UPDATE frontend/src/api/types.ts
  - ADD: Prompt, Folder, PromptVersion TypeScript interfaces
  - FOLLOW pattern: Existing interface definitions (snake_case from API)
  - NAMING: Match backend schema field names
  - PLACEMENT: Add to existing types file

Task 8: CREATE frontend/src/hooks/usePrompts.ts
  - IMPLEMENT: React Query hooks for prompt operations
  - FOLLOW pattern: frontend/src/hooks/useProjects.ts (useQuery/useMutation)
  - NAMING: usePrompts, usePrompt, useCreatePrompt, useUpdatePrompt
  - DEPENDENCIES: Import promptsApi from Task 6
  - PLACEMENT: Hooks directory with data fetching logic

Task 9: CREATE frontend/src/pages/Prompts.tsx
  - IMPLEMENT: Main prompt manager page with routing
  - FOLLOW pattern: frontend/src/pages/Projects.tsx (list/detail routing)
  - NAMING: Export default function Prompts()
  - DEPENDENCIES: Import hooks from Task 8, components from Task 10
  - PLACEMENT: Pages directory for routing

Task 10: CREATE frontend/src/components/prompts/
  - IMPLEMENT: All prompt-specific components
  - FOLLOW pattern: frontend/src/components/common/ (Card system, styling)
  - Components to create:
    - FolderTree.tsx: Hierarchical folder navigation
    - PromptCard.tsx: Grid view card component
    - PromptList.tsx: List view table component
    - PromptEditor.tsx: Slide-out editor panel
    - PromptPlayground.tsx: Testing interface
    - VariableChips.tsx: Variable visualization
  - PLACEMENT: New prompts directory in components

Task 11: UPDATE frontend/src/components/layout/Sidebar.tsx
  - ADD: Navigation item for Prompt Manager
  - FIND pattern: Existing navigation items
  - ADD: NavLink with FileText icon, /prompts route
  - PRESERVE: Existing navigation structure

Task 12: UPDATE frontend/src/App.tsx
  - ADD: Route for Prompts page
  - FIND pattern: Existing Route components
  - ADD: <Route path="/prompts/*" element={<Prompts />} />
  - PRESERVE: Existing routes

Task 13: CREATE backend/tests/test_prompt_service.py
  - IMPLEMENT: Unit tests for prompt service
  - FOLLOW pattern: backend/tests/test_services_project.py
  - COVERAGE: CRUD operations, variable extraction, version management
  - PLACEMENT: Tests directory

Task 14: CREATE frontend/src/components/prompts/__tests__/
  - IMPLEMENT: Component tests for prompt UI
  - FOLLOW pattern: frontend/src/components/__tests__/
  - COVERAGE: User interactions, rendering, error states
  - PLACEMENT: Component test directory
```

### Implementation Patterns & Key Details

```python
# Backend: Variable Extraction Pattern
import re

def extract_variables(content: str) -> List[str]:
    """Extract {{variable}} names from prompt content"""
    # PATTERN: Match {{variable_name}} syntax
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, content)
    return list(set(matches))  # Unique variables only

# Backend: Service Method Pattern
async def create_prompt(self, prompt_data: PromptCreate) -> PromptDetail:
    # PATTERN: Input validation first
    prompt_dict = prompt_data.model_dump()

    # GOTCHA: Extract variables from content
    prompt_dict['variables'] = extract_variables(prompt_dict['content'])

    # GOTCHA: Convert folder_id to ObjectId if provided
    if prompt_dict.get('folder_id'):
        prompt_dict['folder_id'] = ObjectId(prompt_dict['folder_id'])

    # PATTERN: Database operation with error handling
    try:
        result = await self.db.prompts.insert_one(prompt_dict)
        created_prompt = await self.db.prompts.find_one({"_id": result.inserted_id})
        return PromptDetail(**created_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Frontend: Variable Substitution Pattern
export function substituteVariables(
  template: string,
  variables: Record<string, string>
): string {
  // PATTERN: Replace {{variable}} with values
  return template.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
    return variables[varName] || match;  // Keep original if no value
  });
}

# Frontend: Folder Tree Recursive Pattern
interface FolderNode {
  id: string;
  name: string;
  children: FolderNode[];
  promptCount: number;
}

function buildFolderTree(folders: Folder[]): FolderNode[] {
  // PATTERN: Build hierarchical structure from flat list
  const nodeMap = new Map<string, FolderNode>();
  const rootNodes: FolderNode[] = [];

  // Create nodes
  folders.forEach(folder => {
    nodeMap.set(folder.id, {
      ...folder,
      children: [],
      promptCount: 0
    });
  });

  // Build tree
  folders.forEach(folder => {
    const node = nodeMap.get(folder.id)!;
    if (folder.parent_id) {
      const parent = nodeMap.get(folder.parent_id);
      parent?.children.push(node);
    } else {
      rootNodes.push(node);
    }
  });

  return rootNodes;
}
```

### Integration Points

```yaml
DATABASE:
  - collections: "prompts", "prompt_folders"
  - indexes:
    - "CREATE INDEX idx_prompt_folder ON prompts(folder_id)"
    - "CREATE TEXT INDEX idx_prompt_search ON prompts(name, description, content)"
    - "CREATE INDEX idx_prompt_tags ON prompts(tags)"

CONFIG:
  - add to: backend/app/core/config.py
  - settings:
    - "MAX_PROMPT_VERSIONS = 10"
    - "PROMPT_VARIABLE_PATTERN = r'\{\{(\w+)\}\}'"

ROUTES:
  - add to: backend/app/api/api_v1/api.py
  - pattern: "api_router.include_router(prompts.router, prefix='/prompts', tags=['prompts'])"

WEBSOCKET:
  - event: "prompt_updated" - Broadcast when prompt is modified
  - event: "prompt_shared" - Notify when prompt is shared
```

## Validation Loop

### Level 1: Syntax & Style (Backend)

```bash
# Format and lint Python code
cd backend
poetry run ruff check app/models/prompt.py --fix
poetry run ruff check app/schemas/prompt.py --fix
poetry run ruff check app/services/prompt.py --fix
poetry run ruff check app/api/api_v1/endpoints/prompts.py --fix

# Type checking
poetry run mypy app/models/prompt.py
poetry run mypy app/schemas/prompt.py
poetry run mypy app/services/prompt.py
poetry run mypy app/api/api_v1/endpoints/prompts.py

# Expected: Zero errors. Fix any issues before proceeding.
```

### Level 2: Syntax & Style (Frontend)

```bash
# Format and lint TypeScript code
cd frontend
npm run lint -- src/api/prompts.ts
npm run lint -- src/hooks/usePrompts.ts
npm run lint -- src/pages/Prompts.tsx
npm run lint -- src/components/prompts/

# Type checking
npm run type-check

# Format code
npm run format

# Expected: Zero errors. Fix any issues before proceeding.
```

### Level 3: Unit Tests

```bash
# Backend tests
cd backend
poetry run pytest tests/test_prompt_service.py -v
poetry run pytest tests/test_endpoints_prompts.py -v

# Frontend tests
cd frontend
npm run test -- src/components/prompts/
npm run test -- src/hooks/usePrompts.test.ts

# Coverage check
npm run test:coverage

# Expected: All tests pass with >80% coverage
```

### Level 4: Integration Testing

```bash
# Start backend
cd backend
poetry run uvicorn app.main:app --reload --port 8000 &
sleep 3

# Health check
curl -f http://localhost:8000/api/v1/health || echo "API health check failed"

# Test prompt CRUD operations
# Create prompt
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "name": "Test Prompt",
    "content": "Hello {{name}}, your task is {{task}}",
    "tags": ["test", "example"]
  }' | jq .

# List prompts
curl http://localhost:8000/api/v1/prompts \
  -H "X-API-Key: $API_KEY" | jq .

# Search prompts
curl "http://localhost:8000/api/v1/prompts?search=test" \
  -H "X-API-Key: $API_KEY" | jq .

# Start frontend
cd frontend
npm run dev &
sleep 5

# Visual inspection
echo "Open http://localhost:5173/prompts in browser"
echo "Test: Create prompt, organize in folders, test playground"

# Expected: All operations work, UI responsive, no console errors
```

### Level 5: End-to-End Testing

```bash
# Full workflow test
# 1. Create folder structure
# 2. Create prompt with variables
# 3. Test prompt in playground
# 4. Version prompt
# 5. Share prompt
# 6. Export/Import prompts

# Performance test
ab -n 100 -c 10 -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/prompts

# Expected: <300ms response time for search
# Expected: All CRUD operations successful
# Expected: Variable substitution working
```

## Final Validation Checklist

### Technical Validation
- [ ] All validation levels (1-5) completed successfully
- [ ] Backend tests pass: `poetry run pytest tests/ -v`
- [ ] Frontend tests pass: `npm run test`
- [ ] No linting errors: `poetry run ruff check` and `npm run lint`
- [ ] No type errors: `poetry run mypy` and `npm run type-check`

### Feature Validation
- [ ] Create, read, update, delete prompts working
- [ ] Folder organization with drag-and-drop working
- [ ] Variable extraction and substitution working
- [ ] Version history tracking working
- [ ] Search and filtering returning correct results
- [ ] Import/export for JSON, CSV, Markdown working
- [ ] Playground testing interface functional
- [ ] Sharing with access control working

### Code Quality Validation
- [ ] Follows ClaudeLens patterns (Card components, service structure, etc.)
- [ ] Uses existing UI components (Button, Dialog, Loading, etc.)
- [ ] Maintains consistent naming conventions
- [ ] Proper error handling with user feedback
- [ ] Responsive design working on mobile/tablet/desktop

### Documentation & Deployment
- [ ] API endpoints documented in OpenAPI spec
- [ ] Environment variables documented if new ones added
- [ ] Database migrations/indexes created
- [ ] WebSocket events documented

---

## Anti-Patterns to Avoid

- ❌ Don't create new UI component patterns - use existing Card, Button, Dialog components
- ❌ Don't use synchronous database operations - all must be async with Motor
- ❌ Don't hardcode colors - use semantic Tailwind classes (bg-layer-*, text-*-c)
- ❌ Don't skip query key parameters in React Query - include all filter params
- ❌ Don't use string IDs for MongoDB - always use ObjectId with PyObjectId validator
- ❌ Don't ignore TypeScript types - maintain full type safety throughout
- ❌ Don't create new validation patterns - follow existing schema patterns
