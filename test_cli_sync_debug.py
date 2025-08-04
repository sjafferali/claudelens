#!/usr/bin/env python3
import asyncio
import json
from pathlib import Path
from claudelens_cli.core.claude_parser import ClaudeMessageParser

async def test_parsing():
    parser = ClaudeMessageParser()

    # Read a sample message from the JSONL file
    jsonl_path = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")

    with open(jsonl_path, 'r') as f:
        # Find line 59 which has costUsd
        for i, line in enumerate(f, 1):
            if i == 59:
                try:
                    message = json.loads(line.strip())
                    print(f"Line {i} - Type: {message.get('type')}")
                    print(f"Original message has costUsd: {'costUsd' in message}")
                    print(f"costUsd value: {message.get('costUsd')}")

                    # Parse the message
                    parsed = parser.parse_jsonl_message(message)

                    print(f"\nParsed message has costUsd: {'costUsd' in parsed}")
                    if 'costUsd' in parsed:
                        print(f"Parsed costUsd value: {parsed.get('costUsd')}")

                    print(f"\nFull parsed message keys: {list(parsed.keys())}")

                    # Check if the parser is correctly extracting assistant fields
                    if message.get("type") == "assistant":
                        print(f"\nAssistant-specific fields:")
                        print(f"  model: {parsed.get('model')}")
                        print(f"  requestId: {parsed.get('requestId')}")
                        print(f"  durationMs: {parsed.get('durationMs')}")
                        print(f"  costUsd: {parsed.get('costUsd')}")

                    break
                except json.JSONDecodeError:
                    print(f"JSON decode error on line {i}")
                    continue
                except Exception as e:
                    print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_parsing())
