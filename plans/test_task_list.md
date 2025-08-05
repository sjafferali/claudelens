# Backend Test Coverage Improvement Plan

**Current Coverage: 64%** | **Target: 85%+**

This file tracks the systematic improvement of backend test coverage, focusing on one file at a time starting with the lowest coverage files.

## Instructions for Updating This File
After completing each task:
1. Mark the task as ✅ COMPLETED
2. Update the coverage percentage if measured
3. Add any notes about challenges or discoveries
4. Move to the next pending task

## Priority 1: Critical Coverage Gaps (< 70%)

### app/services/analytics.py (59% coverage - SIGNIFICANT IMPROVEMENT!)
- [x] **Task 1.1**: Write test for `get_tool_usage_analytics()` function - basic functionality ✅ COMPLETED
- [x] **Task 1.2**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.3**: Write test for `get_tool_usage_analytics()` error handling ✅ COMPLETED
- [x] **Task 1.4**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.5**: Write test for `get_conversation_flow_analytics()` function ✅ COMPLETED
- [x] **Task 1.6**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.7**: Write test for `get_error_success_tracking()` function ✅ COMPLETED
- [x] **Task 1.8**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.9**: Write test for `get_working_directory_insights()` function ✅ COMPLETED
- [x] **Task 1.10**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.11**: Write test for `get_response_time_analytics()` function ✅ COMPLETED
- [x] **Task 1.12**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.13**: Write test for `get_git_branch_analytics()` function ✅ COMPLETED
- [x] **Task 1.14**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.15**: Write test for `get_token_efficiency_metrics()` function ✅ COMPLETED
- [x] **Task 1.16**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.17**: Write test for `get_session_depth_analysis()` function ✅ COMPLETED
- [x] **Task 1.18**: Run all backend tests and ensure passing ✅ COMPLETED
- [x] **Task 1.19**: Write test for `get_cost_prediction_dashboard()` function ✅ COMPLETED
- [x] **Task 1.20**: Run all backend tests and ensure passing ✅ COMPLETED

### app/api/api_v1/endpoints/search.py (47% coverage)
- [ ] **Task 2.1**: Write test for search endpoint with valid query parameters
- [ ] **Task 2.2**: Run all backend tests and ensure passing
- [ ] **Task 2.3**: Write test for search endpoint with invalid parameters
- [ ] **Task 2.4**: Run all backend tests and ensure passing
- [ ] **Task 2.5**: Write test for search endpoint pagination
- [ ] **Task 2.6**: Run all backend tests and ensure passing
- [ ] **Task 2.7**: Write test for search endpoint with filters
- [ ] **Task 2.8**: Run all backend tests and ensure passing
- [ ] **Task 2.9**: Write test for search endpoint error handling
- [ ] **Task 2.10**: Run all backend tests and ensure passing

### app/api/api_v1/endpoints/analytics.py (50% coverage)
- [ ] **Task 3.1**: Write test for analytics tool usage endpoint
- [ ] **Task 3.2**: Run all backend tests and ensure passing
- [ ] **Task 3.3**: Write test for analytics conversation flow endpoint
- [ ] **Task 3.4**: Run all backend tests and ensure passing
- [ ] **Task 3.5**: Write test for analytics error tracking endpoint
- [ ] **Task 3.6**: Run all backend tests and ensure passing
- [ ] **Task 3.7**: Write test for analytics working directory endpoint
- [ ] **Task 3.8**: Run all backend tests and ensure passing
- [ ] **Task 3.9**: Write test for analytics response time endpoint
- [ ] **Task 3.10**: Run all backend tests and ensure passing
- [ ] **Task 3.11**: Write test for analytics git branch endpoint
- [ ] **Task 3.12**: Run all backend tests and ensure passing
- [ ] **Task 3.13**: Write test for analytics token efficiency endpoint
- [ ] **Task 3.14**: Run all backend tests and ensure passing
- [ ] **Task 3.15**: Write test for analytics session depth endpoint
- [ ] **Task 3.16**: Run all backend tests and ensure passing
- [ ] **Task 3.17**: Write test for analytics cost prediction endpoint
- [ ] **Task 3.18**: Run all backend tests and ensure passing

### app/api/api_v1/endpoints/messages.py (60% coverage)
- [ ] **Task 4.1**: Write test for messages endpoint missing functionality (lines 156-246)
- [ ] **Task 4.2**: Run all backend tests and ensure passing
- [ ] **Task 4.3**: Write test for message creation edge cases
- [ ] **Task 4.4**: Run all backend tests and ensure passing
- [ ] **Task 4.5**: Write test for message update functionality
- [ ] **Task 4.6**: Run all backend tests and ensure passing
- [ ] **Task 4.7**: Write test for message deletion functionality
- [ ] **Task 4.8**: Run all backend tests and ensure passing

### app/services/ingest.py (60% coverage)
- [ ] **Task 5.1**: Write test for ingest service error handling (lines 221, 226-227)
- [ ] **Task 5.2**: Run all backend tests and ensure passing
- [ ] **Task 5.3**: Write test for ingest service validation logic (lines 237-255)
- [ ] **Task 5.4**: Run all backend tests and ensure passing
- [ ] **Task 5.5**: Write test for ingest service file processing (lines 360-362)
- [ ] **Task 5.6**: Run all backend tests and ensure passing
- [ ] **Task 5.7**: Write test for ingest service batch operations (lines 388-451)
- [ ] **Task 5.8**: Run all backend tests and ensure passing
- [ ] **Task 5.9**: Write test for ingest service async operations (lines 492-558)
- [ ] **Task 5.10**: Run all backend tests and ensure passing

