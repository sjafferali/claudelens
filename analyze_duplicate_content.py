#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

def compare_duplicate_messages():
    base_path = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/")
    file1 = base_path / "c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl"
    file2 = base_path / "edc4b902-b618-4aea-85f1-09e21cb9e7ce.jsonl"

    # Read all messages into memory
    file1_messages = {}
    file2_messages = {}

    # Read file 1
    with open(file1, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if 'uuid' in data:
                    file1_messages[data['uuid']] = data

    # Read file 2
    with open(file2, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if 'uuid' in data:
                    file2_messages[data['uuid']] = data

    # Find duplicates and compare
    duplicates = set(file1_messages.keys()) & set(file2_messages.keys())

    print(f"=== Duplicate Message Comparison ===")
    print(f"Found {len(duplicates)} duplicate UUIDs\n")

    # Compare first few duplicates
    differences_found = 0
    for i, uuid in enumerate(list(duplicates)[:5]):
        msg1 = file1_messages[uuid]
        msg2 = file2_messages[uuid]

        print(f"\n--- UUID: {uuid} ---")

        # Compare key fields
        fields_to_compare = ['text', 'createdAt', 'updatedAt', 'session.id', 'conversation.id']

        for field in fields_to_compare:
            # Handle nested fields
            if '.' in field:
                parts = field.split('.')
                val1 = msg1
                val2 = msg2
                for part in parts:
                    val1 = val1.get(part, {}) if isinstance(val1, dict) else None
                    val2 = val2.get(part, {}) if isinstance(val2, dict) else None
            else:
                val1 = msg1.get(field)
                val2 = msg2.get(field)

            if val1 != val2:
                differences_found += 1
                print(f"  {field}: DIFFERENT")
                if field == 'text':
                    print(f"    File1: {val1[:100]}..." if val1 and len(val1) > 100 else f"    File1: {val1}")
                    print(f"    File2: {val2[:100]}..." if val2 and len(val2) > 100 else f"    File2: {val2}")
                else:
                    print(f"    File1: {val1}")
                    print(f"    File2: {val2}")
            else:
                print(f"  {field}: Same")

    # Check session IDs
    print(f"\n=== Session Analysis ===")
    file1_sessions = set()
    file2_sessions = set()

    for msg in file1_messages.values():
        if 'session' in msg and 'id' in msg['session']:
            file1_sessions.add(msg['session']['id'])

    for msg in file2_messages.values():
        if 'session' in msg and 'id' in msg['session']:
            file2_sessions.add(msg['session']['id'])

    print(f"File1 sessions: {file1_sessions}")
    print(f"File2 sessions: {file2_sessions}")

    # Check if all file1 messages are in file2
    print(f"\n=== Coverage Check ===")
    print(f"All file1 UUIDs present in file2: {set(file1_messages.keys()).issubset(set(file2_messages.keys()))}")
    print(f"File2 has additional messages: {len(file2_messages) - len(duplicates)}")

if __name__ == "__main__":
    compare_duplicate_messages()
