#!/usr/bin/env python3
import httpx
import json
from pathlib import Path
import sys
sys.path.append('/Users/sjafferali/github/personal/claudelens/cli')

from claudelens_cli.core.claude_parser import ClaudeMessageParser

# Read and parse messages
jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")

parser = ClaudeMessageParser()
messages = []

with open(jsonl_file, 'r') as f:
    for i, line in enumerate(f):
        if i >= 3:  # Get first 3 messages
            break
        raw_msg = json.loads(line.strip())
        parsed = parser.parse_jsonl_message(raw_msg)
        if parsed:
            messages.append(parsed)

print(f"=== Parsed {len(messages)} messages ===\n")

# Send via API
api_url = "http://c-rat.local.samir.systems:21855/api/v1"
api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

client = httpx.Client(base_url=api_url, headers=headers, timeout=30.0)

# Send messages one by one to see which fails
for i, msg in enumerate(messages):
    print(f"\n=== Sending message {i+1} (type: {msg['type']}) ===")
    payload = {"messages": [msg]}

    try:
        response = client.post("/ingest/batch", json=payload)
        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            stats = result.get("stats", {})
            print(f"Processed: {stats.get('messages_processed', 0)}")
            print(f"Failed: {stats.get('messages_failed', 0)}")

            if stats.get('messages_failed', 0) > 0:
                print("Message failed!")
                # Print the message that failed
                print("\nMessage content:")
                print(json.dumps(msg, indent=2, default=str))
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")
