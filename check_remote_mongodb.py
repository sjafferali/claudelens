#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import urllib.parse

async def check_mongodb():
    # MongoDB connection with auth
    username = urllib.parse.quote_plus("admin")
    password = urllib.parse.quote_plus("AeSh3sewoodeing3ujatoo3ohphee8oh")
    host = "c-rat.local.samir.systems"
    port = 27017

    # Connection string
    uri = f"mongodb://{username}:{password}@{host}:{port}/claudelens?authSource=admin"

    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        db = client.claudelens

        print("=== MongoDB Direct Query ===\n")

        # Check collections
        collections = await db.list_collection_names()
        print(f"Collections: {collections}\n")

        # Check projects
        print("1. Projects collection:")
        projects = await db.projects.find().to_list(None)
        print(f"   Total projects: {len(projects)}")
        for project in projects:
            print(f"   - {project['name']} (ID: {project['_id']})")
            print(f"     Path: {project['path']}")
            print(f"     Stats: {project.get('stats', {})}")

        # Check sessions
        print("\n2. Sessions collection:")
        sessions = await db.sessions.find().to_list(None)
        print(f"   Total sessions: {len(sessions)}")
        for session in sessions[:5]:  # Show first 5
            print(f"   - Session ID: {session.get('sessionId', 'N/A')}")
            print(f"     Project ID: {session.get('projectId', 'N/A')}")
            print(f"     Message Count: {session.get('messageCount', 0)}")

        # Check messages
        print("\n3. Messages collection:")
        message_count = await db.messages.count_documents({})
        print(f"   Total messages: {message_count}")

        # Sample messages
        if message_count > 0:
            messages = await db.messages.find().limit(5).to_list(5)
            for msg in messages:
                print(f"   - Message UUID: {msg.get('uuid', 'N/A')}")
                print(f"     Session ID: {msg.get('sessionId', 'N/A')}")
                print(f"     Type: {msg.get('type', 'N/A')}")

        # Check ingestion logs
        print("\n4. Ingestion logs:")
        logs = await db.ingestion_logs.find().sort("timestamp", -1).limit(5).to_list(5)
        for log in logs:
            print(f"   - Timestamp: {log.get('timestamp', 'N/A')}")
            print(f"     Messages processed: {log.get('messages_processed', 0)}")
            print(f"     Messages skipped: {log.get('messages_skipped', 0)}")
            print(f"     Messages failed: {log.get('messages_failed', 0)}")
            print(f"     Duration: {log.get('duration_ms', 0)}ms")

    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_mongodb())
