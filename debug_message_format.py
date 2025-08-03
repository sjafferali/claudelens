#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

# Read a sample message from the JSONL file
jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")

print("=== Raw Message from File ===")
with open(jsonl_file, 'r') as f:
    raw_line = f.readline().strip()
    raw_msg = json.loads(raw_line)

print(json.dumps(raw_msg, indent=2))

print("\n=== Required Fields Check ===")
required = ["uuid", "type", "sessionId", "timestamp"]
for field in required:
    value = raw_msg.get(field)
    print(f"{field}: {value} (type: {type(value).__name__})")

print("\n=== Message Field Check ===")
message_field = raw_msg.get("message")
print(f"Has 'message' field: {message_field is not None}")
print(f"Message field type: {type(message_field).__name__}")
if message_field:
    print(f"Message field content preview: {str(message_field)[:100]}...")

# Check timestamp format
print("\n=== Timestamp Validation ===")
timestamp = raw_msg.get("timestamp")
try:
    # Try parsing it
    if timestamp.endswith("Z"):
        timestamp_fixed = timestamp[:-1] + "+00:00"
        dt = datetime.fromisoformat(timestamp_fixed)
        print(f"Timestamp parsed successfully: {dt}")
    else:
        dt = datetime.fromisoformat(timestamp)
        print(f"Timestamp parsed successfully: {dt}")
except Exception as e:
    print(f"Timestamp parsing error: {e}")
