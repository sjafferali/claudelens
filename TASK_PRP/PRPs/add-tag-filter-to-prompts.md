# TASK PRP: Add Tag/Label Filtering to Prompts Page

## Context

### Current State Analysis
- **Frontend**: The prompts page (`frontend/src/pages/Prompts.tsx`) already has:
  - Search functionality (searches name, description, and tags)
  - Folder filtering
  - Starred-only filtering
  - Sort controls (by name, created_at, updated_at, use_count)
  - Tags are displayed on prompts (lines 636-647)

- **Backend**: The API (`backend/app/api/api_v1/endpoints/prompts.py`) has:
  - `tags` field in the Prompt model
  - Search functionality that includes tags
  - No dedicated tag filtering endpoint parameter

### Patterns to Follow
```yaml
context:
  patterns:
    - file: frontend/src/components/SessionFilters.tsx
      copy: "Expandable filter component pattern with collapsible sections"
    - file: frontend/src/components/ActiveFilters.tsx
      copy: "Active filter pills with removal functionality"
    - file: frontend/src/pages/Sessions.tsx
      copy: "Integration of filters with main page"

  gotchas:
    - issue: "Backend API doesn't have tag filtering parameter"
      fix: "Add tags parameter to list_prompts endpoint"
    - issue: "Search already includes tags"
      fix: "Separate tag filter from text search for precise filtering"
    - issue: "No way to get all unique tags"
      fix: "Add endpoint to get available tags for filter options"
```

## Task Breakdown

### Phase 1: Backend API Updates

#### TASK 1: Add tags parameter to prompts listing endpoint
**ACTION** backend/app/api/api_v1/endpoints/prompts.py:
  - MODIFY: Add `tags` parameter to `list_prompts` function (line ~40)
  - ADD: Query parameter for comma-separated tags
  - MODIFY: Update filter logic to handle tag filtering
  - VALIDATE: `cd backend && poetry run pytest tests/test_endpoints_prompts.py -k list`
  - IF_FAIL: Check MongoDB query syntax for array field filtering
  - ROLLBACK: Remove tags parameter and filter logic

#### TASK 2: Add endpoint to get all unique tags
**ACTION** backend/app/api/api_v1/endpoints/prompts.py:
  - ADD: New endpoint `/tags/` before individual prompt endpoints
  - IMPLEMENT: MongoDB aggregation to get unique tags with counts
  - VALIDATE: Test endpoint with curl: `curl http://localhost:8000/api/v1/prompts/tags/`
  - IF_FAIL: Check MongoDB aggregation pipeline syntax
  - ROLLBACK: Remove the new endpoint

#### TASK 3: Update PromptService for tag operations
**ACTION** backend/app/services/prompt.py:
  - ADD: Method `get_unique_tags()` with aggregation pipeline
  - ADD: Method `filter_by_tags()` for tag-based filtering
  - VALIDATE: `cd backend && poetry run pytest tests/test_services_prompt.py`
  - IF_FAIL: Debug MongoDB aggregation syntax
  - ROLLBACK: Remove new methods

### Phase 2: Frontend Filter Components

#### TASK 4: Create TagFilter component
**ACTION** frontend/src/components/prompts/TagFilter.tsx:
  - CREATE: New component following SessionFilters pattern
  - IMPLEMENT: Multi-select tag dropdown with checkboxes
  - ADD: "Select All" / "Clear All" options
  - VALIDATE: Component renders without errors
  - IF_FAIL: Check import paths and TypeScript types
  - ROLLBACK: Delete the file

#### TASK 5: Add usePromptTags hook
**ACTION** frontend/src/hooks/usePrompts.ts:
  - ADD: New hook `usePromptTags` to fetch available tags
  - IMPLEMENT: React Query integration
  - ADD: Caching strategy for tags
  - VALIDATE: `cd frontend && npm run type-check`
  - IF_FAIL: Fix TypeScript errors
  - ROLLBACK: Remove the new hook

#### TASK 6: Create ActivePromptFilters component
**ACTION** frontend/src/components/prompts/ActivePromptFilters.tsx:
  - CREATE: Component based on ActiveFilters.tsx pattern
  - IMPLEMENT: Tag pills with X buttons for removal
  - ADD: "Clear all tags" option
  - VALIDATE: Component renders and handles clicks
  - IF_FAIL: Debug event handlers
  - ROLLBACK: Delete the file

### Phase 3: Integration with Prompts Page

#### TASK 7: Update Prompts page state management
**ACTION** frontend/src/pages/Prompts.tsx:
  - ADD: State for selected tags (line ~75)
  - MODIFY: usePrompts hook call to include tags parameter
  - ADD: Handler functions for tag selection/removal
  - VALIDATE: State updates correctly on interaction
  - IF_FAIL: Check state update logic
  - ROLLBACK: Remove tag-related state

#### TASK 8: Integrate TagFilter in UI
**ACTION** frontend/src/pages/Prompts.tsx:
  - ADD: Import TagFilter component
  - INSERT: TagFilter in sidebar after existing filters (line ~305)
  - STYLE: Match existing filter card styling
  - VALIDATE: UI renders correctly
  - IF_FAIL: Check component props
  - ROLLBACK: Remove TagFilter from JSX

