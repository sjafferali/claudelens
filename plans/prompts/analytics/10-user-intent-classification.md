# User Intent Classification Implementation

## Context
ClaudeLens captures message content and tool usage patterns, enabling topic classification that displays in the "Topics" section of the session details panel.

## Feature Description
Implement intelligent topic detection to automatically tag sessions with relevant topics (Web Development, Claude API, Data Visualization, etc.) for the Topics section in the details panel.

## Requirements

### Backend Implementation
1. Create endpoints:
   - `GET /api/v1/analytics/topics/extract` - Extract topics for a session
   - `GET /api/v1/analytics/topics/suggest` - Suggest related topics
   - `POST /api/v1/analytics/topics/train` - Improve topic detection

2. Topic extraction approach:
   ```python
   # Feature extraction from messages:
   #   - Keywords and phrases
   #   - File extensions accessed
   #   - Tool usage patterns
   #   - Library/framework mentions
   #   - Error types encountered
   # Topic categories:
   #   - Web Development
   #   - API Integration
   #   - Data Visualization
   #   - Machine Learning
   #   - Database Operations
   #   - DevOps/Deployment
   #   - Testing/QA
   #   - Documentation
   ```

3. Response schemas:
   ```typescript
   // Topic extraction
   {
     session_id: string,
     topics: [{
       name: string,
       confidence: number,
       category: string,
       relevance_score: number
     }],
     suggested_topics: string[],
     extraction_method: 'keyword' | 'ml' | 'hybrid'
   }

   // Topic aggregation
   {
     popular_topics: [{
       name: string,
       session_count: number,
       trend: 'trending' | 'stable' | 'declining'
     }],
     topic_combinations: [{
       topics: string[],
       frequency: number
     }]
   }
   ```

### Frontend Implementation

1. **Topics Section Component**: `SessionTopics.tsx`
   ```typescript
   // Displays in the details panel
   // Shows extracted topics as tags
   // Consistent with existing UI design
   ```

2. **Tag Display**:
   ```html
   <div class="details-section">
     <h3 class="details-title">Topics</h3>
     <div class="tags">
       <span class="tag">Web Development</span>
       <span class="tag">Claude API</span>
       <span class="tag">Data Visualization</span>
       <span class="tag">React</span>
     </div>
   </div>
   ```

3. **Interactive Features**:
   - Click tag to filter sessions by topic
   - Add/remove topics manually
   - Suggest related topics on hover
   - Topic confidence indicator (optional)

### UI/UX Requirements
- **Tag Styling**: Use existing tag class from mockup
- **Layout**: Flexible wrap for multiple topics
- **Colors**: Consistent with theme variables
- **Interactions**: Subtle hover effects
- **Loading**: Graceful loading state

### Topic Detection Rules
```typescript
const topicRules = {
  "Web Development": ["react", "vue", "angular", "frontend", "css", "html"],
  "Claude API": ["claude", "anthropic", "api", "webhook", "endpoint"],
  "Data Visualization": ["chart", "graph", "plot", "dashboard", "metrics"],
  "Database": ["mongodb", "sql", "postgres", "database", "query"],
  "Testing": ["test", "jest", "vitest", "pytest", "unit test"],
  // ... more rules
};
```

### Visual Styling
```css
/* Reuse existing tag styles from mockup */
.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.tag {
  padding: 4px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  border-radius: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.tag:hover {
  background: var(--border-primary);
  color: var(--text-primary);
}
```

## Technical Considerations
- Cache extracted topics per session
- Use keyword matching for initial implementation
- Add ML-based extraction as enhancement
- Support user corrections to improve accuracy
- Lightweight processing for real-time updates

## Success Criteria
- Topics load instantly in details panel
- Accurate topic extraction from session content
- Consistent tag styling with mockup
- Interactive filtering capabilities
- Graceful handling of sessions without clear topics
