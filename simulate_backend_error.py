#!/usr/bin/env python3
"""Simulate what the backend is trying to do to identify the error"""
import json
from datetime import datetime
from pathlib import Path

# Read a message
jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")

with open(jsonl_file, 'r') as f:
    raw_msg = json.loads(f.readline().strip())

print("=== Simulating Backend Processing ===\n")

# What the backend receives after parsing
message_data = {
    "uuid": raw_msg["uuid"],
    "type": raw_msg["type"],
    "sessionId": raw_msg["sessionId"],
    "timestamp": raw_msg["timestamp"],
    "parentUuid": raw_msg.get("parentUuid"),
    "message": raw_msg.get("message"),
    "userType": raw_msg.get("userType"),
    "cwd": raw_msg.get("cwd"),
    "version": raw_msg.get("version"),
    "gitBranch": raw_msg.get("gitBranch"),
    "isSidechain": raw_msg.get("isSidechain", False)
}

print("1. Message structure:")
print(f"   Type: {message_data['type']}")
print(f"   Has message field: {'message' in message_data}")
print(f"   Message field type: {type(message_data.get('message'))}")

# The issue is likely here - the backend expects 'content' field
print("\n2. Content extraction issue:")
msg_field = message_data.get("message")
if isinstance(msg_field, dict):
    print(f"   Message is a dict with keys: {list(msg_field.keys())}")
    print(f"   Content type: {type(msg_field.get('content'))}")

# MongoDB document structure issue
print("\n3. Potential MongoDB document issues:")

# The backend might be trying to create a document like this:
doc = {
    "uuid": message_data["uuid"],
    "sessionId": message_data["sessionId"],
    "type": message_data["type"],
    "timestamp": message_data["timestamp"],
    "message": message_data["message"],  # This might be the issue!
}

print(f"   Document size estimate: {len(json.dumps(doc))} bytes")

# The issue is that 'message' field contains a complex object
# But the Message schema in the backend expects a 'content' field with string
print("\n4. Schema mismatch:")
print("   Backend Message schema expects: content (string)")
print("   But ingest is storing: message (dict)")
print("   This causes a validation error when MongoDB tries to return the data")

print("\n5. The fix:")
print("   The backend needs to extract content from message object")
print("   And store it in a 'content' field as a string")
print("   My code fix does this, but it hasn't been deployed")

print("\n⚠️  SOLUTION: The backend code update needs to be deployed!")
print("   File: /backend/app/services/ingest.py")
print("   The _message_to_doc method needs the content extraction logic")