#### TASK 9: Add ActivePromptFilters to main content
**ACTION** frontend/src/pages/Prompts.tsx:
  - ADD: Import ActivePromptFilters
  - INSERT: ActivePromptFilters above search bar (line ~318)
  - CONNECT: Filter removal handlers
  - VALIDATE: Active filters display and can be removed
  - IF_FAIL: Debug event handler connections
  - ROLLBACK: Remove ActivePromptFilters

### Phase 4: API Client Updates

#### TASK 10: Update prompts API client
**ACTION** frontend/src/api/prompts.ts:
  - ADD: `tags` parameter to `listPrompts` function
  - ADD: New `getPromptTags` function for tags endpoint
  - UPDATE: TypeScript types for new parameters
  - VALIDATE: `cd frontend && npm run type-check`
  - IF_FAIL: Fix type definitions
  - ROLLBACK: Revert API client changes

#### TASK 11: Update API types
**ACTION** frontend/src/api/types.ts:
  - ADD: `PromptTag` interface with name and count
  - UPDATE: `PromptListParams` to include tags
  - VALIDATE: No TypeScript errors
  - IF_FAIL: Adjust interface definitions
  - ROLLBACK: Remove new types

### Phase 5: Testing & Polish

#### TASK 12: Add frontend tests
**ACTION** frontend/src/components/prompts/__tests__/TagFilter.test.tsx:
  - CREATE: Test file for TagFilter component
  - ADD: Tests for rendering, selection, clearing
  - VALIDATE: `cd frontend && npm test TagFilter`
  - IF_FAIL: Fix test implementation
  - ROLLBACK: Delete test file

#### TASK 13: Add backend tests
**ACTION** backend/tests/test_endpoints_prompts_tags.py:
  - CREATE: Test file for tag-related endpoints
  - ADD: Tests for tag filtering and unique tags endpoint
  - VALIDATE: `cd backend && poetry run pytest tests/test_endpoints_prompts_tags.py`
  - IF_FAIL: Fix test assertions
  - ROLLBACK: Delete test file

#### TASK 14: Performance optimization
**ACTION** Multiple files:
  - ADD: Debounce to tag filter changes
  - ADD: Memoization for filtered results
  - ADD: Index on tags field in MongoDB if not exists
  - VALIDATE: Check performance with many tags
  - IF_FAIL: Review optimization approach
  - ROLLBACK: Remove optimizations

#### TASK 15: Accessibility improvements
**ACTION** frontend/src/components/prompts/TagFilter.tsx:
  - ADD: ARIA labels for tag checkboxes
  - ADD: Keyboard navigation support
  - ADD: Focus management
  - VALIDATE: Test with keyboard only
  - IF_FAIL: Review ARIA guidelines
  - ROLLBACK: Keep basic functionality

## Validation Strategy

### Unit Testing
```bash
# Backend
cd backend
poetry run pytest tests/test_endpoints_prompts.py -v
poetry run pytest tests/test_services_prompt.py -v

# Frontend
cd frontend
npm run test:coverage
```

### Integration Testing
```bash
# Start services
cd backend && poetry run uvicorn app.main:app --reload &
cd frontend && npm run dev &

# Test flow
1. Navigate to /prompts
2. Click on tag filter
3. Select multiple tags
4. Verify filtered results
5. Remove tags via pills
6. Verify results update
```

### Performance Testing
- Load page with 100+ prompts
- Apply multiple tag filters
- Measure response time < 200ms
- Check MongoDB query performance

## Success Criteria

1. ✅ Users can filter prompts by one or more tags
2. ✅ Tag filter UI follows existing design patterns
3. ✅ Active filters are clearly displayed with removal options
4. ✅ Performance remains responsive with many tags
5. ✅ Accessibility standards are met
6. ✅ All tests pass
7. ✅ No regression in existing functionality

## Risk Assessment

### High Risk
- **Breaking existing search**: Mitigated by separate tag parameter
- **Performance with many tags**: Mitigated by indexing and limits

### Medium Risk
- **UI complexity**: Mitigated by following existing patterns
- **State management**: Mitigated by controlled components

### Low Risk
- **Browser compatibility**: Using standard React patterns
- **Data migration**: No schema changes required

## Rollback Plan

If critical issues arise:
1. Revert frontend changes (git revert)
2. Revert backend changes (git revert)
3. Clear browser cache
4. Restart services
5. Verify prompts page works without tag filtering

## Dependencies

- MongoDB supports array field queries ✅
- React Query for data fetching ✅
- Existing filter components as patterns ✅
- No external library additions needed ✅

## Assumptions

1. Tags are already stored as arrays in the database
2. Users want AND logic for multiple tags (all selected tags must match)
3. Tag list is reasonable size (<100 unique tags)
4. No tag management UI needed (tags edited via prompt editor)

## Notes

- Consider adding tag autocomplete in future iteration
- Could add tag grouping/categories later
- May want to add tag usage analytics
- Consider tag normalization (lowercase, trim)
