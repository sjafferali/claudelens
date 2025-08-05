# Backend Test Coverage Improvement Task List

This document tracks the tasks for systematically improving test coverage in the ClaudeLens backend. Each task represents a single test file to write or improve, followed by a verification task to ensure all tests pass.

## Instructions for Maintaining This Document

1. **Mark tasks as completed** by changing `[ ]` to `[x]` after completing each task
2. **Add the completion date** next to completed tasks (e.g., `[x] Task name - 2025-08-05`)
3. **Document any issues or blockers** in the Notes section for each task
4. **Update coverage percentages** after completing each set of tests
5. **Run all backend tests** after each task to ensure no regressions

## Current Coverage Summary

Last updated: 2025-08-05

- Overall backend coverage: 40% (improved from 37%)
- Target coverage: 80%+

### Files with Lowest Coverage (Priority Targets)
1. `app/services/ingest_debug.py` - 0% coverage
2. `app/services/validation.py` - 100% coverage ✓
3. `app/services/analytics.py` - 6% coverage (1700 lines!)
4. `app/services/ingest.py` - 29% coverage ✓ (improved from 7%)
5. `app/services/session.py` - 86% coverage ✓
6. `app/services/message.py` - 98% coverage ✓
7. `app/services/project.py` - 99% coverage ✓
8. `app/api/api_v1/endpoints/projects.py` - 100% coverage ✓
9. `app/api/api_v1/endpoints/sessions.py` - 98% coverage ✓ (new)
10. `app/api/api_v1/endpoints/messages.py` - 59% coverage ✓ (new)

## Task List

### Phase 1: Core Service Tests (High Priority)

#### Validation Service Tests
- [x] Task 1.1: Write tests for `app/services/validation.py` - test message validation logic - 2025-08-05
- [x] Task 1.2: Run all backend tests and ensure they pass - 2025-08-05

#### Session Service Tests
- [x] Task 2.1: Write tests for `app/services/session.py` - test session creation - 2025-08-05
- [x] Task 2.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 2.3: Write tests for `app/services/session.py` - test session updates and queries - 2025-08-05
- [x] Task 2.4: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 2.5: Write tests for `app/services/session.py` - test session deletion and cleanup - 2025-08-05
- [x] Task 2.6: Run all backend tests and ensure they pass - 2025-08-05

#### Message Service Tests
- [x] Task 3.1: Write tests for `app/services/message.py` - test message creation - 2025-08-05
- [x] Task 3.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 3.3: Write tests for `app/services/message.py` - test message queries and filtering - 2025-08-05
- [x] Task 3.4: Run all backend tests and ensure they pass - 2025-08-05

#### Project Service Tests
- [x] Task 4.1: Write tests for `app/services/project.py` - test project CRUD operations - 2025-08-05
- [x] Task 4.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 4.3: Write tests for `app/services/project.py` - test project statistics - 2025-08-05
- [x] Task 4.4: Run all backend tests and ensure they pass - 2025-08-05

### Phase 2: API Endpoint Tests

#### Projects Endpoint Tests
- [x] Task 5.1: Write tests for `app/api/api_v1/endpoints/projects.py` - test GET endpoints - 2025-08-05
- [x] Task 5.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 5.3: Write tests for `app/api/api_v1/endpoints/projects.py` - test POST/PUT/DELETE - 2025-08-05
- [x] Task 5.4: Run all backend tests and ensure they pass - 2025-08-05

#### Sessions Endpoint Tests
- [x] Task 6.1: Write tests for `app/api/api_v1/endpoints/sessions.py` - test session endpoints - 2025-08-05
- [x] Task 6.2: Run all backend tests and ensure they pass - 2025-08-05

#### Messages Endpoint Tests
- [x] Task 7.1: Write tests for `app/api/api_v1/endpoints/messages.py` - test message list/filter - 2025-08-05
- [x] Task 7.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 7.3: Write tests for `app/api/api_v1/endpoints/messages.py` - test message CRUD - 2025-08-05
- [x] Task 7.4: Run all backend tests and ensure they pass - 2025-08-05

### Phase 3: Complex Service Tests

#### Ingest Service Tests
- [x] Task 8.1: Write tests for `app/services/ingest.py` - test basic message ingestion - 2025-08-05
- [x] Task 8.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 8.3: Write tests for `app/services/ingest.py` - test batch processing - 2025-08-05
- [x] Task 8.4: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 8.5: Write tests for `app/services/ingest.py` - test error handling - 2025-08-05
- [x] Task 8.6: Run all backend tests and ensure they pass - 2025-08-05

