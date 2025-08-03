#!/usr/bin/env python3
import asyncio
import httpx
import json
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import urllib.parse

async def investigate():
    # MongoDB connection
    username = urllib.parse.quote_plus("admin")
    password = urllib.parse.quote_plus("AeSh3sewoodeing3ujatoo3ohphee8oh")
    host = "c-rat.local.samir.systems"
    port = 27017
    uri = f"mongodb://{username}:{password}@{host}:{port}/claudelens?authSource=admin"

    # API details
    api_url = "http://c-rat.local.samir.systems:21855/api/v1"
    api_key = "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"

    print("=== COMPREHENSIVE SYNC INVESTIGATION ===\n")

    try:
        # 1. Connect to MongoDB
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        db = client.claudelens

        print("1. MongoDB Collections Overview:")
        collections = await db.list_collection_names()
        print(f"   Collections: {collections}")

        # 2. Check Projects
        print("\n2. Projects in Database:")
        projects = await db.projects.find().to_list(None)
        for project in projects:
            print(f"\n   Project: {project['name']}")
            print(f"   ID: {project['_id']}")
            print(f"   Path: {project['path']}")
            print(f"   Stats: {project.get('stats', {})}")
            print(f"   Created: {project.get('createdAt', 'N/A')}")
            print(f"   Updated: {project.get('updatedAt', 'N/A')}")

        # 3. Check Sessions
        print("\n3. Sessions in Database:")
        sessions = await db.sessions.find().to_list(None)
        print(f"   Total sessions: {len(sessions)}")

        if sessions:
            for session in sessions[:5]:
                print(f"\n   Session ID: {session.get('sessionId', 'N/A')}")
                print(f"   Project ID: {session.get('projectId', 'N/A')}")
                print(f"   Message Count: {session.get('messageCount', 0)}")
                print(f"   Started: {session.get('startedAt', 'N/A')}")
                print(f"   Updated: {session.get('updatedAt', 'N/A')}")

        # 4. Check Messages
        print("\n4. Messages in Database:")
        message_count = await db.messages.count_documents({})
        print(f"   Total messages: {message_count}")

        if message_count > 0:
            # Get sample messages
            messages = await db.messages.find().limit(5).to_list(5)
            for msg in messages:
                print(f"\n   Message UUID: {msg.get('uuid', 'N/A')}")
                print(f"   Session ID: {msg.get('sessionId', 'N/A')}")
                print(f"   Type: {msg.get('type', 'N/A')}")
                print(f"   Has content: {'content' in msg}")
                print(f"   Content preview: {str(msg.get('content', ''))[:100]}...")
                print(f"   Timestamp: {msg.get('timestamp', 'N/A')}")

        # 5. Check specific session
        target_session_id = "c2017c7e-c211-419c-a1d8-857a97bccbf6"
        print(f"\n5. Checking for specific session: {target_session_id}")

        specific_session = await db.sessions.find_one({"sessionId": target_session_id})
        if specific_session:
            print("   Session found!")
            print(f"   Project ID: {specific_session.get('projectId')}")
            print(f"   Message Count: {specific_session.get('messageCount', 0)}")
        else:
            print("   Session NOT found!")

        # Check messages for this session
        session_messages = await db.messages.count_documents({"sessionId": target_session_id})
        print(f"   Messages for this session: {session_messages}")

        # 6. Check ingestion logs
        print("\n6. Recent Ingestion Logs:")
        logs = await db.ingestion_logs.find().sort("timestamp", -1).limit(10).to_list(10)
        for i, log in enumerate(logs[:5]):
            print(f"\n   Log {i+1}:")
            print(f"   Timestamp: {log.get('timestamp', 'N/A')}")
            print(f"   Processed: {log.get('messages_processed', 0)}")
            print(f"   Failed: {log.get('messages_failed', 0)}")
            print(f"   Skipped: {log.get('messages_skipped', 0)}")
            print(f"   Duration: {log.get('duration_ms', 0)}ms")

        # 7. Test API endpoints
        print("\n7. Testing API Endpoints:")

        headers = {"X-API-Key": api_key}
        async with httpx.AsyncClient(base_url=api_url, headers=headers) as api_client:
            # Get projects via API
            response = await api_client.get("/projects/")
            if response.status_code == 200:
                api_projects = response.json()
                print(f"\n   API Projects: {api_projects['total']} projects")

                for proj in api_projects['items']:
                    print(f"\n   Project: {proj['name']}")
                    print(f"   ID: {proj['_id']}")
                    print(f"   Stats: {proj.get('stats', {})}")

                    # Get sessions for this project
                    sess_response = await api_client.get(f"/sessions/?project_id={proj['_id']}")
                    if sess_response.status_code == 200:
                        sess_data = sess_response.json()
                        print(f"   Sessions via API: {sess_data['total']}")

            # Get all sessions
            response = await api_client.get("/sessions/")
            if response.status_code == 200:
                all_sessions = response.json()
                print(f"\n   All sessions via API: {all_sessions['total']}")

        # 8. Check for project path mismatch
        print("\n8. Checking for Project Path Issues:")

        # The path from the sync command
        expected_path = "/Users/sjafferali/.claude_personal/projects/-Users-sjafferali-github-personal-claudehistoryarchive"
        print(f"   Expected path: {expected_path}")

        # Check if this exact path exists in projects
        path_match = await db.projects.find_one({"path": expected_path})
        if path_match:
            print(f"   Found project with exact path match!")
            print(f"   Project ID: {path_match['_id']}")

            # Count sessions for this project
            session_count = await db.sessions.count_documents({"projectId": path_match['_id']})
            print(f"   Sessions for this project: {session_count}")
        else:
            print("   No project found with exact path match!")

            # Look for similar paths
            similar_projects = await db.projects.find({"path": {"$regex": "claudehistoryarchive"}}).to_list(None)
            if similar_projects:
                print(f"\n   Found {len(similar_projects)} projects with similar paths:")
                for proj in similar_projects:
                    print(f"   - {proj['path']}")

        # 9. Direct message check
        print("\n9. Checking for Messages with Wrong Project Association:")

        # Get a few messages and check their associations
        sample_messages = await db.messages.find().limit(10).to_list(10)
        if sample_messages:
            print(f"   Checking {len(sample_messages)} sample messages...")

            for msg in sample_messages[:3]:
                session_id = msg.get('sessionId')
                if session_id:
                    session = await db.sessions.find_one({"sessionId": session_id})
                    if session:
                        project_id = session.get('projectId')
                        project = await db.projects.find_one({"_id": project_id})
                        if project:
                            print(f"\n   Message -> Session -> Project:")
                            print(f"   Message: {msg['uuid'][:8]}...")
                            print(f"   Session: {session_id[:8]}...")
                            print(f"   Project: {project['name']} ({project['path']})")
                        else:
                            print(f"\n   WARNING: Session {session_id} has invalid project ID: {project_id}")
                    else:
                        print(f"\n   WARNING: Message has session_id {session_id} but session doesn't exist!")

        client.close()

    except Exception as e:
        print(f"\nError during investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate())
