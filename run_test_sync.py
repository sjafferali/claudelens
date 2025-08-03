#!/usr/bin/env python3
import httpx
import json
from pathlib import Path
import sys
sys.path.append('/Users/sjafferali/github/personal/claudelens/cli')

from claudelens_cli.core.claude_parser import ClaudeMessageParser

print("=== TEST SYNC WITH DEBUG LOGGING ===\n")
print("This will send a single message to test the debug logging.\n")

# Parse one message
jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")
parser = ClaudeMessageParser()

with open(jsonl_file, 'r') as f:
    raw_msg = json.loads(f.readline().strip())
    parsed = parser.parse_jsonl_message(raw_msg)

print(f"Testing with message:")
print(f"  Type: {parsed['type']}")
print(f"  UUID: {parsed['uuid']}")
print(f"  Session: {parsed['sessionId']}")

# Send to API
api_url = "http://c-rat.local.samir.systems:21855/api/v1"
api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

headers = {"X-API-Key": api_key}
client = httpx.Client(base_url=api_url, headers=headers, timeout=30.0)

payload = {"messages": [parsed]}

print(f"\nSending to API...")
response = client.post("/ingest/batch", json=payload)

print(f"\nResponse: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(json.dumps(result, indent=2))

print("\n" + "="*60)
print("IMPORTANT: Check the server logs for debug output!")
print("The logs should show:")
print("  - Message reception and parsing")
print("  - Session creation")
print("  - Content extraction")
print("  - MongoDB operations")
print("  - Any errors that occur")
print("="*60)
