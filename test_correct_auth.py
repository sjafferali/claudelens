#!/usr/bin/env python3
import httpx
import json
from pathlib import Path

# Read a sample message from the JSONL file
jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")
messages = []

with open(jsonl_file, 'r') as f:
    for i, line in enumerate(f):
        if i >= 3:  # Get first 3 messages
            break
        msg = json.loads(line.strip())
        messages.append(msg)

# Test sending with correct API key
api_url = "http://c-rat.local.samir.systems:21855/api/v1"
api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

client = httpx.Client(base_url=api_url, headers=headers, timeout=30.0)

print("=== Testing Ingest with Correct API Key ===")
try:
    # Send first message only
    payload = {"messages": [messages[0]]}
    print(f"\nSending payload with {len(payload['messages'])} message(s)")
    print(f"First message type: {messages[0].get('type')}")
    print(f"First message has 'message' field: {'message' in messages[0]}")

    response = client.post("/ingest/batch", json=payload)
    print(f"\nResponse status: {response.status_code}")

    if response.status_code == 422:
        print("Validation error - full response:")
        error_data = response.json()
        print(json.dumps(error_data, indent=2))

        # Print first few validation errors in detail
        if "detail" in error_data and isinstance(error_data["detail"], list):
            print("\nDetailed validation errors:")
            for i, error in enumerate(error_data["detail"][:3]):
                print(f"\nError {i+1}:")
                print(f"  Location: {error.get('loc', [])}")
                print(f"  Message: {error.get('msg')}")
                print(f"  Type: {error.get('type')}")
                if 'input' in error:
                    print(f"  Input: {json.dumps(error['input'], indent=2)[:200]}...")
    elif response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text[:1000]}")

except Exception as e:
    print(f"Error: {e}")
