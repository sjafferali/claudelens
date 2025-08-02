# Task: Implement Session Search and Filtering UI

## Application Overview

ClaudeLens is a web application designed to analyze and visualize Claude AI conversation sessions. The application consists of:

- **Backend**: FastAPI (Python) with MongoDB for data storage
- **Frontend**: React with TypeScript, Tailwind CSS, and Vite
- **Purpose**: Track, analyze, and browse Claude AI conversations organized by projects

The app allows users to:
- View all their Claude AI projects
- Browse sessions within projects
- View detailed conversation threads with full message history
- Analyze costs and token usage

## Current State

### Sessions Page (`/sessions`)
Currently, the Sessions page displays:
- A list of all sessions (or filtered by project if `?project_id=xxx` is in URL)
- Basic pagination (Previous/Next buttons)
- Each session shows:
  - Summary or session ID
  - Message count
  - Time ago (relative timestamp)
  - Total cost
- Clicking a session navigates to `/sessions/{sessionId}` to view the full conversation

### Backend API
The backend already supports comprehensive filtering through the `/api/v1/sessions/` endpoint:

```
GET /api/v1/sessions/
Query Parameters:
- project_id: Filter by specific project
- search: Text search in session summaries
- start_date: Filter sessions starting after this date
- end_date: Filter sessions ending before this date
- sort_by: Sort by started_at, ended_at, message_count, or total_cost
- sort_order: asc or desc
- skip: Pagination offset
- limit: Number of results per page
```

## Task Requirements

### 1. Search Bar Component
Create a search input that:
- Appears at the top of the sessions list
- Has a search icon (from lucide-react)
- Placeholder text: "Search sessions..."
- Debounced input (300ms) to avoid excessive API calls
- Clears search with an X button when text is present

### 2. Filter Panel
Add a collapsible filter panel with:
- **Date Range Picker**
  - Start date input
  - End date input
  - Quick presets: "Last 7 days", "Last 30 days", "Last 3 months", "All time"
  - Use date-fns for date formatting

- **Sort Options**
  - Dropdown with options:
    - "Most Recent" (started_at desc)
    - "Oldest First" (started_at asc)
    - "Most Messages" (message_count desc)
    - "Highest Cost" (total_cost desc)

- **Project Filter** (only show if not already filtered by project)
  - Dropdown to select a specific project
  - "All Projects" option
  - Fetch project list from `/api/v1/projects/`

### 3. Active Filters Display
Show active filters as removable chips below the search bar:
- Each chip shows the filter type and value
- X button to remove individual filters
- "Clear all filters" link when multiple filters active

### 4. URL State Management
Sync all filters with URL query parameters:
- `?search=query`
- `?start_date=2024-01-01`
- `?end_date=2024-12-31`
- `?sort_by=message_count`
- `?sort_order=desc`
- `?project_id=xxx`
- `?page=2` (for pagination)

This allows users to bookmark filtered views and use browser back/forward.

### 5. Loading and Empty States
- Show loading skeleton while fetching filtered results
- Show appropriate empty state messages:
  - "No sessions found matching your filters"
  - Suggest clearing filters if no results
  - Show different message for search vs date filters

## Implementation Details

### Technologies to Use
- **React Hook Form** or native React state for form handling
- **date-fns** for date formatting and manipulation
- **lucide-react** icons for UI elements
- **React Router** `useSearchParams` hook for URL state
- **Tailwind CSS** for styling
- **@tanstack/react-query** for data fetching (already in use)

### Component Structure
1. Create `components/SessionFilters.tsx` for the filter panel
2. Create `components/SearchBar.tsx` for reusable search input
3. Create `components/ActiveFilters.tsx` for filter chips
4. Create `hooks/useSessionFilters.ts` for filter state management
5. Update `pages/Sessions.tsx` to integrate all components

### UI/UX Guidelines
- Filter panel should be collapsible to save space
- Use subtle animations for expanding/collapsing
- Maintain responsive design (stack filters vertically on mobile)
- Show result count: "Showing X of Y sessions"
- Preserve filters when navigating to session detail and back
- Auto-focus search input when user presses "/" key (common pattern)

### State Management
- Store filter state in URL query parameters
- Use React's useSearchParams or a custom hook
- Debounce search input to reduce API calls
- Reset page to 1 when filters change
- Cache filter results with React Query

### Error Handling
- Show toast notifications for API errors
- Validate date ranges (start date before end date)
- Handle invalid URL parameters gracefully
- Provide helpful error messages

## Success Criteria
1. Users can search sessions by text
2. Users can filter by date range with presets
3. Users can sort sessions by different criteria
4. All filters work together (combined filtering)
5. URL reflects current filter state
6. Filter state persists on page refresh
7. Responsive design works on mobile
8. Performance is smooth with debounced search
9. Empty states provide clear guidance
10. Loading states prevent UI flickering

## Testing Considerations
- Test with various filter combinations
- Verify URL parameter encoding/decoding
- Check edge cases (empty results, invalid dates)
- Test on different screen sizes
- Verify accessibility (keyboard navigation, screen readers)
- Performance test with many sessions

## Files to Modify/Create
- `/frontend/src/pages/Sessions.tsx` - Integrate new components
- `/frontend/src/components/SessionFilters.tsx` - New filter panel
- `/frontend/src/components/SearchBar.tsx` - New search component
- `/frontend/src/components/ActiveFilters.tsx` - New filter chips
- `/frontend/src/hooks/useSessionFilters.ts` - New filter logic hook
- `/frontend/src/api/sessions.ts` - Already supports filters, may need minor updates
- `/frontend/src/hooks/useSessions.ts` - Update to use filter parameters
