# Analytics Page Bug Fix Task

## Context
ClaudeLens is a web application that archives and analyzes Claude AI conversation history. It consists of:
- **Backend**: FastAPI server (Python) in `/backend` directory
- **Frontend**: React/TypeScript app in `/frontend` directory
- **CLI**: Command-line tool in `/cli` directory for syncing Claude conversations
- **MongoDB**: Database for storing projects, sessions, and messages

## Current Setup
The development environment is running with:
- MongoDB on localhost:27017 (persistent storage)
- Backend API on http://localhost:8000
- Frontend on http://localhost:5173
- One project uploaded: "claudehistoryarchive" with 2 sessions and 357 messages

To start the environment: `./scripts/dev.sh --persistent-db`

## Task Overview
Fix the analytics page issues documented in `/plans/analytics-issue.md`. The analytics page has multiple data inconsistency and display issues that need to be resolved.

## Key Issues to Address
The main problems are:
1. **Triple-counting bug**: Costs and messages are being counted 3x their actual values
2. **Data inconsistencies**: Different sections show different totals for the same metrics
3. **Missing visualizations**: Several charts show no data despite having valid data in the database
4. **Incorrect calculations**: Session counts, branch classifications, and directory structures are wrong

See `/plans/analytics-issue.md` for the complete list of 12 issues with reproduction steps.

## Important Files to Review

### Backend Analytics Logic
- `/backend/app/services/analytics.py` - Main analytics service
- `/backend/app/api/api_v1/endpoints/analytics.py` - API endpoints
- `/backend/app/services/sessions.py` - Session calculations
- `/backend/app/repositories/messages.py` - Message queries

### Frontend Analytics Components
- `/frontend/src/pages/Analytics/` - Main analytics page and subcomponents
- `/frontend/src/services/api/analytics.ts` - API client for analytics
- `/frontend/src/hooks/useAnalytics.ts` - React hooks for analytics data

## Verification Process

After making fixes, use the Playwright MCP tools to verify:

```bash
# Navigate to analytics page
mcp__playwright__browser_navigate url="http://localhost:5173/analytics"

# Take screenshots to compare
mcp__playwright__browser_take_screenshot fullPage=true filename="analytics-after-fix.png"

# Check specific values
mcp__playwright__browser_evaluate function="() => document.querySelector('[data-testid=\"total-cost\"]')?.textContent"
```

## Working Instructions

1. **Keep the issue document updated**: As you work on each issue in `/plans/analytics-issue.md`, mark items with `[x]` when completed and add notes about the fix.

2. **Test incrementally**: After fixing each issue, verify it works before moving to the next.

3. **Check for side effects**: Some issues may be related (e.g., the triple-counting affects multiple sections).

4. **Use the existing data**: The uploaded project has real data that exposes these issues - don't add sample data.

## Suggested Approach

1. **Start with the root cause**: The triple-counting bug in analytics calculations
   - Check if messages are being counted multiple times due to forking
   - Look for issues in aggregation pipelines in MongoDB queries
   - Verify the deduplication logic for shared messages

2. **Fix data flow**: Ensure consistent data between backend and frontend
   - Trace how costs are calculated from messages to final display
   - Check if frontend is doing additional calculations

3. **Address empty visualizations**:
   - Verify data exists in the expected format
   - Check for timezone or data transformation issues
   - Add proper empty states where appropriate

4. **Test thoroughly**: Use both the UI and API endpoints directly to verify fixes

## Helpful Commands

```bash
# Check MongoDB data directly
curl http://localhost:8000/api/v1/sessions/ | jq
curl http://localhost:8000/api/v1/analytics/overview | jq

# Run backend with logs
cd backend && poetry run uvicorn app.main:app --reload --log-level debug

# Check frontend console for errors
# (Use browser dev tools when running Playwright)
```

## Success Criteria
- All 12 issues in `/plans/analytics-issue.md` are resolved
- Analytics page shows consistent, accurate data across all sections
- No console errors or warnings related to analytics
- All visualizations display properly with the test data
- Performance is acceptable (no long loading times)

Remember to update the issue tracking document as you progress and use Playwright to verify each fix visually!
