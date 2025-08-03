# ClaudeLens UI Enhancement Mockups

This directory contains interactive HTML mockups for utilizing the existing `parentUuid` and `isSidechain` fields to enhance the conversation UI.

## Viewing the Mockups

Open any HTML file in your browser to see the interactive mockup:

1. **01-thread-navigation-enhancement.html** - Navigate between parent/child messages with visual thread indicators
2. **02-sidechain-visualization.html** - Highlight and navigate parallel task executions (sidechains)
3. **03-conversation-fork-points.html** - Identify and highlight where conversations branch
4. **04-thread-aware-search.html** - Enhanced search that understands message relationships
5. **05-smart-message-grouping.html** - Automatically group and collapse related messages

## Quick Start

```bash
# Open all mockups in your default browser (macOS)
open mockups/*.html

# Or open individually
open mockups/01-thread-navigation-enhancement.html
```

## Implementation Priority

Based on the analysis of your data (98.9% messages have parentUuid, 13.3% are sidechains):

1. **Thread Navigation** (Low complexity, high value) - Quick win
2. **Sidechain Visualization** (Medium complexity, high value) - Shows Claude's capabilities
3. **Smart Message Grouping** (Low-Medium complexity, high value) - Improves readability
4. **Thread-Aware Search** (Medium complexity, medium value) - Power user feature
5. **Fork Points** (Medium complexity, lower value) - Depends on actual fork frequency

## Key Insights from Data Analysis

- **parentUuid** is heavily used (98.9% of messages) - perfect for thread navigation
- **isSidechain** represents 13.3% of messages - significant enough to warrant special UI
- Both fields can be leveraged without any backend changes
- Current UI doesn't fully utilize these rich relationships
