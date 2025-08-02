# ClaudeLens Implementation Plan

## Project Structure

```
claudelens/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sessions.py
│   │   │   │   ├── messages.py
│   │   │   │   ├── projects.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── search.py
│   │   │   │   └── ingest.py
│   │   │   ├── __init__.py
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   ├── message.py
│   │   │   ├── project.py
│   │   │   └── analytics.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py
│   │   │   ├── search.py
│   │   │   ├── analytics.py
│   │   │   └── deduplication.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_models/
│   ├── scripts/
│   │   ├── generate_sample_data.py
│   │   └── run_dev.py
│   ├── alembic/
│   ├── poetry.lock
│   ├── pyproject.toml
│   └── Dockerfile.backend
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── sessions.ts
│   │   │   ├── messages.ts
│   │   │   ├── search.ts
│   │   │   └── analytics.ts
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── sessions/
│   │   │   ├── messages/
│   │   │   ├── search/
│   │   │   └── analytics/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── store/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile.frontend
├── cli/
│   ├── claudelens_cli/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── sync.py
│   │   │   ├── status.py
│   │   │   └── config.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── sync_engine.py
│   │   │   ├── watcher.py
│   │   │   └── state.py
│   │   └── utils/
│   ├── tests/
│   ├── poetry.lock
│   └── pyproject.toml
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── nginx.conf
├── scripts/
│   ├── dev.sh
│   ├── test.sh
│   └── build.sh
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
├── README.md
└── LICENSE
```

## Implementation Phases

### Phase 1: Foundation (Tasks 1-5)
- Set up project structure
- Configure development environment
- Set up MongoDB with proper schemas
- Create base models and database connections
- Set up testing infrastructure

### Phase 2: Data Ingestion (Tasks 6-10)
- Build CLI tool structure
- Implement JSONL parsing
- Create deduplication logic
- Build sync engine with state tracking
- Implement file watcher for continuous sync

### Phase 3: Backend API (Tasks 11-20)
- Implement FastAPI application structure
- Create API endpoints for data retrieval
- Build search functionality
- Implement analytics aggregations
- Add authentication and rate limiting

### Phase 4: Frontend Core (Tasks 21-30)
- Set up React/Vite project
- Create component library
- Build session browser
- Implement message viewer
- Add search interface

### Phase 5: Visualizations (Tasks 31-35)
- Create activity heatmap
- Build cost analytics charts
- Implement usage statistics
- Add export functionality

### Phase 6: Infrastructure (Tasks 36-40)
- Create unified Docker image
- Set up GitHub Actions CI/CD
- Configure deployment scripts
- Add monitoring and logging

## CLI Sync Strategy

### Deduplication Approach
1. **State File**: Maintain `.claudelens/sync_state.json` in user's home directory
2. **Content Hashing**: SHA-256 hash of each message for deduplication
3. **Timestamp Tracking**: Track last sync time per project
4. **Incremental Sync**: Only process files modified after last sync

### State File Structure
```json
{
  "version": "1.0.0",
  "last_sync": "2024-01-15T10:30:00Z",
  "projects": {
    "/Users/user/project1": {
      "last_sync": "2024-01-15T10:30:00Z",
      "last_file": "session-uuid.jsonl",
      "last_line": 150,
      "synced_messages": ["hash1", "hash2", "..."]
    }
  },
  "api_endpoint": "http://localhost:8000",
  "api_key": "encrypted-key"
}
```

### Sync Algorithm
```python
1. Load state file
2. Scan Claude directory for projects
3. For each project:
   a. List JSONL files modified after last_sync
   b. For each file:
      - If new: process entire file
      - If seen: resume from last_line
   c. For each message:
      - Generate content hash
      - Check if hash exists in synced_messages
      - If new: queue for upload
   d. Batch upload messages (100 at a time)
   e. Update state file after successful upload
4. Save state file
```

## Docker Strategy

### Unified Container Structure
```
/app/
├── backend/          # Python FastAPI app
├── frontend/dist/    # Built React app
├── nginx.conf        # Nginx configuration
└── entrypoint.sh     # Startup script
```

### Build Process
1. Multi-stage Docker build
2. Build frontend in Node stage
3. Build backend in Python stage
4. Final stage with Nginx + Python
5. Nginx serves frontend and proxies /api to backend

### Docker Compose Configuration
```yaml
version: '3.8'
services:
  claudelens:
    image: claudelens:latest
    ports:
      - "3000:80"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017/claudelens
      - API_KEY=${API_KEY}
    depends_on:
      - mongodb

  mongodb:
    image: mongo:7.0
    volumes:
      - claudelens_data:/data/db
    ports:
      - "27017:27017"

volumes:
  claudelens_data:
```

## Development Scripts

### dev.sh Features
```bash
# Start with testcontainers MongoDB
./scripts/dev.sh

# Start with persistent MongoDB
./scripts/dev.sh --persistent-db

# Load sample data
./scripts/dev.sh --load-samples

# Run specific services
./scripts/dev.sh --backend-only
./scripts/dev.sh --frontend-only
```

### Sample Data Generation
- Create realistic conversation data
- Multiple projects with various sizes
- Different message types and tool uses
- Span several months for analytics testing
- Include edge cases for testing

## GitHub Actions Workflow

### CI Pipeline Steps
1. **Lint & Format**
   - Python: Ruff
   - TypeScript: ESLint + Prettier
   - Dockerfile: Hadolint

2. **Test**
   - Python: pytest with coverage
   - TypeScript: Vitest with coverage
   - Integration tests with Testcontainers

3. **Build**
   - Build Docker image
   - Tag with version and commit SHA
   - Push to GitHub Container Registry

4. **Security Scan**
   - Scan dependencies for vulnerabilities
   - Scan Docker image with Trivy

## Security Considerations

1. **API Authentication**: API key in headers
2. **Input Validation**: Pydantic models for all inputs
3. **Rate Limiting**: Redis-based rate limiting
4. **CORS**: Configurable CORS settings
5. **Environment Variables**: All secrets in env vars
6. **Database Security**: MongoDB authentication enabled

## Performance Optimizations

1. **Batch Processing**: Ingest messages in batches
2. **Indexes**: Optimized MongoDB indexes
3. **Caching**: Redis caching for common queries
4. **Pagination**: Cursor-based pagination
5. **Async Operations**: Full async/await stack
6. **Connection Pooling**: Reuse database connections

## Monitoring & Logging

1. **Structured Logging**: JSON logs with context
2. **Request Tracking**: Unique request IDs
3. **Performance Metrics**: Response time tracking
4. **Error Tracking**: Sentry integration ready
5. **Health Checks**: /health endpoint

## Testing Strategy

1. **Unit Tests**: 80%+ coverage target
2. **Integration Tests**: API endpoint testing
3. **E2E Tests**: Critical user flows
4. **Load Tests**: Verify performance targets
5. **Security Tests**: OWASP checks
