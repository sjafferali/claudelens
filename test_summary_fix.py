#!/usr/bin/env python3
"""Test script to verify summary ingestion fix."""

import json
import sys
import requests
from pathlib import Path

# Configuration
API_URL = "http://c-rat.local.samir.systems:21855"
API_KEY = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"
SESSION_ID = "ae1b8d41-3852-465c-bf87-5a73b99272b8"
JSONL_FILE = "/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudelens/ae1b8d41-3852-465c-bf87-5a73b99272b8.jsonl"

def load_messages(file_path):
    """Load messages from JSONL file."""
    messages = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                messages.append(json.loads(line))
    return messages

def ingest_messages(messages):
    """Send messages to the ingestion endpoint."""
    url = f"{API_URL}/api/v1/ingest/batch"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    # Prepare the batch request
    batch_request = {
        "messages": messages,
        "overwrite_mode": True  # Update existing messages
    }

    response = requests.post(url, json=batch_request, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def check_session_summary():
    """Check if the session summary is correctly set."""
    url = f"{API_URL}/api/v1/sessions/{SESSION_ID}"
    headers = {"X-API-Key": API_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("summary")
    else:
        print(f"Error fetching session: {response.status_code}")
        return None

def main():
    print("Testing summary ingestion fix...")
    print(f"Session ID: {SESSION_ID}")
    print()

    # Check current summary
    print("Current session summary:")
    current_summary = check_session_summary()
    if current_summary:
        print(f"  {current_summary[:100]}...")
    else:
        print("  No summary found")
    print()

    # Load messages
    print(f"Loading messages from {JSONL_FILE}")
    messages = load_messages(JSONL_FILE)
    print(f"  Found {len(messages)} messages")

    # Find summary message
    summary_msg = None
    for msg in messages:
        if msg.get("type") == "summary":
            summary_msg = msg
            break

    if summary_msg:
        print(f"  Found summary message: {summary_msg.get('summary', 'N/A')}")
    else:
        print("  No summary message found in file")
        sys.exit(1)

    print()
    print("Re-ingesting messages with overwrite_mode=True...")
    result = ingest_messages(messages)

    if result:
        stats = result.get("stats", {})
        print(f"  Messages processed: {stats.get('messages_processed', 0)}")
        print(f"  Messages updated: {stats.get('messages_updated', 0)}")
        print(f"  Messages failed: {stats.get('messages_failed', 0)}")

    print()
    print("Checking updated session summary...")
    new_summary = check_session_summary()
    if new_summary:
        print(f"  {new_summary}")

        if new_summary != current_summary:
            print()
            print("✅ Summary successfully updated!")
        else:
            print()
            print("❌ Summary unchanged")
    else:
        print("  No summary found")

if __name__ == "__main__":
    main()
