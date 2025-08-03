#!/usr/bin/env python3
import asyncio
import sys
import json
from pathlib import Path
import urllib.parse
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

sys.path.append('/Users/sjafferali/github/personal/claudelens/backend')
sys.path.append('/Users/sjafferali/github/personal/claudelens/cli')

from app.services.ingest_debug import IngestServiceDebug
from app.schemas.ingest import MessageIngest
from claudelens_cli.core.claude_parser import ClaudeMessageParser

async def test_debug_ingest():
    # MongoDB connection
    username = urllib.parse.quote_plus("admin")
    password = urllib.parse.quote_plus("AeSh3sewoodeing3ujatoo3ohphee8oh")
    host = "c-rat.local.samir.systems"
    port = 27017
    uri = f"mongodb://{username}:{password}@{host}:{port}/claudelens?authSource=admin"

    print("=== DEBUG INGEST TEST ===\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    db = client.claudelens

    # Parse a test message
    jsonl_file = Path("/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive/c2017c7e-c211-419c-a1d8-857a97bccbf6.jsonl")
    parser = ClaudeMessageParser()

    # Get first few messages
    messages = []
    with open(jsonl_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 3:  # Get first 3 messages
                break
            raw_msg = json.loads(line.strip())
            parsed = parser.parse_jsonl_message(raw_msg)
            if parsed:
                # Convert to MessageIngest format
                msg_ingest = MessageIngest(
                    uuid=parsed['uuid'],
                    type=parsed['type'],
                    sessionId=parsed['sessionId'],
                    timestamp=parsed['timestamp'],
                    parentUuid=parsed.get('parentUuid'),
                    message=parsed.get('message'),
                    userType=parsed.get('userType'),
                    cwd=parsed.get('cwd'),
                    version=parsed.get('version'),
                    gitBranch=parsed.get('gitBranch'),
                    isSidechain=parsed.get('isSidechain', False),
                    model=parsed.get('model'),
                    requestId=parsed.get('requestId'),
                    toolUseResult=parsed.get('toolUseResult'),
                )
                messages.append(msg_ingest)

    print(f"Parsed {len(messages)} test messages\n")

    # Create debug ingest service
    ingest_service = IngestServiceDebug(db)

    # Clear any existing data for clean test
    session_id = "c2017c7e-c211-419c-a1d8-857a97bccbf6"
    print(f"Clearing existing data for session {session_id}...")
    await db.messages.delete_many({"sessionId": session_id})
    await db.sessions.delete_many({"sessionId": session_id})

    # Run ingestion with debug logging
    print("\n=== RUNNING DEBUG INGESTION ===\n")

    try:
        stats = await ingest_service.ingest_messages(messages)
        print(f"\n=== INGESTION STATS ===")
        print(f"Messages received: {stats.messages_received}")
        print(f"Messages processed: {stats.messages_processed}")
        print(f"Messages failed: {stats.messages_failed}")
        print(f"Messages skipped: {stats.messages_skipped}")
        print(f"Sessions created: {stats.sessions_created}")

    except Exception as e:
        print(f"\nERROR during ingestion: {e}")
        import traceback
        traceback.print_exc()

    # Verify data in database
    print("\n=== VERIFYING DATABASE ===\n")

    # Check session
    session = await db.sessions.find_one({"sessionId": session_id})
    if session:
        print(f"✓ Session found in database!")
        print(f"  Project ID: {session.get('projectId')}")
        print(f"  Message count: {session.get('messageCount', 0)}")
    else:
        print("✗ Session NOT found in database!")

    # Check messages
    message_count = await db.messages.count_documents({"sessionId": session_id})
    print(f"\nMessages in database: {message_count}")

    if message_count > 0:
        # Get first message
        first_msg = await db.messages.find_one({"sessionId": session_id})
        if first_msg:
            print(f"\nFirst message details:")
            print(f"  UUID: {first_msg.get('uuid')}")
            print(f"  Type: {first_msg.get('type')}")
            print(f"  Has content field: {'content' in first_msg}")
            if 'content' in first_msg:
                print(f"  Content preview: {first_msg['content'][:100]}...")

    # Check project
    if session:
        project = await db.projects.find_one({"_id": session.get('projectId')})
        if project:
            print(f"\n✓ Project found!")
            print(f"  Name: {project['name']}")
            print(f"  Path: {project['path']}")

    client.close()
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_debug_ingest())
