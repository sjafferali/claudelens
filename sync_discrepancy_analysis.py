#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

def analyze_sync_discrepancy():
    """Analyze why 333 messages sync but only 265 appear in DB"""

    base_path = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/")
    file1_path = base_path / "c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl"
    file2_path = base_path / "edc4b902-b618-4aea-85f1-09e21cb9e7ce.jsonl"

    print("=== ClaudeLens Sync Discrepancy Analysis ===\n")

    # Read messages from both files
    file1_messages = []
    file2_messages = []

    with open(file1_path, 'r') as f:
        for line in f:
            if line.strip():
                file1_messages.append(json.loads(line))

    with open(file2_path, 'r') as f:
        for line in f:
            if line.strip():
                file2_messages.append(json.loads(line))

    print(f"File 1 ({file1_path.name}):")
    print(f"  - Total messages: {len(file1_messages)}")

    print(f"\nFile 2 ({file2_path.name}):")
    print(f"  - Total messages: {len(file2_messages)}")

    # Extract UUIDs
    file1_uuids = {msg['uuid'] for msg in file1_messages if 'uuid' in msg}
    file2_uuids = {msg['uuid'] for msg in file2_messages if 'uuid' in msg}

    # Analyze overlap
    common_uuids = file1_uuids & file2_uuids
    unique_to_file1 = file1_uuids - file2_uuids
    unique_to_file2 = file2_uuids - file1_uuids

    print(f"\n=== UUID Analysis ===")
    print(f"File 1 unique UUIDs: {len(file1_uuids)}")
    print(f"File 2 unique UUIDs: {len(file2_uuids)}")
    print(f"Common UUIDs: {len(common_uuids)}")
    print(f"UUIDs only in file 1: {len(unique_to_file1)}")
    print(f"UUIDs only in file 2: {len(unique_to_file2)}")
    print(f"Total unique UUIDs across both files: {len(file1_uuids | file2_uuids)}")

    print(f"\n=== Sync Behavior Explanation ===")
    print(f"1. CLI reads all messages from both files:")
    print(f"   - File 1: {len(file1_messages)} messages")
    print(f"   - File 2: {len(file2_messages)} messages")
    print(f"   - Total: {len(file1_messages) + len(file2_messages)} messages")

    print(f"\n2. When using --overwrite mode:")
    print(f"   - Messages with duplicate UUIDs are replaced")
    print(f"   - File 2 is processed after File 1")
    print(f"   - All {len(common_uuids)} messages from File 1 are overwritten by File 2")

    print(f"\n3. Final database state:")
    print(f"   - Unique messages from File 1: {len(unique_to_file1)}")
    print(f"   - All messages from File 2: {len(file2_messages)}")
    print(f"   - Total in DB: {len(unique_to_file1) + len(file2_messages)} messages")

    print(f"\n=== Key Finding ===")
    print(f"The discrepancy occurs because:")
    print(f"- CLI counts every message it reads: {len(file1_messages) + len(file2_messages)} messages")
    print(f"- But {len(common_uuids)} messages from File 1 have the same UUIDs as messages in File 2")
    print(f"- With --overwrite, these duplicates are replaced, not added")
    print(f"- Actual unique messages stored: {len(file1_uuids | file2_uuids)} messages")

    # Verify the math
    expected_db_count = len(file1_uuids | file2_uuids)
    print(f"\n=== Verification ===")
    print(f"Messages CLI reports syncing: {len(file1_messages) + len(file2_messages)}")
    print(f"Expected messages in DB: {expected_db_count}")
    print(f"Actual messages in DB: 265")
    print(f"Match: {'✓' if expected_db_count == 265 else '✗'}")

    # Show session info
    print(f"\n=== Session Information ===")
    sessions = set()
    for msg in file1_messages + file2_messages:
        if 'session' in msg and 'id' in msg['session']:
            sessions.add(msg['session']['id'])

    print(f"Unique sessions found: {len(sessions)}")
    for session_id in sorted(sessions):
        print(f"  - {session_id}")

if __name__ == "__main__":
    analyze_sync_discrepancy()
