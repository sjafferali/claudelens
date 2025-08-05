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

- Overall backend coverage: ~25%
- Target coverage: 80%+

### Files with Lowest Coverage (Priority Targets)
1. `app/services/ingest_debug.py` - 0% coverage
2. `app/services/validation.py` - 0% coverage
3. `app/services/analytics.py` - 6% coverage (1700 lines!)
4. `app/services/ingest.py` - 7% coverage
5. `app/services/session.py` - 8% coverage

## Task List

### Phase 1: Core Service Tests (High Priority)

#### Validation Service Tests
- [ ] Task 1.1: Write tests for `app/services/validation.py` - test message validation logic
- [ ] Task 1.2: Run all backend tests and ensure they pass

#### Session Service Tests
- [ ] Task 2.1: Write tests for `app/services/session.py` - test session creation
- [ ] Task 2.2: Run all backend tests and ensure they pass
- [ ] Task 2.3: Write tests for `app/services/session.py` - test session updates and queries
- [ ] Task 2.4: Run all backend tests and ensure they pass
- [ ] Task 2.5: Write tests for `app/services/session.py` - test session deletion and cleanup
- [ ] Task 2.6: Run all backend tests and ensure they pass

#### Message Service Tests
- [ ] Task 3.1: Write tests for `app/services/message.py` - test message creation
- [ ] Task 3.2: Run all backend tests and ensure they pass
- [ ] Task 3.3: Write tests for `app/services/message.py` - test message queries and filtering
- [ ] Task 3.4: Run all backend tests and ensure they pass

#### Project Service Tests
- [ ] Task 4.1: Write tests for `app/services/project.py` - test project CRUD operations
- [ ] Task 4.2: Run all backend tests and ensure they pass
- [ ] Task 4.3: Write tests for `app/services/project.py` - test project statistics
- [ ] Task 4.4: Run all backend tests and ensure they pass

### Phase 2: API Endpoint Tests

#### Projects Endpoint Tests
- [ ] Task 5.1: Write tests for `app/api/api_v1/endpoints/projects.py` - test GET endpoints
- [ ] Task 5.2: Run all backend tests and ensure they pass
- [ ] Task 5.3: Write tests for `app/api/api_v1/endpoints/projects.py` - test POST/PUT/DELETE
- [ ] Task 5.4: Run all backend tests and ensure they pass

#### Sessions Endpoint Tests
- [ ] Task 6.1: Write tests for `app/api/api_v1/endpoints/sessions.py` - test session endpoints
- [ ] Task 6.2: Run all backend tests and ensure they pass

#### Messages Endpoint Tests
- [ ] Task 7.1: Write tests for `app/api/api_v1/endpoints/messages.py` - test message list/filter
- [ ] Task 7.2: Run all backend tests and ensure they pass
- [ ] Task 7.3: Write tests for `app/api/api_v1/endpoints/messages.py` - test message CRUD
- [ ] Task 7.4: Run all backend tests and ensure they pass

### Phase 3: Complex Service Tests

#### Ingest Service Tests
- [ ] Task 8.1: Write tests for `app/services/ingest.py` - test basic message ingestion
- [ ] Task 8.2: Run all backend tests and ensure they pass
- [ ] Task 8.3: Write tests for `app/services/ingest.py` - test batch processing
- [ ] Task 8.4: Run all backend tests and ensure they pass
- [ ] Task 8.5: Write tests for `app/services/ingest.py` - test error handling
- [ ] Task 8.6: Run all backend tests and ensure they pass

#### Search Service Tests
- [ ] Task 9.1: Write tests for `app/services/search.py` - test basic search functionality
- [ ] Task 9.2: Run all backend tests and ensure they pass
- [ ] Task 9.3: Write tests for `app/services/search.py` - test advanced filters
- [ ] Task 9.4: Run all backend tests and ensure they pass

#### Cost Calculation Tests
- [ ] Task 10.1: Write tests for `app/services/cost_calculation.py` - test cost calculations
- [ ] Task 10.2: Run all backend tests and ensure they pass

### Phase 4: Analytics Service Tests (Large File - Break Down)

#### Basic Analytics Tests
- [ ] Task 11.1: Write tests for `app/services/analytics.py` - test session analytics
- [ ] Task 11.2: Run all backend tests and ensure they pass
- [ ] Task 11.3: Write tests for `app/services/analytics.py` - test message analytics
- [ ] Task 11.4: Run all backend tests and ensure they pass

#### Time-based Analytics Tests
- [ ] Task 12.1: Write tests for `app/services/analytics.py` - test time series analytics
- [ ] Task 12.2: Run all backend tests and ensure they pass
- [ ] Task 12.3: Write tests for `app/services/analytics.py` - test aggregation functions
- [ ] Task 12.4: Run all backend tests and ensure they pass

#### Performance Analytics Tests
- [ ] Task 13.1: Write tests for `app/services/analytics.py` - test performance metrics
- [ ] Task 13.2: Run all backend tests and ensure they pass
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
