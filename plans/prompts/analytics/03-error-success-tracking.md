# Error and Success Rate Tracking Implementation

## Context
ClaudeLens captures tool execution results in the `toolUseResult` field, with a new UI design featuring stat cards and a details panel for comprehensive session analytics.

## Feature Description
Implement error tracking and success rate analytics that integrates seamlessly with the stat cards and details panel, providing at-a-glance metrics and detailed error analysis.

## Requirements

### Backend Implementation
1. Create endpoints:
   - `GET /api/v1/analytics/session/health` - For session health stat card
   - `GET /api/v1/analytics/errors/detailed` - For error details in panel
   - `GET /api/v1/analytics/success-rate` - For success rate metrics

2. Query parameters:
   - `session_id`: Filter by specific session
   - `time_range`: TimeRange enum
   - `error_severity`: 'critical' | 'warning' | 'info'

3. Database aggregation:
   ```python
   # Parse toolUseResult for success/error status
   # Calculate overall session health score
   # Identify error patterns and frequency
   # Group errors by type and severity
   ```

4. Response schemas:
   ```typescript
   // Session health for stat card
   {
     success_rate: number,
     total_operations: number,
     error_count: number,
     health_status: 'excellent' | 'good' | 'fair' | 'poor'
   }

   // Detailed errors for panel
   {
     errors: [{
       timestamp: string,
       tool: string,
       error_type: string,
       severity: 'critical' | 'warning' | 'info',
       message: string,
       context: string
     }],
     error_summary: {
       by_type: Record<string, number>,
       by_tool: Record<string, number>
     }
   }
   ```

### Frontend Implementation

1. **Success Rate Stat Card**: `SuccessRateCard.tsx`
   ```typescript
   // Part of the 2x2 stat grid
   // Shows success percentage as primary metric
   // Color-coded based on rate:
   // - > 95%: var(--success) green
   // - 80-95%: var(--text-primary) normal
   // - < 80%: #ef4444 red
   ```

2. **Error Details Section**: `ErrorDetailsPanel.tsx`
   ```typescript
   // In the details panel below "Tools Used"
   // Shows recent errors as expandable items
   // Error item styling:
   // - Critical: red badge
   // - Warning: orange badge
   // - Info: blue badge
   ```

3. **Visual Indicators**:
   ```html
   <!-- Success rate in stat card -->
   <div class="stat-card">
     <div class="stat-value" style="color: var(--success)">95.2%</div>
     <div class="stat-label">Success Rate</div>
   </div>

   <!-- Error badges in details -->
   <div class="error-item">
     <span class="error-badge critical">Critical</span>
     <span class="error-tool">Bash</span>
     <span class="error-time">2 min ago</span>
   </div>
   ```

### UI/UX Requirements
- **Stat Card**: Show success rate with color coding
- **Details Panel**: List recent errors with severity badges
- **Inline Indicators**: Add small error icons next to failed tool calls in conversation
- **Hover Details**: Show error message on hover
- **Theme Support**: Error colors work in both dark/light themes

### Integration Points
1. **Message Display**: Add error indicators to failed tool calls
2. **Session Stats**: Include error count in session statistics
3. **Real-time Updates**: Update error count as they occur
4. **Export Function**: Include error log in session export

### Error Visualization
```css
.error-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.error-badge.critical {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.error-badge.warning {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}
```

## Technical Considerations
- Parse toolUseResult efficiently for error detection
- Cache success rates for performance
- Sanitize error messages for display
- Group similar errors to reduce noise

## Success Criteria
- Success rate calculation < 50ms
- Error details load instantly
- Clear visual distinction between error severities
- Seamless integration with existing UI components
- Helpful error messages that guide resolution
