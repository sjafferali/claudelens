#!/usr/bin/env python3
import json
from collections import defaultdict
from pathlib import Path

def analyze_jsonl_files():
    base_path = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/")
    file1 = base_path / "c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl"
    file2 = base_path / "edc4b902-b618-4aea-85f1-09e21cb9e7ce.jsonl"

    # Track UUIDs by file
    file1_uuids = set()
    file2_uuids = set()
    uuid_to_files = defaultdict(list)

    # Read file 1
    print(f"Reading {file1.name}...")
    with open(file1, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    data = json.loads(line)
                    if 'uuid' in data:
                        uuid = data['uuid']
                        file1_uuids.add(uuid)
                        uuid_to_files[uuid].append((file1.name, line_num))
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num} in file1: {e}")

    # Read file 2
    print(f"Reading {file2.name}...")
    with open(file2, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    data = json.loads(line)
                    if 'uuid' in data:
                        uuid = data['uuid']
                        file2_uuids.add(uuid)
                        uuid_to_files[uuid].append((file2.name, line_num))
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num} in file2: {e}")

    # Analysis
    print(f"\n=== UUID Analysis ===")
    print(f"File 1 UUIDs: {len(file1_uuids)}")
    print(f"File 2 UUIDs: {len(file2_uuids)}")
    print(f"Total unique UUIDs: {len(uuid_to_files)}")

    # Find duplicates
    duplicates = {uuid: files for uuid, files in uuid_to_files.items() if len(files) > 1}
    print(f"\nDuplicate UUIDs across files: {len(duplicates)}")

    # Check overlap
    overlap = file1_uuids & file2_uuids
    print(f"UUIDs present in both files: {len(overlap)}")

    # Unique to each file
    unique_to_file1 = file1_uuids - file2_uuids
    unique_to_file2 = file2_uuids - file1_uuids
    print(f"UUIDs unique to file 1: {len(unique_to_file1)}")
    print(f"UUIDs unique to file 2: {len(unique_to_file2)}")

    # Expected vs actual
    print(f"\n=== Summary ===")
    print(f"Total messages read: {len(file1_uuids) + len(file2_uuids)} (333)")
    print(f"Unique messages: {len(uuid_to_files)}")
    print(f"Messages lost to duplicates: {len(file1_uuids) + len(file2_uuids) - len(uuid_to_files)}")

    # Show some duplicate examples
    if duplicates:
        print(f"\n=== First 5 Duplicate UUID Examples ===")
        for i, (uuid, files) in enumerate(list(duplicates.items())[:5]):
            print(f"\nUUID: {uuid}")
            for filename, line_num in files:
                print(f"  - {filename}, line {line_num}")

if __name__ == "__main__":
    analyze_jsonl_files()
