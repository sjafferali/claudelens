#!/usr/bin/env python3
"""Test cost data ingestion."""
import httpx
import json
from datetime import datetime, timezone

# Configuration
API_URL = "http://c-rat.local.samir.systems:21855"
API_KEY = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

# Test messages with cost data
test_messages = [
    {
        "uuid": "test-cost-msg-1",
        "type": "user",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sessionId": "test-cost-session-1",
        "cwd": "/test/project",
        "message": {"content": "Test message with cost data"},
    },
    {
        "uuid": "test-cost-msg-2",
        "type": "assistant",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sessionId": "test-cost-session-1",
        "parentUuid": "test-cost-msg-1",
        "cwd": "/test/project",
        "message": {"content": "Response with cost data"},
        "model": "claude-3-5-sonnet-20241022",
        "costUsd": 0.05,  # This is the cost data we're testing
        "durationMs": 1500,
        "usage": {
            "inputTokens": 100,
            "outputTokens": 200,
        },
    },
]

# Send the test messages
def test_ingest():
    """Test ingesting messages with cost data."""
    print("Testing cost data ingestion...")

    # Create HTTP client
    client = httpx.Client(
        base_url=API_URL,
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )

    try:
        # Send the batch
        response = client.post(
            "/api/v1/ingest/batch",
            json={"messages": test_messages},
        )

        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Result: {json.dumps(result, indent=2)}")

            # Check if the messages were processed
            if result.get("stats", {}).get("messages_processed", 0) > 0:
                print("\n✓ Messages ingested successfully")

                # Now check if the cost data was saved
                session_response = client.get(
                    f"/api/v1/sessions/?sessionId=test-cost-session-1"
                )

                if session_response.status_code == 200:
                    sessions = session_response.json()
                    if sessions["items"]:
                        session = sessions["items"][0]
                        print(f"\nSession totalCost: {session.get('totalCost', 'N/A')}")

                        # Get messages to check individual costs
                        messages_response = client.get(
                            f"/api/v1/messages/?session_id={session['_id']}"
                        )

                        if messages_response.status_code == 200:
                            messages = messages_response.json()
                            for msg in messages["items"]:
                                if msg["type"] == "assistant":
                                    print(f"Assistant message costUsd: {msg.get('costUsd', 'N/A')}")
                    else:
                        print("No sessions found")
                else:
                    print(f"Failed to get sessions: {session_response.status_code}")
            else:
                print("✗ No messages were processed")
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    test_ingest()