#### Search Service Tests
- [x] Task 9.1: Write tests for `app/services/search.py` - test basic search functionality - 2025-08-05
- [x] Task 9.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 9.3: Write tests for `app/services/search.py` - test advanced filters - 2025-08-05
- [x] Task 9.4: Run all backend tests and ensure they pass - 2025-08-05

#### Cost Calculation Tests
- [x] Task 10.1: Write tests for `app/services/cost_calculation.py` - test cost calculations - 2025-08-05
- [x] Task 10.2: Run all backend tests and ensure they pass - 2025-08-05

### Phase 4: Analytics Service Tests (Large File - Break Down)

#### Basic Analytics Tests
- [x] Task 11.1: Write tests for `app/services/analytics.py` - test session analytics - 2025-08-05
- [x] Task 11.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 11.3: Write tests for `app/services/analytics.py` - test message analytics - 2025-08-05
- [x] Task 11.4: Run all backend tests and ensure they pass - 2025-08-05

#### Time-based Analytics Tests
- [x] Task 12.1: Write tests for `app/services/analytics.py` - test time series analytics - 2025-08-05
- [x] Task 12.2: Run all backend tests and ensure they pass - 2025-08-05
- [x] Task 12.3: Write tests for `app/services/analytics.py` - test aggregation functions - 2025-08-05
- [x] Task 12.4: Run all backend tests and ensure they pass - 2025-08-05

#### Performance Analytics Tests
- [x] Task 13.1: Write tests for `app/services/analytics.py` - test performance metrics - 2025-08-05
- [x] Task 13.2: Run all backend tests and ensure they pass - 2025-08-05
- [ ] Task 13.3: Write tests for `app/services/analytics.py` - test branch analytics
- [ ] Task 13.4: Run all backend tests and ensure they pass

### Phase 5: Infrastructure and Utility Tests

#### WebSocket Manager Tests
- [ ] Task 14.1: Write tests for `app/services/websocket_manager.py` - test connection handling
- [ ] Task 14.2: Run all backend tests and ensure they pass
- [ ] Task 14.3: Write tests for `app/services/websocket_manager.py` - test message broadcasting
- [ ] Task 14.4: Run all backend tests and ensure they pass

#### Middleware Tests
- [ ] Task 15.1: Write tests for `app/middleware/logging.py` - test logging middleware
- [ ] Task 15.2: Run all backend tests and ensure they pass
- [ ] Task 15.3: Write tests for `app/middleware/rate_limit.py` - test rate limiting
- [ ] Task 15.4: Run all backend tests and ensure they pass

#### Core Module Tests
- [ ] Task 16.1: Write tests for `app/core/exceptions.py` - test custom exceptions
- [ ] Task 16.2: Run all backend tests and ensure they pass
- [ ] Task 16.3: Write tests for `app/core/database.py` - test database utilities
- [ ] Task 16.4: Run all backend tests and ensure they pass

### Phase 6: Integration and End-to-End Tests

#### API Integration Tests
- [ ] Task 17.1: Write integration tests for ingest → message flow
- [ ] Task 17.2: Run all backend tests and ensure they pass
- [ ] Task 17.3: Write integration tests for search functionality
- [ ] Task 17.4: Run all backend tests and ensure they pass

#### WebSocket Integration Tests
- [ ] Task 18.1: Write tests for WebSocket real-time updates
- [ ] Task 18.2: Run all backend tests and ensure they pass

## Running Tests

To run all backend tests with coverage:
```bash
cd backend
poetry run pytest --cov=app --cov-report=term-missing --cov-report=html
```

To run tests for a specific file:
```bash
cd backend
poetry run pytest tests/test_services_validation.py -v
```

## Notes and Blockers

### General Notes
- Focus on testing happy paths first, then error cases
- Use pytest fixtures for common test data
- Mock external dependencies (MongoDB, etc.)
- Ensure each test is independent and can run in isolation

### Discovered Issues
- (Document any issues found while writing tests)

### Dependencies to Mock
- MongoDB connections
- External API calls
- File system operations
- WebSocket connections

## Coverage Goals by Phase

1. **Phase 1 Completion Target**: 40% overall coverage
2. **Phase 2 Completion Target**: 55% overall coverage
3. **Phase 3 Completion Target**: 65% overall coverage
4. **Phase 4 Completion Target**: 75% overall coverage
5. **Phase 5 Completion Target**: 80% overall coverage
6. **Phase 6 Completion Target**: 85%+ overall coverage

---

Last updated: 2025-08-05
