#!/usr/bin/env python3
"""Script to add test messages including user messages to the database."""
import asyncio
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import random

async def add_test_data():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://root:example@localhost:27017/")
    db = client.claudelens

    # Create a test project
    project_id = ObjectId()
    project = {
        "_id": project_id,
        "name": "Test Project",
        "path": "/test/project",
        "description": "Test project for user message display",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    await db.projects.insert_one(project)
    print(f"Created project: {project_id}")

    # Create a test session
    session_id = f"test-session-{random.randint(1000, 9999)}"
    session = {
        "_id": ObjectId(),
        "sessionId": session_id,
        "projectId": project_id,
        "summary": "Test conversation with user messages",
        "startedAt": datetime.utcnow() - timedelta(hours=1),
        "endedAt": datetime.utcnow(),
        "messageCount": 6,
        "totalCost": 0.05
    }
    session_obj_id = session["_id"]
    await db.sessions.insert_one(session)
    print(f"Created session: {session_obj_id}")

    # Create messages with alternating types
    messages = []
    base_time = datetime.utcnow() - timedelta(minutes=30)

    # User message 1
    messages.append({
        "_id": ObjectId(),
        "uuid": f"msg-{random.randint(1000, 9999)}-1",
        "type": "user",
        "sessionId": session_id,
        "content": "Hello Claude! Can you help me understand how async/await works in Python?",
        "timestamp": base_time,
        "createdAt": base_time,
        "parentUuid": None
    })

    # Assistant response 1
    messages.append({
        "_id": ObjectId(),
        "uuid": f"msg-{random.randint(1000, 9999)}-2",
        "type": "assistant",
        "sessionId": session_id,
        "content": "I'd be happy to explain async/await in Python! Let me break it down for you:\n\n1. **Asynchronous Programming**: This allows your program to handle multiple operations concurrently without blocking.\n\n2. **async keyword**: Defines an asynchronous function (coroutine)\n3. **await keyword**: Pauses execution until the awaited operation completes\n\nHere's a simple example:\n\n```python\nimport asyncio\n\nasync def fetch_data():\n    print('Starting to fetch data...')\n    await asyncio.sleep(2)  # Simulating an API call\n    return 'Data fetched!'\n\nasync def main():\n    result = await fetch_data()\n    print(result)\n\n# Run the async function\nasyncio.run(main())\n```",
        "timestamp": base_time + timedelta(seconds=30),
        "createdAt": base_time + timedelta(seconds=30),
        "model": "claude-3-opus-20240229",
        "parentUuid": messages[0]["uuid"],
        "usage": {
            "input_tokens": 25,
            "output_tokens": 150
        }
    })

    # User message 2
    messages.append({
        "_id": ObjectId(),
        "uuid": f"msg-{random.randint(1000, 9999)}-3",
        "type": "user",
        "sessionId": session_id,
        "content": "That's helpful! Can you show me how to use async/await with multiple concurrent tasks?",
        "timestamp": base_time + timedelta(minutes=2),
        "createdAt": base_time + timedelta(minutes=2),
        "parentUuid": messages[1]["uuid"]
    })

    # Tool use message
    messages.append({
        "_id": ObjectId(),
        "uuid": f"msg-{random.randint(1000, 9999)}-4",
        "type": "tool_use",
        "sessionId": session_id,
        "content": '{"name": "create_file", "input": {"filename": "async_example.py", "content": "# Example code"}}',
        "timestamp": base_time + timedelta(minutes=3),
        "createdAt": base_time + timedelta(minutes=3),
        "model": "claude-3-opus-20240229",
        "parentUuid": messages[2]["uuid"]
    })

    # Tool result
    messages.append({
        "_id": ObjectId(),
        "uuid": f"msg-{random.randint(1000, 9999)}-5",
        "type": "tool_result",
        "sessionId": session_id,
        "content": "File 'async_example.py' created successfully.",
        "timestamp": base_time + timedelta(minutes=3, seconds=10),
        "createdAt": base_time + timedelta(minutes=3, seconds=10),
        "parentUuid": messages[3]["uuid"]
    })

    # Assistant response 2
    messages.append({
        "_id": ObjectId(),
        "uuid": f"msg-{random.randint(1000, 9999)}-6",
        "type": "assistant",
        "sessionId": session_id,
        "content": "I've created a file with an example. Here's how to run multiple tasks concurrently using asyncio.gather():\n\n```python\nimport asyncio\n\nasync def task1():\n    await asyncio.sleep(2)\n    return 'Task 1 completed'\n\nasync def task2():\n    await asyncio.sleep(1)\n    return 'Task 2 completed'\n\nasync def main():\n    # Run tasks concurrently\n    results = await asyncio.gather(task1(), task2())\n    print(results)\n\nasyncio.run(main())\n```\n\nThis will run both tasks at the same time, taking only 2 seconds total instead of 3!",
        "timestamp": base_time + timedelta(minutes=4),
        "createdAt": base_time + timedelta(minutes=4),
        "model": "claude-3-opus-20240229",
        "parentUuid": messages[4]["uuid"],
        "usage": {
            "input_tokens": 180,
            "output_tokens": 120
        }
    })

    # Insert all messages
    result = await db.messages.insert_many(messages)
    print(f"Inserted {len(result.inserted_ids)} messages")

    print(f"\nTest data created successfully!")
    print(f"Session ID: {session_obj_id}")
    print(f"You can view this session at: http://localhost:5173/sessions/{session_obj_id}")

if __name__ == "__main__":
    asyncio.run(add_test_data())
