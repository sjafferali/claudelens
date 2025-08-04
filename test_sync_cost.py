#!/usr/bin/env python3
import json
import requests
import asyncio
from datetime import datetime

# Test data from the JSONL file
test_messages = [
    {
        "parentUuid": "2f21b7a8-373e-4697-af74-7f2ad12b0294",
        "isSidechain": False,
        "userType": "external",
        "cwd": "/Users/sjafferali/github/personal/claudehistoryarchive",
        "sessionId": "c2017c7e-c211-419c-a1d8-857a97bccbf6",
        "version": "1.0.65",
        "gitBranch": "",
        "message": {
            "id": "msg_01MXKyVNjccgcJTLJzUW4jYP",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-4-20250514",
            "content": [{"type": "text", "text": "Test message with cost"}],
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {
                "input_tokens": 1,
                "cache_creation_input_tokens": 921,
                "cache_read_input_tokens": 66015,
                "output_tokens": 1,
                "service_tier": "standard"
            }
        },
        "requestId": "req_011CRhUQsVZYPiTwVEUfTvRv",
        "type": "assistant",
        "uuid": "0eddc922-0680-4ac7-8d19-33a82f43821c",
        "timestamp": "2025-08-01T18:36:25.160Z",
        "costUsd": 0.12345  # This is the cost field we're testing
    }
]

async def test_sync():
    # API configuration
    base_url = "http://c-rat.local.samir.systems:21855/api/v1"
    api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    # Prepare batch request
    batch_request = {
        "messages": test_messages,
        "overwrite_mode": True  # Overwrite existing messages
    }

    print("Sending test message with costUsd field...")
    print(f"costUsd value: {test_messages[0]['costUsd']}")

    # Send request
    response = requests.post(
        f"{base_url}/ingest/batch",
        json=batch_request,
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Success! Response: {json.dumps(result, indent=2)}")

        # Now check if the message was stored with costUsd
        import pymongo
        client = pymongo.MongoClient('mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin')
        db = client.claudelens

        # Find the message we just inserted
        message = db.messages.find_one({"uuid": "0eddc922-0680-4ac7-8d19-33a82f43821c"})
        if message:
            print(f"\nMessage in database:")
            print(f"  uuid: {message.get('uuid')}")
            print(f"  costUsd: {message.get('costUsd', 'NOT PRESENT')}")
            if 'costUsd' in message:
                print(f"  costUsd type: {type(message['costUsd'])}")
        else:
            print("\nMessage not found in database!")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    asyncio.run(test_sync())
