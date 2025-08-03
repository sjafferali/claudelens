# Cost Prediction Dashboard Implementation

## Context
ClaudeLens tracks cost data per message and session, displaying it in the "Cost" stat card with detailed analytics available in expanded views.

## Feature Description
Implement cost tracking and prediction that powers the Cost stat card (showing session/project costs) and provides detailed cost breakdowns and predictions in analytics views.

## Requirements

### Backend Implementation
1. Create endpoints:
   - `GET /api/v1/analytics/cost/summary` - For stat card display
   - `GET /api/v1/analytics/cost/breakdown` - For detailed cost analysis
   - `GET /api/v1/analytics/cost/prediction` - For cost forecasting

2. Query parameters:
   - `session_id`: Filter by specific session
   - `project_id`: Filter by project
   - `time_range`: TimeRange enum
   - `prediction_days`: For forecast endpoint (7, 14, 30)

3. Cost calculation:
   ```python
   # Extract costUsd from messages
   # Sum total costs for stat card
   # Break down by model type
   # Calculate trends and predictions
   # Format currency display
   ```

4. Response schemas:
   ```typescript
   // Summary for stat card
   {
     total_cost: number,
     formatted_cost: string,  // e.g., "$0.45", "$12.30"
     currency: string,
     trend: 'up' | 'down' | 'stable',
     period: string
   }

   // Detailed breakdown
   {
     cost_breakdown: {
       by_model: [{
         model: string,
         cost: number,
         percentage: number,
         message_count: number
       }],
       by_time: [{
         timestamp: string,
         cost: number,
         cumulative: number
       }]
     },
     cost_metrics: {
       avg_cost_per_message: number,
       avg_cost_per_hour: number,
       most_expensive_model: string,
       cost_efficiency_score: number
     }
   }
   ```

### Frontend Implementation

1. **Cost Stat Card**: `CostStatCard.tsx`
   ```typescript
   // Displays in the 2x2 stat grid
   // Shows formatted cost (e.g., "$0.45")
   // Styling:
   // - stat-value: 24px font, var(--accent-primary)
   // - stat-label: 12px font, var(--text-muted)
   // - Shows "$0.00" when no cost data
   ```

2. **Cost Details Section**: `CostDetailsPanel.tsx`
   ```typescript
   // New section in details panel (optional)
   // Shows cost breakdown by model
   // Mini chart showing cost over time
   // Budget warnings if applicable
   ```

3. **Visual Design**:
   ```html
   <!-- Stat card -->
   <div class="stat-card">
     <div class="stat-value">$0.45</div>
     <div class="stat-label">Cost</div>
   </div>

   <!-- Alternative "No cost data" display -->
   <div class="stat-card">
     <div class="stat-value">$0.00</div>
     <div class="stat-label">Cost</div>
   </div>

   <!-- Cost breakdown in details (optional) -->
   <div class="cost-breakdown">
     <div class="cost-item">
       <span class="cost-model">claude-3-opus</span>
       <span class="cost-amount">$0.35</span>
     </div>
     <div class="cost-item">
       <span class="cost-model">claude-3-sonnet</span>
       <span class="cost-amount">$0.10</span>
     </div>
   </div>
   ```

### UI/UX Requirements
- **Stat Card**: Display cost with proper currency formatting
- **No Data State**: Show "$0.00" or "No cost data" gracefully
- **Hover Details**: Show breakdown on hover (optional)
- **Color Coding**: Green for low cost, yellow for medium, red for high
- **Real-time Updates**: Update as new costs are incurred

### Cost Display Rules
```typescript
function formatCost(cost: number): string {
  if (cost === 0) return "$0.00";
  if (cost < 0.01) return "<$0.01";
  if (cost < 1) return `$${cost.toFixed(2)}`;
  if (cost < 100) return `$${cost.toFixed(2)}`;
  return `$${cost.toFixed(0)}`;
}
```

### Visual Styling
```css
.stat-card .stat-value {
  font-family: 'Monaco', 'Menlo', monospace;
}

.cost-breakdown {
  margin-top: 12px;
  font-size: 13px;
}

.cost-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  color: var(--text-secondary);
}

.cost-amount {
  font-family: 'Monaco', 'Menlo', monospace;
  color: var(--text-primary);
}
```

## Technical Considerations
- Handle missing cost data gracefully
- Cache cost calculations for performance
- Support multiple currencies (future)
- Real-time cost updates as messages arrive
- Consider free tier vs paid usage

## Success Criteria
- Cost displays instantly in stat card
- Accurate cost calculation from message data
- Clear "No cost data" state when applicable
- Consistent currency formatting
- Updates reflect immediately in UI
