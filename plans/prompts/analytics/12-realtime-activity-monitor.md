# Real-time Activity Monitor Implementation

## Status: ✅ COMPLETED

### Implementation Summary:
- Backend WebSocket endpoints created: `/ws/session/{session_id}` and `/ws/stats/{session_id}`
- Backend REST endpoints created: `/api/v1/analytics/session/live` and `/api/v1/analytics/stats/live`
- Frontend component created: `LiveStatCards.tsx` with real-time updates
- WebSocket connection manager with auto-reconnection and heartbeat
- Smooth number animations and pulse effects on stat updates
- Connection status indicator (Live/Connecting/Error/Offline)
- Integration with ingest system for automatic updates
- Full Analytics page integration with session selector

## Context
ClaudeLens tracks messages in real-time, enabling live updates to the stat cards and session details as activity occurs.

## Feature Description
Implement real-time updates for stat cards (Messages, Tools Used, Tokens, Cost) and session activity using WebSocket connections, ensuring the UI reflects live changes.

## Requirements

### Backend Implementation
1. Create WebSocket endpoints:
   - `/ws/session/{session_id}` - Session-specific updates
   - `/ws/stats/{session_id}` - Stat card updates

2. REST endpoints:
   - `GET /api/v1/analytics/session/live` - Current session state
   - `GET /api/v1/analytics/stats/live` - Live stat values

3. Real-time event types:
   ```python
   # WebSocket events for stat updates:
   #   - message_count_update
   #   - tool_usage_update
   #   - token_count_update
   #   - cost_update
   #   - new_message
   # Event payload includes incremental updates
   ```

4. Response schemas:
   ```typescript
   // Stat update event
   {
     type: 'stat_update',
     stat_type: 'messages' | 'tools' | 'tokens' | 'cost',
     session_id: string,
     timestamp: string,
     update: {
       new_value: number,
       formatted_value: string,  // "262", "18", "45K", "$0.45"
       delta: number,
       animation: 'increment' | 'none'
     }
   }

   // New message event
   {
     type: 'new_message',
     session_id: string,
     message: {
       uuid: string,
       author: string,
       timestamp: string,
       preview: string,
       tool_used?: string
     }
   }
   ```

### Frontend Implementation

1. **Real-time Stat Cards**: `LiveStatCards.tsx`
   ```typescript
   // WebSocket connection for each stat card
   // Smooth number animations on update
   // Visual pulse effect on change
   // Handles reconnection gracefully
   ```

2. **Update Animation**:
   ```css
   @keyframes statPulse {
     0% { transform: scale(1); }
     50% { transform: scale(1.05); color: var(--accent-hover); }
     100% { transform: scale(1); }
   }

   .stat-value.updating {
     animation: statPulse 0.3s ease;
   }
   ```

3. **Live Message Updates**: `LiveMessageFeed.tsx`
   ```typescript
   // Append new messages to conversation
   // Smooth scroll to new content
   // Update message count in real-time
   // Highlight new messages briefly
   ```

### UI/UX Requirements
- **Stat Updates**: Smooth number transitions
- **Visual Feedback**: Subtle pulse on update
- **Performance**: No UI jank during updates
- **Connection State**: Show connection status
- **Graceful Degradation**: Work without WebSocket

### Implementation Details

1. **Stat Card Updates**:
   ```typescript
   // Messages stat card
   const [messageCount, setMessageCount] = useState(262);

   useWebSocket(`/ws/stats/${sessionId}`, (event) => {
     if (event.stat_type === 'messages') {
       animateValue(messageCount, event.update.new_value);
       pulseElement('.stat-card.messages');
     }
   });
   ```

2. **Connection Indicator**:
   ```html
   <div class="connection-status">
     <span class="status-dot active"></span>
     <span class="status-text">Live</span>
   </div>
   ```

3. **Number Animation**:
   ```typescript
   function animateValue(from: number, to: number, duration = 300) {
     const start = Date.now();
     const delta = to - from;

     const animate = () => {
       const progress = Math.min((Date.now() - start) / duration, 1);
       const current = Math.round(from + delta * easeOutQuad(progress));
       setValue(current);

       if (progress < 1) requestAnimationFrame(animate);
     };

     requestAnimationFrame(animate);
   }
   ```

### Visual Styling
```css
.connection-status {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-dot.active {
  background: var(--success);
  box-shadow: 0 0 4px var(--success);
}
```

## Technical Considerations
- Debounce rapid updates to prevent UI thrashing
- Batch updates when multiple stats change
- Handle WebSocket reconnection gracefully
- Cache last known values for offline mode
- Minimize re-renders with targeted updates

## Success Criteria
- Updates appear within 100ms of server event
- Smooth animations without performance impact
- Clear connection status indication
- Graceful handling of connection loss
- No memory leaks from event listeners
