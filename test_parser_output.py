#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.append('/Users/sjafferali/github/personal/claudelens/cli')

from claudelens_cli.core.claude_parser import ClaudeMessageParser

# Read and parse a message
jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")

parser = ClaudeMessageParser()

print("=== Testing Claude Parser ===\n")

with open(jsonl_file, 'r') as f:
    for i, line in enumerate(f):
        if i >= 3:  # Test first 3 messages
            break

        raw_msg = json.loads(line.strip())
        print(f"Message {i+1} (type: {raw_msg.get('type')}):")

        parsed = parser.parse_jsonl_message(raw_msg)

        if parsed is None:
            print("  Parser returned None (message skipped)")
        else:
            print(f"  Parsed successfully")
            print(f"  Fields in parsed message: {list(parsed.keys())}")

            # Check key fields
            print(f"  - uuid: {parsed.get('uuid')}")
            print(f"  - sessionId: {parsed.get('sessionId')}")
            print(f"  - type: {parsed.get('type')}")
            print(f"  - timestamp: {parsed.get('timestamp')}")
            print(f"  - has 'message' field: {'message' in parsed}")

            # For user messages with toolUseResult
            if parsed.get('type') == 'user' and 'toolUseResult' in parsed:
                print(f"  - toolUseResult type: {type(parsed['toolUseResult'])}")

        print()
