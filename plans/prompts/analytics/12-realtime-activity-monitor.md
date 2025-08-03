# Real-time Activity Monitor Implementation

## Context
ClaudeLens ingests messages in real-time, enabling live monitoring of Claude activity across all projects and sessions.

## Feature Description
Implement a real-time activity dashboard showing live Claude interactions, active sessions, and instant metrics with WebSocket updates.

## Requirements

### Backend Implementation
1. Create WebSocket endpoints:
   - `/ws/activity-stream` - Real-time message stream
   - `/ws/metrics-updates` - Live metric updates

2. REST endpoints:
   - `GET /api/v1/analytics/live-activity`
   - `GET /api/v1/analytics/active-sessions`

3. Real-time processing:
   ```python
   # WebSocket message types:
   #   - new_message
   #   - session_started
   #   - session_ended
   #   - metric_update
   #   - alert_triggered
   # Stream processing:
   #   - Message deduplication
   #   - Rate limiting
   #   - Metric aggregation
   #   - Alert detection
   ```

4. Response schemas:
   ```typescript
   // WebSocket message
   {
     type: 'new_message' | 'session_update' | 'metric_update' | 'alert',
     timestamp: string,
     data: {
       session_id?: string,
       project?: string,
       message_type?: string,
       cost?: number,
       tool?: string,
       metric_updates?: {
         active_sessions: number,
         messages_per_minute: number,
         current_cost_rate: number
       }
     }
   }

   // Live activity response
   {
     active_sessions: [{
       session_id: string,
       project: string,
       started_at: string,
       message_count: number,
       current_cost: number,
       last_activity: string,
       status: 'active' | 'idle' | 'thinking'
     }],
     recent_activity: [{
       timestamp: string,
       type: string,
       project: string,
       summary: string,
       cost: number
     }],
     live_metrics: {
       messages_per_minute: number,
       active_sessions: number,
       cost_per_hour_rate: number,
       active_projects: string[]
     }
   }
   ```

### Frontend Implementation
1. Create components:
   - `ActivityFeed.tsx` - Scrolling activity feed
   - `LiveMetrics.tsx` - Real-time metric cards
   - `ActiveSessionsGrid.tsx` - Grid of active sessions
   - `ActivitySparklines.tsx` - Mini charts for trends
   - `AlertNotifications.tsx` - Real-time alerts

2. Features:
   - Auto-scrolling activity feed
   - Live updating metrics
   - Session status indicators
   - Notification system
   - Activity filtering

### UI/UX Requirements
- Smooth animations for updates
- Color-coded activity types
- Pulse effects for new activity
- Minimal latency (<100ms)
- Responsive grid layout

## Technical Considerations
- WebSocket connection management
- Reconnection handling
- Message buffering
- Rate limiting for high activity
- Efficient DOM updates

## Success Criteria
- Real-time updates within 100ms
- Handle 1000+ concurrent sessions
- Smooth UI with no jank
- Clear activity visualization
- Reliable WebSocket connections
