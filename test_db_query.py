#!/usr/bin/env python3
"""Test script to query MongoDB directly and investigate message counts."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import requests
from datetime import datetime

async def investigate_messages():
    # MongoDB connection
    mongo_url = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"
    client = AsyncIOMotorClient(mongo_url)
    db = client.claudelens

    print("=== MongoDB Direct Query Results ===\n")

    # 1. Count total messages
    total_messages = await db.messages.count_documents({})
    print(f"Total messages in database: {total_messages}")

    # 2. Count messages by type
    print("\nMessages by type:")
    for msg_type in ["user", "assistant", "summary"]:
        count = await db.messages.count_documents({"type": msg_type})
        print(f"  {msg_type}: {count}")

    # 3. Count unique sessions
    unique_sessions = await db.messages.distinct("sessionId")
    print(f"\nUnique sessions: {len(unique_sessions)}")

    # 4. Check for the specific project
    project_path = "/Users/sjafferali/github/personal/claudehistoryarchive"
    project = await db.projects.find_one({"path": project_path})
    if project:
        print(f"\nProject found: {project['name']} (ID: {project['_id']})")

        # Count sessions for this project
        project_sessions = await db.sessions.count_documents({"projectId": project["_id"]})
        print(f"Sessions for this project: {project_sessions}")

        # Get session IDs for this project
        session_docs = await db.sessions.find({"projectId": project["_id"]}).to_list(None)
        session_ids = [doc["sessionId"] for doc in session_docs]

        # Count messages for these sessions
        project_messages = await db.messages.count_documents({"sessionId": {"$in": session_ids}})
        print(f"Messages for this project: {project_messages}")

    # 5. Check for messages without sessions
    all_message_sessions = await db.messages.distinct("sessionId")
    all_db_sessions = await db.sessions.distinct("sessionId")
    orphan_sessions = set(all_message_sessions) - set(all_db_sessions)
    if orphan_sessions:
        print(f"\nFound {len(orphan_sessions)} sessions with messages but no session record!")
        orphan_count = await db.messages.count_documents({"sessionId": {"$in": list(orphan_sessions)}})
        print(f"Orphan messages: {orphan_count}")

        # Show sample orphan sessions
        print("\nSample orphan sessions:")
        for session_id in list(orphan_sessions)[:5]:
            msg_count = await db.messages.count_documents({"sessionId": session_id})
            first_msg = await db.messages.find_one({"sessionId": session_id})
            print(f"  {session_id}: {msg_count} messages")
            if first_msg:
                print(f"    First message type: {first_msg.get('type')}, timestamp: {first_msg.get('timestamp')}")

    # 6. Check most recent messages
    print("\n=== Most Recent Messages ===")
    recent_messages = await db.messages.find().sort("createdAt", -1).limit(5).to_list(5)
    for msg in recent_messages:
        print(f"  {msg.get('uuid')[:8]}... - {msg.get('type')} - {msg.get('createdAt')}")

    # 7. API comparison
    print("\n=== API Query Results ===")
    api_url = "http://c-rat.local.samir.systems:21855/api/v1"
    api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"
    headers = {"X-API-Key": api_key}

    # Get sessions from API
    try:
        response = requests.get(f"{api_url}/sessions", headers=headers, params={"limit": 1000})
        if response.status_code == 200:
            data = response.json()
            api_sessions = data.get("items", [])
            api_total = data.get("total", 0)
            print(f"Sessions from API: {api_total}")

            # Count messages across all sessions
            total_api_messages = sum(session.get("messageCount", 0) for session in api_sessions)
            print(f"Total message count from session records: {total_api_messages}")
    except Exception as e:
        print(f"Error querying API: {e}")

    client.close()

if __name__ == "__main__":
    asyncio.run(investigate_messages())
