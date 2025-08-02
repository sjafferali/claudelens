#!/usr/bin/env python3
"""Test script for multiple claude_dir support."""

import json
import os
import tempfile
from pathlib import Path
import subprocess
import sys

def create_test_claude_dir(base_dir: Path, name: str) -> Path:
    """Create a test Claude directory structure."""
    claude_dir = base_dir / name
    projects_dir = claude_dir / "projects"

    # Create directory structure
    projects_dir.mkdir(parents=True, exist_ok=True)

    # Create a test project
    project_dir = projects_dir / f"test-project-{name}"
    project_dir.mkdir(exist_ok=True)

    # Create a test JSONL file
    jsonl_file = project_dir / "session1.jsonl"
    test_data = {
        "id": f"msg_{name}_1",
        "content": f"Test message from {name}",
        "role": "user",
        "timestamp": "2024-01-01T00:00:00Z"
    }

    with open(jsonl_file, 'w') as f:
        json.dump(test_data, f)
        f.write('\n')

    print(f"✓ Created test Claude directory: {claude_dir}")
    print(f"  - Project: {project_dir.name}")
    print(f"  - Session file: {jsonl_file.name}")

    return claude_dir

def test_config_commands():
    """Test config commands for multiple directories."""
    print("\n=== Testing Config Commands ===")

    # Show current config
    result = subprocess.run(
        ["claudelens", "config", "show"],
        capture_output=True,
        text=True
    )
    print(f"Current config shown: {result.returncode == 0}")

    # Test setting multiple directories
    test_dirs = "/tmp/claude1,/tmp/claude2,/tmp/claude3"
    result = subprocess.run(
        ["claudelens", "config", "set", "claude_dirs", test_dirs],
        capture_output=True,
        text=True
    )
    print(f"Set multiple dirs via config: {result.returncode == 0}")
    if result.returncode == 0:
        print(f"  Output: {result.stdout.strip()}")

def test_cli_flags():
    """Test CLI flags for multiple directories."""
    print("\n=== Testing CLI Flags ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test directories
        dir1 = create_test_claude_dir(base_dir, "claude1")
        dir2 = create_test_claude_dir(base_dir, "claude2")
        dir3 = create_test_claude_dir(base_dir, "claude3")

        # Test sync with multiple --claude-dir flags
        print("\nTesting sync with multiple --claude-dir flags...")
        cmd = [
            "claudelens", "sync", "--dry-run",
            "--claude-dir", str(dir1),
            "--claude-dir", str(dir2),
            "--claude-dir", str(dir3)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Sync with multiple dirs: {result.returncode == 0}")

        if result.stdout:
            print("\nOutput:")
            print(result.stdout)

        if result.stderr:
            print("\nErrors:")
            print(result.stderr)

def test_env_variables():
    """Test environment variable support."""
    print("\n=== Testing Environment Variables ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test directories
        dir1 = create_test_claude_dir(base_dir, "env1")
        dir2 = create_test_claude_dir(base_dir, "env2")

        # Test with comma-separated CLAUDE_DIR
        env = os.environ.copy()
        env["CLAUDE_DIR"] = f"{dir1},{dir2}"

        result = subprocess.run(
            ["claudelens", "sync", "--dry-run"],
            capture_output=True,
            text=True,
            env=env
        )

        print(f"Sync with CLAUDE_DIR env var: {result.returncode == 0}")

        # Test with CLAUDE_DIRS
        env["CLAUDE_DIRS"] = f"{dir1},{dir2}"
        del env["CLAUDE_DIR"]

        result = subprocess.run(
            ["claudelens", "sync", "--dry-run"],
            capture_output=True,
            text=True,
            env=env
        )

        print(f"Sync with CLAUDE_DIRS env var: {result.returncode == 0}")

def main():
    """Run all tests."""
    print("Testing Multiple Claude Directory Support")
    print("=" * 40)

    # Check if claudelens is available
    result = subprocess.run(
        ["which", "claudelens"],
        capture_output=True
    )

    if result.returncode != 0:
        print("ERROR: claudelens CLI not found in PATH")
        print("Please install the CLI first: pip install -e cli/")
        sys.exit(1)

    # Run tests
    test_config_commands()
    test_cli_flags()
    test_env_variables()

    print("\n✓ All tests completed!")

if __name__ == "__main__":
    main()
