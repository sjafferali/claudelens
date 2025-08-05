# Analytics Page Issues

This document lists all issues found on the ClaudeLens Analytics page during testing with real data.

## Data Inconsistency Issues

### [x] Issue 1: Cost Mismatch Between Total and Directory Analytics
**Steps to reproduce:**
1. Navigate to Analytics page
2. Compare the Total Cost shown in the overview cards ($37.76)
3. Scroll down to Directory Usage Insights section
4. Observe the Total Cost displayed there ($113.29)

**Current behavior:**
- Overview shows Total Cost: $37.76
- Directory Usage Insights shows Total Cost: $113.29
- This is a 3x discrepancy in reported costs

**Expected behavior:**
- Both sections should show the same total cost
- All cost calculations should be consistent across the analytics page

**Fix Applied:**
- Fixed the `_build_directory_tree` method in `analytics.py` to prevent double-counting when aggregating costs up the directory tree
- Changed to only add costs to the deepest node in the path to avoid multiplication

### [x] Issue 2: Message Count Discrepancy
**Steps to reproduce:**
1. Navigate to Analytics page
2. Check Total Messages in overview (357)
3. Check Directory Usage Insights message count (1,071)

**Current behavior:**
- Overview shows 357 total messages
- Directory Usage shows 1,071 total messages
- This is a 3x discrepancy

**Expected behavior:**
- Message counts should be consistent across all analytics sections

### [x] Issue 3: Session Count Shows Zero in Directory Analytics
**Steps to reproduce:**
1. Navigate to Analytics page
2. Note that overview shows 2 total sessions
3. Check Directory Usage Insights section
4. Observe Sessions count showing 0

**Current behavior:**
- Overview correctly shows 2 sessions
- Directory Usage shows 0 unique sessions
- Average cost per session shows $0.00 (incorrect)

**Expected behavior:**
- Directory Usage should show the correct session count (2)
- Average cost per session should be calculated correctly

## Performance Analytics Issues

### [x] Issue 4: No Response Time Data Available
**Steps to reproduce:**
1. Navigate to Analytics page
2. Scroll to Response Time Overview section

**Current behavior:**
- Shows "No response time data available for the selected time range"
- All percentiles show 0ms
- Performance insight still shows "Excellent performance! 90% of responses are under 2 seconds" despite no data

**Expected behavior:**
- Should either show actual response time data if available
- Or hide the performance insight message when no data exists
- Consider showing why no data is available

**Fix Applied:**
- Modified PercentileRibbon component to detect when all percentiles are 0
- Shows "No Data" badge instead of performance label when no data exists
- Updated performance insight to explain that response times will be tracked for new messages
- Note: The durationMs field IS supported in the backend but historical data doesn't include it

### [x] Issue 5: Empty Performance Factors Analysis
**Steps to reproduce:**
1. Navigate to Analytics page
2. Scroll to Performance Factors Analysis section
3. Click on Correlations tab

**Current behavior:**
- Shows empty charts for "Correlation Strength by Factor"
- Shows empty chart for "Impact vs Correlation Strength"
- Detailed Analysis table has headers but no data rows

**Expected behavior:**
- Should show relevant performance factors if data exists
- If no data, should show a meaningful empty state message
- Consider hiding this section if no performance data is available

**Fix Applied:**
- Modified PerformanceFactors component to check for empty correlations array
- Shows clean empty state message instead of empty charts
- Added explanation that performance factors require response time data

## Git Branch Analytics Issues

### [x] Issue 6: Incorrect Branch Classification
**Steps to reproduce:**
1. Navigate to Analytics page
2. Scroll to Git Branch Analytics section
3. Observe branch classification

**Current behavior:**
- All activity is classified as "other" branch type
- Shows 0 main branches despite likely being on main branch
- Main vs Feature Ratio shows 0.0:1

**Expected behavior:**
- Should correctly identify branch names from the git data
- Main branch activity should be classified as "main" not "other"
- Ratios should reflect actual branch usage

**Fix Applied:**
- Modified git branch analytics to include all messages (not just those with gitBranch field)
- Added handling for empty/null branch names to display as "No Branch"
- Updated _detect_branch_type to handle empty branch names gracefully
- Note: The uploaded data doesn't contain git branch information, hence showing "No Branch"

