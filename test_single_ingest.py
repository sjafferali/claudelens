#!/usr/bin/env python3
import httpx
import json
from pathlib import Path
import sys
sys.path.append('/Users/sjafferali/github/personal/claudelens/cli')

from claudelens_cli.core.claude_parser import ClaudeMessageParser

# Parse a single message
jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")

parser = ClaudeMessageParser()

# Get first message
with open(jsonl_file, 'r') as f:
    raw_msg = json.loads(f.readline().strip())
    parsed_msg = parser.parse_jsonl_message(raw_msg)

print("=== Testing Single Message Ingest ===\n")
print(f"Message type: {parsed_msg['type']}")
print(f"Message UUID: {parsed_msg['uuid']}")
print(f"Session ID: {parsed_msg['sessionId']}")
print(f"Has message field: {'message' in parsed_msg}")

# Send to API
api_url = "http://c-rat.local.samir.systems:21855/api/v1"
api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

client = httpx.Client(base_url=api_url, headers=headers, timeout=30.0)

# Test with a single message
payload = {"messages": [parsed_msg]}

print(f"\nSending message to API...")
print(f"Payload size: {len(json.dumps(payload))} bytes")

try:
    response = client.post("/ingest/batch", json=payload)
    print(f"\nResponse status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        stats = result.get("stats", {})
        print(f"\nIngestion stats:")
        print(f"  Received: {stats.get('messages_received', 0)}")
        print(f"  Processed: {stats.get('messages_processed', 0)}")
        print(f"  Failed: {stats.get('messages_failed', 0)}")
        print(f"  Skipped: {stats.get('messages_skipped', 0)}")
        print(f"  Sessions created: {stats.get('sessions_created', 0)}")

        if stats.get('messages_failed', 0) > 0:
            print("\n⚠️  MESSAGE FAILED TO INGEST!")

            # Check server logs or error details
            print("\nMessage that failed:")
            print(json.dumps(parsed_msg, indent=2, default=str))

    elif response.status_code == 422:
        print("\nValidation error!")
        error_data = response.json()
        print(json.dumps(error_data, indent=2))
    else:
        print(f"\nUnexpected response: {response.text[:500]}")

except Exception as e:
    print(f"\nException: {e}")
    import traceback
    traceback.print_exc()

# Also test the backend directly to see if there's a logging issue
print("\n\n=== Checking if backend code was updated ===")
print("The backend should have the updated ingest.py file that extracts content properly.")
print("If messages are still failing, the update may not have been deployed.")
