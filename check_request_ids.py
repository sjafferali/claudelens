#!/usr/bin/env python3
"""Check if requestId can help with timing."""

import json
from datetime import datetime

file_path = "/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-stashhog-titlethumnails/27232383-1164-4619-8d62-e84d352c380e.jsonl"

print("Analyzing requestId patterns...\n")

# Group messages by requestId
request_groups = {}
all_messages = []

with open(file_path, 'r') as f:
    for line in f:
        try:
            msg = json.loads(line.strip())
            all_messages.append(msg)

            req_id = msg.get('requestId')
            if req_id:
                if req_id not in request_groups:
                    request_groups[req_id] = []
                request_groups[req_id].append(msg)
        except:
            continue

print(f"Total messages: {len(all_messages)}")
print(f"Messages with requestId: {sum(1 for m in all_messages if 'requestId' in m)}")
print(f"Unique requestIds: {len(request_groups)}")

# Analyze request groups
print("\n--- Request Group Analysis ---")
for req_id, msgs in list(request_groups.items())[:3]:  # First 3 groups
    print(f"\nRequest ID: {req_id}")
    print(f"Messages in group: {len(msgs)}")

    # Sort by timestamp
    msgs.sort(key=lambda m: m['timestamp'])

    for msg in msgs:
        print(f"  - {msg['type']:10} {msg['timestamp']} {msg['uuid'][:8]}...")

        # Show if it's an assistant message with usage
        if msg['type'] == 'assistant' and 'message' in msg:
            usage = msg['message'].get('usage', {})
            if usage:
                total_tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                print(f"    └─ tokens: {total_tokens} (input: {usage.get('input_tokens', 0)}, output: {usage.get('output_tokens', 0)})")

# Check timing between user input and first assistant with same conversation
print("\n--- Checking actual API response times ---")
# Look for user messages followed by assistant messages
timing_samples = []

for i in range(len(all_messages) - 1):
    curr = all_messages[i]

    # Find next assistant message after a user message
    if curr['type'] == 'user' and 'toolUseResult' not in curr:
        # This is a real user input, not a tool result
        for j in range(i + 1, min(i + 10, len(all_messages))):
            next_msg = all_messages[j]
            if next_msg['type'] == 'assistant':
                # Calculate time difference
                user_time = datetime.fromisoformat(curr['timestamp'].replace('Z', '+00:00'))
                assistant_time = datetime.fromisoformat(next_msg['timestamp'].replace('Z', '+00:00'))
                time_diff = (assistant_time - user_time).total_seconds()

                # Check if they're part of same conversation flow
                same_session = curr.get('sessionId') == next_msg.get('sessionId')

                timing_samples.append({
                    'user_ts': curr['timestamp'],
                    'assistant_ts': next_msg['timestamp'],
                    'time_diff': time_diff,
                    'same_session': same_session,
                    'has_request_id': 'requestId' in next_msg
                })
                break

if timing_samples:
    print(f"\nFound {len(timing_samples)} user→assistant timing samples")

    # Filter for reasonable response times (< 5 minutes)
    reasonable_times = [s for s in timing_samples if s['same_session'] and 0 < s['time_diff'] < 300]

    if reasonable_times:
        times = [s['time_diff'] for s in reasonable_times]
        print(f"\nReasonable response times (same session, <5 min):")
        print(f"  Count: {len(times)}")
        print(f"  Min: {min(times):.1f}s")
        print(f"  Max: {max(times):.1f}s")
        print(f"  Average: {sum(times)/len(times):.1f}s")
        print(f"  Median: {sorted(times)[len(times)//2]:.1f}s")
