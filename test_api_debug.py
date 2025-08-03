#!/usr/bin/env python3
import httpx
import json
from pathlib import Path
import sys
sys.path.append('/Users/sjafferali/github/personal/claudelens/cli')

from claudelens_cli.core.claude_parser import ClaudeMessageParser

# Parse messages
jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")
parser = ClaudeMessageParser()

messages = []
with open(jsonl_file, 'r') as f:
    # Get just the first message for testing
    raw_msg = json.loads(f.readline().strip())
    parsed = parser.parse_jsonl_message(raw_msg)
    if parsed:
        messages.append(parsed)

print("=== TESTING API WITH DEBUG LOGGING ===\n")
print(f"Testing with {len(messages)} message(s)")
print(f"Message type: {messages[0]['type']}")
print(f"Message UUID: {messages[0]['uuid']}")
print(f"Session ID: {messages[0]['sessionId']}")

# Send to API
api_url = "http://c-rat.local.samir.systems:21855/api/v1"
api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

client = httpx.Client(base_url=api_url, headers=headers, timeout=60.0)

# Send messages
payload = {"messages": messages}

print(f"\nSending to API...")
print(f"Payload preview:")
print(json.dumps(messages[0], indent=2, default=str)[:500] + "...")

try:
    response = client.post("/ingest/batch", json=payload)
    print(f"\nResponse status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        stats = result.get("stats", {})
        print(f"\nIngestion stats:")
        print(json.dumps(stats, indent=2))

        if stats.get('messages_failed', 0) > 0:
            print("\n⚠️  MESSAGES FAILED!")
            print("Check server logs for debug output")
    else:
        print(f"\nError response: {response.text[:500]}")

except Exception as e:
    print(f"\nException: {e}")
    import traceback
    traceback.print_exc()

print("\n=== IMPORTANT ===")
print("1. Check the server logs for detailed debug output")
print("2. The debug logging should show exactly where the process fails")
print("3. Look for MongoDB insert errors or schema validation issues")
