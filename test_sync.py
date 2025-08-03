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
    print(f"  Timestamp: {msg.get('timestamp')}")
    print(f"  CWD: {msg.get('cwd')}")

# Test sending a single message batch
api_url = "http://c-rat.local.samir.systems:21855/api/v1"
client = httpx.Client(base_url=api_url, timeout=30.0)

print("\n=== Testing Ingest Endpoint ===")
try:
    # Try without auth first to see error
    response = client.post("/ingest/batch", json={"messages": messages[:1]})
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
