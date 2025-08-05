#!/usr/bin/env python3
"""Check what timestamps are available in assistant messages."""

import json
from pathlib import Path
from datetime import datetime

# Sample file to check
file_path = "/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-stashhog-titlethumnails/27232383-1164-4619-8d62-e84d352c380e.jsonl"

print("Analyzing assistant message timestamps...\n")

# Track pairs of user->assistant messages
last_user_msg = None
assistant_samples = []

with open(file_path, 'r') as f:
    for line in f:
        try:
            msg = json.loads(line.strip())

            if msg.get('type') == 'user':
                last_user_msg = msg

            elif msg.get('type') == 'assistant' and last_user_msg:
                # Calculate time difference
                user_time = datetime.fromisoformat(last_user_msg['timestamp'].replace('Z', '+00:00'))
                assistant_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                time_diff = (assistant_time - user_time).total_seconds()

                sample = {
                    'uuid': msg['uuid'],
                    'timestamp': msg['timestamp'],
                    'user_timestamp': last_user_msg['timestamp'],
                    'time_diff_seconds': time_diff,
                    'has_multiple_timestamps': False,
                    'message_fields': list(msg.get('message', {}).keys()) if isinstance(msg.get('message'), dict) else []
                }

                # Check if message has any other timestamp fields
                if isinstance(msg.get('message'), dict):
                    for key in msg['message']:
                        if 'time' in key.lower() or 'stamp' in key.lower():
                            sample['has_multiple_timestamps'] = True
                            sample[f'message.{key}'] = msg['message'][key]

                assistant_samples.append(sample)

                # Show first few examples
                if len(assistant_samples) <= 3:
                    print(f"Sample {len(assistant_samples)}:")
                    print(f"  Assistant UUID: {sample['uuid']}")
                    print(f"  Assistant timestamp: {sample['timestamp']}")
                    print(f"  Previous user timestamp: {sample['user_timestamp']}")
                    print(f"  Time difference: {sample['time_diff_seconds']:.1f} seconds")
                    print(f"  Message fields: {sample['message_fields']}")
                    print()

        except Exception as e:
            continue

# Analyze time differences
time_diffs = [s['time_diff_seconds'] for s in assistant_samples]
if time_diffs:
    print(f"\nTime difference statistics (user->assistant):")
    print(f"  Count: {len(time_diffs)}")
    print(f"  Min: {min(time_diffs):.1f} seconds")
    print(f"  Max: {max(time_diffs):.1f} seconds")
    print(f"  Average: {sum(time_diffs)/len(time_diffs):.1f} seconds")

    # Show distribution
    print(f"\nDistribution:")
    print(f"  < 10 seconds: {sum(1 for t in time_diffs if t < 10)}")
    print(f"  10-60 seconds: {sum(1 for t in time_diffs if 10 <= t < 60)}")
    print(f"  1-5 minutes: {sum(1 for t in time_diffs if 60 <= t < 300)}")
    print(f"  > 5 minutes: {sum(1 for t in time_diffs if t >= 300)}")

print("\nChecking for any special timestamp fields in messages...")
has_special_timestamps = any(s['has_multiple_timestamps'] for s in assistant_samples)
print(f"Found additional timestamp fields: {has_special_timestamps}")
