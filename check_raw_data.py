#!/usr/bin/env python3
"""Check raw Claude data for cost and duration fields."""

import json
from pathlib import Path

# Sample file to check
file_path = "/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-stashhog-titlethumnails/27232383-1164-4619-8d62-e84d352c380e.jsonl"

# Read and analyze messages
assistant_with_cost = 0
assistant_with_duration = 0
assistant_total = 0
user_with_duration = 0
user_total = 0

with open(file_path, 'r') as f:
    for line in f:
        try:
            msg = json.loads(line.strip())

            if msg.get('type') == 'assistant':
                assistant_total += 1
                if 'costUsd' in msg:
                    assistant_with_cost += 1
                if 'durationMs' in msg:
                    assistant_with_duration += 1

                # Show a sample
                if assistant_total == 1:
                    print("Sample assistant message:")
                    print(f"  uuid: {msg.get('uuid')}")
                    print(f"  has costUsd: {'costUsd' in msg}")
                    print(f"  has durationMs: {'durationMs' in msg}")
                    print(f"  has usage: {'usage' in msg.get('message', {})}")
                    if 'usage' in msg.get('message', {}):
                        print(f"  usage: {msg['message']['usage']}")

            elif msg.get('type') == 'user':
                user_total += 1
                if 'toolUseResult' in msg and isinstance(msg['toolUseResult'], dict):
                    if 'durationMs' in msg['toolUseResult']:
                        user_with_duration += 1

        except json.JSONDecodeError:
            continue

print(f"\nSummary:")
print(f"Assistant messages: {assistant_total}")
print(f"  with costUsd: {assistant_with_cost}")
print(f"  with durationMs: {assistant_with_duration}")
print(f"\nUser messages: {user_total}")
print(f"  with toolUseResult.durationMs: {user_with_duration}")
