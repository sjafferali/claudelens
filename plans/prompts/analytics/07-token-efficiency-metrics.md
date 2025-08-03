# Token Efficiency Metrics Implementation

## Context
ClaudeLens extracts token usage from message metadata, displaying it prominently in the stat cards UI with detailed breakdowns in the session details panel.

## Feature Description
Implement token analytics that powers the "Tokens" stat card (showing total token count) and provides detailed efficiency metrics in the session analytics view.

## Requirements

### Backend Implementation
1. Create endpoints:
   - `GET /api/v1/analytics/tokens/summary` - For stat card display
   - `GET /api/v1/analytics/tokens/detailed` - For detailed breakdown
   - `GET /api/v1/analytics/tokens/efficiency` - For efficiency scores

2. Query parameters:
   - `session_id`: Filter by specific session
   - `time_range`: TimeRange enum
   - `include_cache_metrics`: boolean

3. Database aggregation:
   ```python
   # Extract token counts from message metadata
   # Sum total tokens for stat card
   # Calculate token breakdown by type
   # Compute efficiency metrics
   # Format for display (e.g., "45K" for 45,000)
   ```

4. Response schemas:
   ```typescript
   // Summary for stat card
   {
     total_tokens: number,
     formatted_total: string,  // e.g., "45K", "1.2M"
     cost_estimate: number,
     trend: 'up' | 'down' | 'stable'
   }

   // Detailed breakdown
   {
     token_breakdown: {
       input_tokens: number,
       output_tokens: number,
       cache_creation: number,
       cache_read: number,
       total: number
     },
     efficiency_metrics: {
       cache_hit_rate: number,
       input_output_ratio: number,
       avg_tokens_per_message: number,
       cost_per_token: number
     },
     formatted_values: {
       total: string,      // "45K"
       input: string,      // "28K"
       output: string,     // "17K"
     }
   }
   ```

### Frontend Implementation

1. **Token Stat Card**: `TokenStatCard.tsx`
   ```typescript
   // Displays in the 2x2 stat grid
   // Shows formatted token count (e.g., "45K")
   // Styling:
   // - stat-value: 24px font, var(--accent-primary)
   // - stat-label: 12px font, var(--text-muted)
   // - Subtle trend indicator (optional)
   ```

2. **Token Details Section**: `TokenDetailsPanel.tsx`
   ```typescript
   // New section in details panel
   // Shows token breakdown with progress bars
   // Visual breakdown:
   // - Input tokens: blue bar
   // - Output tokens: green bar
   // - Cache tokens: purple bar
   ```

3. **Visual Design**:
   ```html
   <!-- Stat card -->
   <div class="stat-card">
     <div class="stat-value">45K</div>
     <div class="stat-label">Tokens</div>
   </div>

   <!-- Details panel section -->
   <div class="details-section">
     <h3 class="details-title">Token Usage</h3>
     <div class="token-breakdown">
       <div class="token-bar">
         <div class="token-segment input" style="width: 62%"></div>
         <div class="token-segment output" style="width: 38%"></div>
       </div>
       <div class="token-stats">
         <span class="token-stat">Input: 28K</span>
         <span class="token-stat">Output: 17K</span>
       </div>
     </div>
   </div>
   ```

### UI/UX Requirements
- **Stat Card**: Display total tokens with smart formatting (K, M)
- **Details Panel**: Visual breakdown with color-coded segments
- **Hover Effects**: Show exact counts on hover
- **Efficiency Indicators**: Small badges for high cache hit rates
- **Theme Support**: Colors adjust for dark/light themes

### Token Formatting Rules
```typescript
function formatTokenCount(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(0)}K`;
  return count.toString();
}
```

### Visual Styling
```css
.token-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  display: flex;
  overflow: hidden;
}

.token-segment {
  transition: width 0.3s ease;
}

.token-segment.input {
  background: var(--accent-primary);
}

.token-segment.output {
  background: var(--success);
}

.token-stat {
  font-size: 12px;
  color: var(--text-muted);
  margin-right: 16px;
}
```

## Technical Considerations
- Cache token calculations for performance
- Handle missing token data gracefully
- Update counts in real-time as messages arrive
- Format large numbers for readability

## Success Criteria
- Token count loads instantly in stat card
- Accurate token counting and categorization
- Clear visual breakdown of token types
- Responsive updates as session progresses
- Consistent formatting across all displays
