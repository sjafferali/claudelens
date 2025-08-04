#!/bin/bash

# Test cost data ingestion

API_URL="http://c-rat.local.samir.systems:21855"
API_KEY="ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

# Create test messages with cost data
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
SESSION_ID="test-cost-session-$(date +%s)"

cat > /tmp/test_messages.json <<EOF
{
  "messages": [
    {
      "uuid": "test-cost-msg-1",
      "type": "user",
      "timestamp": "$TIMESTAMP",
      "sessionId": "$SESSION_ID",
      "cwd": "/test/project",
      "message": {"content": "Test message with cost data"}
    },
    {
      "uuid": "test-cost-msg-2",
      "type": "assistant",
      "timestamp": "$TIMESTAMP",
      "sessionId": "$SESSION_ID",
      "parentUuid": "test-cost-msg-1",
      "cwd": "/test/project",
      "message": {"content": "Response with cost data"},
      "model": "claude-3-5-sonnet-20241022",
      "costUsd": 0.05,
      "durationMs": 1500,
      "usage": {
        "inputTokens": 100,
        "outputTokens": 200
      }
    }
  ]
}
EOF

echo "Testing cost data ingestion..."
echo "Session ID: $SESSION_ID"

# Send the batch
echo -e "\nSending messages..."
RESPONSE=$(curl -s -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/test_messages.json \
  "$API_URL/api/v1/ingest/batch")

echo "Ingest response:"
echo "$RESPONSE" | jq '.'

# Wait a moment for processing
sleep 2

# Check if session was created with cost data
echo -e "\nChecking session cost..."
SESSION_RESPONSE=$(curl -s \
  -H "X-API-Key: $API_KEY" \
  "$API_URL/api/v1/sessions/?sessionId=$SESSION_ID")

TOTAL_COST=$(echo "$SESSION_RESPONSE" | jq -r '.items[0].totalCost // "N/A"')
echo "Session totalCost: $TOTAL_COST"

# Get session ID for message query
SESSION_DB_ID=$(echo "$SESSION_RESPONSE" | jq -r '.items[0]._id // "N/A"')

if [ "$SESSION_DB_ID" != "N/A" ]; then
  echo -e "\nChecking message costs..."
  MESSAGES_RESPONSE=$(curl -s \
    -H "X-API-Key: $API_KEY" \
    "$API_URL/api/v1/messages/?session_id=$SESSION_DB_ID")

  echo "$MESSAGES_RESPONSE" | jq -r '.items[] | select(.type == "assistant") | {type: .type, costUsd: .costUsd, model: .model}'
fi

# Clean up
rm -f /tmp/test_messages.json
