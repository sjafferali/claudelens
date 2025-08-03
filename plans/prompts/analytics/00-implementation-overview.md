# ClaudeLens Analytics Implementation Overview

This directory contains implementation prompts for comprehensive analytics features in ClaudeLens. Each prompt is designed to integrate with the new UI design featuring stat cards, details panels, and modern visualizations.

## UI Design Integration

The new ClaudeLens UI features:
- **Stat Cards**: Compact 2x2 grid showing Messages, Tools Used, Tokens, and Cost
- **Details Panel**: Right sidebar with Session Details, Statistics, Tools Used, and Topics sections
- **Modern Theme**: Dark/light mode support with CSS variables
- **Responsive Layout**: Sidebar navigation, main content area, and details panel

## Implementation Order

The prompts are numbered in the recommended implementation order, considering dependencies and complexity:

### Phase 1: Foundation Analytics (1-4)
1. **01-tool-usage-analytics.md** - Tool usage tracking with tag-based visualization
2. **02-conversation-flow-analytics.md** - Conversation structure in timeline view
3. **03-error-success-tracking.md** - Error patterns integrated with stat cards
4. **04-working-directory-insights.md** - Directory insights for details panel

### Phase 2: Performance Analytics (5-8)
5. **05-response-time-analytics.md** - Response time for performance stat cards
6. **06-git-branch-analytics.md** - Git branch patterns in session context
7. **07-token-efficiency-metrics.md** - Token usage for the stat grid
8. **08-session-depth-analysis.md** - Complexity metrics for session stats

### Phase 3: Advanced Analytics (9-12)
9. **09-cost-prediction-dashboard.md** - Cost predictions for the Cost stat card
10. **10-user-intent-classification.md** - Intent tags for Topics section
11. **11-performance-benchmarking.md** - Comparative view in details panel
12. **12-realtime-activity-monitor.md** - Live updates for stat cards

## Key Data Points Available

From the ClaudeLens data model, we have access to:

- **Message Level**: uuid, sessionId, type, timestamp, model, costUsd, durationMs, tool usage
- **Session Level**: sessionId, projectId, startedAt, endedAt, messageCount, totalCost
- **Project Level**: name, path, description, stats (message_count, session_count)
- **Additional Context**: cwd, gitBranch, version, isSidechain, parentUuid

## UI Component Integration

Each analytics feature should integrate with:

1. **Stat Cards** (320x140px each):
   - Large value display (24px font)
   - Descriptive label below
   - Accent color highlighting
   - Background: var(--bg-primary)

2. **Details Panel Sections**:
   - Section title (16px font)
   - Detail items with label/value pairs
   - Tag-based displays for categorical data
   - Consistent spacing and borders

3. **Visualization Areas**:
   - Timeline view for conversations
   - Compact/Raw view toggles
   - Search and filter integration
   - Export functionality

## Common Patterns

Each implementation should follow these patterns:

1. **Backend**: FastAPI endpoints with MongoDB aggregation pipelines
2. **Frontend**: React components with TypeScript and CSS variables
3. **Visualizations**: Recharts for charts, custom components for stat cards
4. **Styling**: Use CSS variables for theme support
5. **Export**: CSV/PDF export for all analytics data

## Technical Stack

- **Backend**: FastAPI (Python 3.11+), Motor (async MongoDB), Redis
- **Frontend**: React 18+, TypeScript, Recharts, CSS Variables
- **Database**: MongoDB with aggregation pipelines
- **Real-time**: WebSockets via FastAPI
- **Testing**: Pytest (backend), Vitest (frontend)

## Performance Targets

- Query response time: < 500ms for standard queries
- Real-time updates: < 100ms latency
- Dashboard load time: < 2 seconds
- Support scale: 1M+ messages, 10K+ sessions

## Success Metrics

Each analytics feature should:
1. Fit seamlessly into the new UI design
2. Provide instant visual feedback via stat cards
3. Support theme switching (dark/light)
4. Scale gracefully on different screen sizes
5. Maintain consistent styling with CSS variables
