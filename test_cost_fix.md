# Cost Calculation Fix Summary

## Issue Identified
The discrepancy between the total cost reported in the directory usage insights and the actual session cost was due to incorrect aggregation in the `_update_session_stats` function.

## Root Cause
In `/backend/app/services/ingest.py`, the session cost aggregation was incorrectly adding both `costUsd` and `totalCost` fields:

```javascript
"totalCost": {
    "$sum": {
        "$add": [
            {"$ifNull": ["$costUsd", 0]},
            {"$ifNull": ["$totalCost", 0]},  // This line was causing double-counting
        ]
    }
}
```

Messages should only have a `costUsd` field, not `totalCost`. The `totalCost` field belongs to sessions, not messages.

## Fix Applied
Changed the aggregation to only sum the `costUsd` field:

```javascript
"totalCost": {
    "$sum": {"$ifNull": ["$costUsd", 0]}
}
```

## Impact
1. **Directory Usage Analytics**: Already correctly sums only `costUsd` from messages
2. **Session Total Cost**: Will now be correctly calculated when sessions are updated
3. **Existing Sessions**: Need to run `/backend/scripts/fix_session_costs.py` to recalculate costs

## Testing Steps
1. Start the development environment
2. Run the fix script: `poetry run python scripts/fix_session_costs.py`
3. Compare session costs in the Analytics page with directory usage costs
4. They should now match correctly

## Files Modified
- `/backend/app/services/ingest.py` - Fixed the aggregation pipeline in `_update_session_stats`