### app/api/dependencies.py (60% coverage)
- [ ] **Task 6.1**: Write test for dependency injection functions (lines 13, 20-30)
- [ ] **Task 6.2**: Run all backend tests and ensure passing
- [ ] **Task 6.3**: Write test for authentication dependencies
- [ ] **Task 6.4**: Run all backend tests and ensure passing

## Priority 2: Moderate Coverage Gaps (70-90%)

### app/api/api_v1/endpoints/websocket.py (64% coverage)
- [ ] **Task 7.1**: Write test for websocket connection handling (lines 26-46)
- [ ] **Task 7.2**: Run all backend tests and ensure passing
- [ ] **Task 7.3**: Write test for websocket message processing (lines 56-88)
- [ ] **Task 7.4**: Run all backend tests and ensure passing
- [ ] **Task 7.5**: Write test for websocket error scenarios (lines 96-109)
- [ ] **Task 7.6**: Run all backend tests and ensure passing

### app/main.py (64% coverage)
- [ ] **Task 8.1**: Write test for FastAPI app initialization (lines 32-49)
- [ ] **Task 8.2**: Run all backend tests and ensure passing
- [ ] **Task 8.3**: Write test for middleware setup (lines 82, 93, 104)
- [ ] **Task 8.4**: Run all backend tests and ensure passing
- [ ] **Task 8.5**: Write test for startup/shutdown events (lines 114-122)
- [ ] **Task 8.6**: Run all backend tests and ensure passing

### app/core/security.py (67% coverage)
- [ ] **Task 9.1**: Write test for security functions (lines 11, 16)
- [ ] **Task 9.2**: Run all backend tests and ensure passing

### app/services/realtime_integration.py (67% coverage)
- [ ] **Task 10.1**: Write test for realtime integration connection (lines 25, 33-34)
- [ ] **Task 10.2**: Run all backend tests and ensure passing
- [ ] **Task 10.3**: Write test for realtime integration message handling (lines 55, 65, 69-80)
- [ ] **Task 10.4**: Run all backend tests and ensure passing
- [ ] **Task 10.5**: Write test for realtime integration error scenarios (lines 84-95, 113-114)
- [ ] **Task 10.6**: Run all backend tests and ensure passing

### app/services/session.py (86% coverage)
- [ ] **Task 11.1**: Write test for session service edge cases (lines 85-86, 155-156)
- [ ] **Task 11.2**: Run all backend tests and ensure passing
- [ ] **Task 11.3**: Write test for session service error handling (lines 239, 242, 244-245)
- [ ] **Task 11.4**: Run all backend tests and ensure passing

### app/middleware/rate_limit.py (89% coverage)
- [ ] **Task 12.1**: Write test for rate limiting edge cases (lines 100-112)
- [ ] **Task 12.2**: Run all backend tests and ensure passing

### app/services/websocket_manager.py (91% coverage)
- [ ] **Task 13.1**: Write test for websocket manager error scenarios (lines 147-149, 179, 183)
- [ ] **Task 13.2**: Run all backend tests and ensure passing
- [ ] **Task 13.3**: Write test for websocket manager connection lifecycle (lines 265, 282-283)
- [ ] **Task 13.4**: Run all backend tests and ensure passing

## Priority 3: Near-Complete Coverage (90%+)

### app/api/api_v1/api.py (92% coverage)
- [ ] **Task 14.1**: Write test for missing line 31 in API router
- [ ] **Task 14.2**: Run all backend tests and ensure passing

### app/schemas/ingest.py (94% coverage)
- [ ] **Task 15.1**: Write test for schema validation edge cases (lines 50-52, 55)
- [ ] **Task 15.2**: Run all backend tests and ensure passing

### app/services/ingest_debug.py (94% coverage)
- [ ] **Task 16.1**: Write test for debug service edge cases (lines 168-171, 192-198)
- [ ] **Task 16.2**: Run all backend tests and ensure passing

### app/models/project.py (97% coverage)
- [ ] **Task 17.1**: Write test for project model line 34
- [ ] **Task 17.2**: Run all backend tests and ensure passing

### app/services/search.py (97% coverage)
- [ ] **Task 18.1**: Write test for search service edge cases (lines 202, 222, 247-248, 394)
- [ ] **Task 18.2**: Run all backend tests and ensure passing

### app/services/message.py (98% coverage)
- [ ] **Task 19.1**: Write test for message service lines 66, 237
- [ ] **Task 19.2**: Run all backend tests and ensure passing

### app/api/api_v1/endpoints/sessions.py (98% coverage)
- [ ] **Task 20.1**: Write test for sessions endpoint line 52
- [ ] **Task 20.2**: Run all backend tests and ensure passing

### app/services/project.py (99% coverage)
- [ ] **Task 21.1**: Write test for project service line 120
- [ ] **Task 21.2**: Run all backend tests and ensure passing

## Final Verification
- [ ] **Task 22.1**: Run full coverage report to verify overall improvement
- [ ] **Task 22.2**: Run all backend tests final verification
- [ ] **Task 22.3**: Document final coverage statistics

## Notes
- Focus on the `app/services/analytics.py` file first as it has the lowest coverage (20%)
- Each test should target specific uncovered lines shown in the coverage report
- Ensure all tests pass before moving to the next file
- Use existing test patterns and fixtures from the current test suite

**Test Command**: `poetry run pytest backend/tests/ -v --cov=app --cov-report=term-missing`
