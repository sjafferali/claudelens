#!/usr/bin/env python3
"""Test script to verify the sync fix works correctly"""
import asyncio
import httpx
import json
from pathlib import Path

async def test_sync_fix():
    """Test that the server correctly reports inserted vs updated messages"""

    # Test messages with duplicate UUIDs
    test_messages = [
        {
            "uuid": "test-uuid-1",
            "type": "user",
            "sessionId": "test-session-1",
            "timestamp": "2024-01-01T00:00:00Z",
            "message": {"text": "Test message 1 - version 1"},
            "cwd": "/test/project"
        },
        {
            "uuid": "test-uuid-2",
            "type": "assistant",
            "sessionId": "test-session-1",
            "timestamp": "2024-01-01T00:01:00Z",
            "message": {"text": "Test response 1"},
            "cwd": "/test/project"
        }
    ]

    # First batch - should all be inserted
    print("=== Test 1: Initial sync (should insert 2 messages) ===")
    async with httpx.AsyncClient(base_url="http://c-rat.local.samir.systems:21855") as client:
        response = await client.post(
            "/api/v1/ingest/batch",
            json={"messages": test_messages, "overwrite_mode": True},
            headers={"X-API-Key": "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"},
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            stats = result.get("stats", {})
            print(f"Response: {json.dumps(stats, indent=2)}")
            print(f"Messages processed (inserted): {stats.get('messages_processed', 0)}")
            print(f"Messages updated: {stats.get('messages_updated', 0)}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

    # Second batch - modify one message and add a new one
    print("\n=== Test 2: Sync with 1 duplicate and 1 new message ===")
    test_messages_2 = [
        {
            "uuid": "test-uuid-1",  # Duplicate UUID
            "type": "user",
            "sessionId": "test-session-1",
            "timestamp": "2024-01-01T00:00:00Z",
            "message": {"text": "Test message 1 - version 2 (updated)"},  # Different content
            "cwd": "/test/project"
        },
        {
            "uuid": "test-uuid-3",  # New UUID
            "type": "user",
            "sessionId": "test-session-1",
            "timestamp": "2024-01-01T00:02:00Z",
            "message": {"text": "Test message 3 - new"},
            "cwd": "/test/project"
        }
    ]

    async with httpx.AsyncClient(base_url="http://c-rat.local.samir.systems:21855") as client:
        response = await client.post(
            "/api/v1/ingest/batch",
            json={"messages": test_messages_2, "overwrite_mode": True},
            headers={"X-API-Key": "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"},
            timeout=30.0
        )

        if response.status_code == 200:
            result = response.json()
            stats = result.get("stats", {})
            print(f"Response: {json.dumps(stats, indent=2)}")
            print(f"Messages processed (inserted): {stats.get('messages_processed', 0)}")
            print(f"Messages updated: {stats.get('messages_updated', 0)}")

            # Verify counts
            expected_inserted = 1  # test-uuid-3
            expected_updated = 1   # test-uuid-1

            if stats.get('messages_processed') == expected_inserted and stats.get('messages_updated') == expected_updated:
                print("\n✅ Test PASSED: Correctly counted 1 insert and 1 update")
            else:
                print(f"\n❌ Test FAILED: Expected {expected_inserted} inserts and {expected_updated} updates")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_sync_fix())
