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

print("=== Sample Messages ===")
for i, msg in enumerate(messages):
    print(f"\nMessage {i+1}:")
    print(f"  UUID: {msg.get('uuid')}")
    print(f"  Session ID: {msg.get('sessionId')}")
    print(f"  Type: {msg.get('type')}")
    print(f"  Has message field: {'message' in msg}")

# Test sending a single message batch with auth
api_url = "http://c-rat.local.samir.systems:21855/api/v1"
api_key = "ohc3EeG9ieZaingohneechier6jahHuuquoD4eiph2FoogeeDo1ohphoa4Yaec"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

client = httpx.Client(base_url=api_url, headers=headers, timeout=30.0)

print("\n=== Testing Ingest Endpoint with Auth ===")
try:
    # Send first message only
    payload = {"messages": [messages[0]]}
    print(f"\nSending payload with {len(payload['messages'])} message(s)")

    response = client.post("/ingest/batch", json=payload)
    print(f"Response status: {response.status_code}")

    if response.status_code == 422:
        print("Validation error - full response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Response: {response.text[:1000]}")

except Exception as e:
    print(f"Error: {e}")