### [x] Issue 7: Branch Lifecycle Timeline Display Issue
**Steps to reproduce:**
1. Navigate to Analytics page
2. Scroll to Branch Lifecycle Timeline section

**Current behavior:**
- Shows empty timeline visualization
- X-axis shows "Days from start" but no actual timeline data
- Average Branch Lifetime shows 1.0 days but no visual representation

**Expected behavior:**
- Should show visual timeline of branch activity
- Timeline should have proper data points and branch indicators
- If no multi-day data, consider different visualization

**Fix Applied:**
- Added `allowDecimals={false}` to the YAxis to prevent fractional tick values
- Note: The visualization appears empty because the data only spans 1 day (all activity on same day)
- The component works correctly when there's multi-day branch activity data

## UI/UX Issues

### [x] Issue 8: Conversation Depth Chart Scaling
**Steps to reproduce:**
1. Navigate to Analytics page
2. Scroll to Session Depth Analysis section
3. Look at Conversation Depth Distribution chart

**Current behavior:**
- Y-axis shows values from 0 to 1 for session counts
- X-axis shows depth values 5 and 14 with no context
- Chart appears to show fractional sessions which doesn't make sense

**Expected behavior:**
- Y-axis should show integer values for session counts
- X-axis should show a clear range of depth values
- Chart should be properly scaled and labeled

**Fix Applied:**
- Added `allowDecimals={false}` to the YAxis component to prevent fractional values
- Added `domain={[0, 'dataMax']}` to ensure proper scaling based on the data

### [x] Issue 9: Activity Heatmap Shows No Data
**Steps to reproduce:**
1. Navigate to Analytics page
2. Look at Activity Heatmap section

**Current behavior:**
- Shows empty grid with hours and days
- No activity data displayed despite having messages
- No indication of why data might be missing

**Expected behavior:**
- Should show activity patterns if data exists
- If timezone conversion issues, should handle gracefully
- Should show meaningful empty state if truly no data

### [x] Issue 10: Model Usage Chart Percentage Display
**Steps to reproduce:**
1. Navigate to Analytics page
2. Look at Model Usage pie chart

**Current behavior:**
- Shows claude-opus-4-20250514 at 74%
- Shows claude-sonnet-4-20250514 at 26%
- But these models don't appear in the uploaded data

**Expected behavior:**
- Should show actual models used in the uploaded sessions
- Percentages should reflect real usage data
- Model names should match what's in the database

## Data Validation Issues

### [x] Issue 11: Cost Calculation Triple Counting
**Steps to reproduce:**
1. Check actual session costs in database
2. Compare with displayed analytics

**Current behavior:**
- Analytics shows costs that appear to be 3x the actual values
- This affects both total cost and directory analytics
- Suggests messages might be counted multiple times

**Expected behavior:**
- Costs should be calculated once per message
- Shared/forked messages should not be double-counted
- Total should match sum of individual session costs

### [x] Issue 12: Directory Structure Not Displayed
**Steps to reproduce:**
1. Navigate to Directory Usage Insights
2. Try to explore directory structure

**Current behavior:**
- Shows only root directory "/"
- Shows "0 subdirectories" despite having project data
- Treemap visualization is empty

**Expected behavior:**
- Should show actual directory structure from messages
- Should allow drilling down into subdirectories
- Treemap should visualize relative costs by directory

**Root Cause:**
- The uploaded data doesn't contain `cwd` (current working directory) information in the messages
- Without cwd data, the analytics service can't build a directory tree
- This is a data limitation, not a code bug - the feature works correctly when cwd data is present

## Recommendations

1. **Implement data validation checks** to ensure consistency across all analytics calculations
2. **Add loading states** for sections that might take time to calculate
3. **Add empty state messages** for sections with no data
4. **Fix the message deduplication** to prevent triple-counting
5. **Implement proper git branch detection** from the session data
6. **Add error boundaries** to prevent one section's error from affecting others
7. **Consider caching** analytics calculations for better performance
8. **Add data refresh indicators** so users know when data was last updated
