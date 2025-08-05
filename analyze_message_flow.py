#!/usr/bin/env python3
"""Analyze message flow to understand timestamp patterns."""

import json
from datetime import datetime
from collections import defaultdict

file_path = "/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-stashhog-titlethumnails/27232383-1164-4619-8d62-e84d352c380e.jsonl"

print("Analyzing message flow patterns...\n")

# Read all messages
messages = []
with open(file_path, 'r') as f:
    for line in f:
        try:
            msg = json.loads(line.strip())
            messages.append(msg)
        except:
            continue

# Sort by timestamp to see flow
messages.sort(key=lambda m: m['timestamp'])

# Group messages by timestamp
timestamp_groups = defaultdict(list)
for msg in messages:
    timestamp_groups[msg['timestamp']].append(msg)

print(f"Total messages: {len(messages)}")
print(f"Unique timestamps: {len(timestamp_groups)}")
print(f"Messages sharing timestamps: {sum(1 for group in timestamp_groups.values() if len(group) > 1)}")

print("\n--- First 10 message flows ---")
for i, msg in enumerate(messages[:10]):
    msg_type = msg['type']
    ts = msg['timestamp']
    uuid = msg['uuid']

    # Check if it's part of a group
    group_size = len(timestamp_groups[ts])

    prefix = "  " if group_size > 1 else ""
    group_info = f" (group of {group_size})" if group_size > 1 else ""

    print(f"{prefix}{i+1}. {msg_type:10} {ts} {uuid[:8]}...{group_info}")

    # For assistant messages, show if they have tool_use
    if msg_type == 'assistant' and 'message' in msg:
        content = msg['message'].get('content', [])
        for item in content if isinstance(content, list) else []:
            if isinstance(item, dict) and item.get('type') == 'tool_use':
                print(f"{prefix}   └─ has tool_use: {item.get('name', 'unknown')}")

print("\n--- Checking message patterns ---")
# Find patterns where multiple messages share same timestamp
pattern_counts = defaultdict(int)
for ts, group in timestamp_groups.items():
    if len(group) > 1:
        types = tuple(sorted(msg['type'] for msg in group))
        pattern_counts[types] += 1

print("\nTimestamp sharing patterns:")
for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {pattern}: {count} occurrences")

# Check for tool_use followed by tool_result patterns
print("\n--- Looking for tool execution patterns ---")
tool_patterns = []
for i in range(len(messages) - 1):
    curr = messages[i]
    next_msg = messages[i + 1]

    # Check if assistant has tool_use
    if curr['type'] == 'assistant' and 'message' in curr:
        content = curr['message'].get('content', [])
        has_tool_use = any(
            isinstance(item, dict) and item.get('type') == 'tool_use'
            for item in (content if isinstance(content, list) else [])
        )

        if has_tool_use and next_msg['type'] == 'user':
            # Check if next user message has tool result
            if 'toolUseResult' in next_msg:
                time_diff = (
                    datetime.fromisoformat(next_msg['timestamp'].replace('Z', '+00:00')) -
                    datetime.fromisoformat(curr['timestamp'].replace('Z', '+00:00'))
                ).total_seconds()

                tool_patterns.append({
                    'assistant_ts': curr['timestamp'],
                    'user_ts': next_msg['timestamp'],
                    'time_diff': time_diff,
                    'has_duration': 'durationMs' in next_msg.get('toolUseResult', {})
                })

if tool_patterns:
    print(f"\nFound {len(tool_patterns)} tool execution patterns")
    print("First 5 examples:")
    for i, pattern in enumerate(tool_patterns[:5]):
        print(f"  {i+1}. Assistant (tool_use) → User (tool_result)")
        print(f"     Time difference: {pattern['time_diff']:.1f}s")
        print(f"     Tool result has durationMs: {pattern['has_duration']}")
