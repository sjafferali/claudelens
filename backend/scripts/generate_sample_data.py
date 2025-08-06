"""Generate sample Claude conversation data for testing."""

import asyncio
import os
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import motor.motor_asyncio
from bson import Decimal128, ObjectId
from faker import Faker

fake = Faker()

# Sample models for different Claude versions
MODELS = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-opus-4-20250514",
]

# Sample code snippets for conversations
CODE_SAMPLES = [
    (
        "python",
        "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    ),
    ("javascript", "const sum = (arr) => arr.reduce((a, b) => a + b, 0);"),
    (
        "typescript",
        "interface User {\n  id: string;\n  name: string;\n  email: string;\n}",
    ),
    (
        "react",
        "const Button = ({ onClick, children }) => (\n  <button onClick={onClick}>{children}</button>\n);",
    ),
]

# Sample tools that Claude might use
TOOLS = [
    {"name": "Read", "description": "Read file contents"},
    {"name": "Write", "description": "Write to file"},
    {"name": "Edit", "description": "Edit file contents"},
    {"name": "Bash", "description": "Execute bash command"},
    {"name": "Grep", "description": "Search for patterns in files"},
    {"name": "LS", "description": "List directory contents"},
    {"name": "TodoWrite", "description": "Update todo list"},
]


async def generate_sample_data(db_url: str | None = None):
    """Generate sample data for testing."""
    # Use environment variable if no URL provided
    if db_url is None:
        # Check if we should use testcontainer
        if os.getenv("USE_TEST_DB", "").lower() == "true":
            print("Using testcontainer for MongoDB...")

            # First check if URL file exists (from backend process)
            import tempfile

            url_file = os.path.join(
                tempfile.gettempdir(), "claudelens_testcontainer_url.txt"
            )
            if os.path.exists(url_file):
                try:
                    with open(url_file) as f:
                        db_url = f.read().strip()
                    print("Read testcontainer URL from temp file")
                except Exception as e:
                    print(f"Error reading URL file: {e}")

            if not db_url:
                # Fallback to starting a new testcontainer (not ideal)
                import sys

                sys.path.insert(
                    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                from app.core.testcontainers_db import get_testcontainer_mongodb_url

                db_url = get_testcontainer_mongodb_url()
                if not db_url:
                    print("Error: Failed to get testcontainer MongoDB URL")
                    return
        else:
            db_url = (
                os.getenv("TESTCONTAINER_MONGODB_URL")
                or os.getenv("MONGODB_URL")
                or "mongodb://admin:admin123@localhost:27017/claudelens?authSource=admin"
            )

    print(f"Using MongoDB URL: {db_url}")
    client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
    db = client.claudelens

    # Clear existing data
    await db.projects.delete_many({})
    await db.sessions.delete_many({})
    await db.messages.delete_many({})

    # Generate projects
    projects = []
    for _i in range(5):
        project = {
            "_id": ObjectId(),
            "name": fake.word() + "-project",
            "path": f"/Users/testuser/projects/{fake.word()}-project",
            "description": fake.sentence(),
            "createdAt": datetime.now(UTC) - timedelta(days=random.randint(30, 365)),
            "updatedAt": datetime.now(UTC),
        }
        projects.append(project)

    await db.projects.insert_many(projects)

    # Generate sessions and messages
    for project in projects:
        # 5-20 sessions per project
        for _ in range(random.randint(5, 20)):
            session_id = fake.uuid4()
            start_time = datetime.now(UTC) - timedelta(days=random.randint(1, 30))

            session = {
                "_id": ObjectId(),
                "sessionId": session_id,
                "projectId": project["_id"],
                "summary": fake.sentence(),
                "startedAt": start_time,
                "endedAt": start_time + timedelta(hours=random.uniform(0.1, 3)),
                "messageCount": 0,
                "totalCost": Decimal128("0.0"),
                "metadata": {
                    "gitBranch": random.choice(["main", "develop", "feature/test"]),
                    "version": "1.0.55",
                },
            }

            # Generate conversation messages
            messages = []
            parent_uuid = None
            current_time = start_time
            total_cost = Decimal("0.0")

            # 10-50 messages per session
            for msg_idx in range(random.randint(10, 50)):
                msg_uuid = fake.uuid4()
                is_user = msg_idx % 2 == 0

                if is_user:
                    message = {
                        "uuid": msg_uuid,
                        "parentUuid": parent_uuid,
                        "sessionId": session_id,
                        "type": "user",
                        "message": {"role": "user", "content": fake.paragraph()},
                        "timestamp": current_time,
                        "userType": "external",
                        "cwd": project["path"],
                    }
                else:
                    model = random.choice(MODELS)

                    # Generate realistic token counts
                    input_tokens = random.randint(100, 2000)
                    output_tokens = random.randint(50, 1500)

                    # Calculate cost based on model and tokens
                    # Rough pricing estimates per million tokens
                    model_pricing = {
                        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
                        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
                        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
                        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
                    }

                    pricing = model_pricing.get(model, {"input": 3.0, "output": 15.0})
                    cost = (input_tokens * pricing["input"] / 1_000_000) + (
                        output_tokens * pricing["output"] / 1_000_000
                    )
                    total_cost += Decimal(str(cost))

                    # Sometimes include code
                    content = fake.paragraph()
                    if random.random() > 0.7:
                        lang, code = random.choice(CODE_SAMPLES)
                        content = f"{content}\n\n```{lang}\n{code}\n```"

                    message = {
                        "uuid": msg_uuid,
                        "parentUuid": parent_uuid,
                        "sessionId": session_id,
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": content,
                            "model": model,
                        },
                        "timestamp": current_time,
                        "costUsd": cost,
                        "durationMs": random.randint(500, 5000),
                        "model": model,
                        # Add token information
                        "inputTokens": input_tokens,
                        "outputTokens": output_tokens,
                        "tokensInput": input_tokens,  # Alternative field name
                        "tokensOutput": output_tokens,  # Alternative field name
                        "metadata": {
                            "usage": {
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "cache_creation_input_tokens": random.randint(0, 100)
                                if random.random() > 0.8
                                else 0,
                                "cache_read_input_tokens": random.randint(0, 50)
                                if random.random() > 0.9
                                else 0,
                            }
                        },
                    }

                messages.append(message)

                # Occasionally add tool use messages (20% chance)
                if not is_user and random.random() > 0.8:
                    # Add tool_use message
                    tool_use_uuid = fake.uuid4()
                    tool = random.choice(TOOLS)
                    tool_use_message = {
                        "uuid": tool_use_uuid,
                        "parentUuid": parent_uuid,
                        "sessionId": session_id,
                        "type": "tool_use",
                        "content": f'{{"name": "{tool["name"]}", "input": {{"file_path": "/test/file.py"}}}}',
                        "timestamp": current_time + timedelta(seconds=1),
                        "model": model,
                    }
                    messages.append(tool_use_message)

                    # Add tool_result message
                    tool_result_uuid = fake.uuid4()
                    tool_result_message = {
                        "uuid": tool_result_uuid,
                        "parentUuid": tool_use_uuid,
                        "sessionId": session_id,
                        "type": "tool_result",
                        "content": "Tool executed successfully. File contents: ...",
                        "timestamp": current_time + timedelta(seconds=2),
                    }
                    messages.append(tool_result_message)
                    parent_uuid = tool_result_uuid
                    current_time += timedelta(seconds=3)
                else:
                    parent_uuid = msg_uuid
                    current_time += timedelta(seconds=random.randint(5, 60))

            # Calculate total tokens for the session
            total_input_tokens = sum(
                msg.get("inputTokens", 0)
                for msg in messages
                if msg.get("type") == "assistant"
            )
            total_output_tokens = sum(
                msg.get("outputTokens", 0)
                for msg in messages
                if msg.get("type") == "assistant"
            )
            tool_count = len([msg for msg in messages if msg.get("type") == "tool_use"])

            session["messageCount"] = len(messages)
            session["totalCost"] = Decimal128(str(total_cost))
            session["totalTokens"] = total_input_tokens + total_output_tokens
            session["inputTokens"] = total_input_tokens
            session["outputTokens"] = total_output_tokens
            session["toolsUsed"] = tool_count

            await db.sessions.insert_one(session)
            if messages:
                await db.messages.insert_many(messages)

    print("Sample data generated successfully!")

    # Print statistics
    project_count = await db.projects.count_documents({})
    session_count = await db.sessions.count_documents({})
    message_count = await db.messages.count_documents({})

    print(f"Created {project_count} projects")
    print(f"Created {session_count} sessions")
    print(f"Created {message_count} messages")


if __name__ == "__main__":
    asyncio.run(generate_sample_data())
