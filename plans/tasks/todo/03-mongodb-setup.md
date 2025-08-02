# Task 03: MongoDB Database Setup

## Status
**Status:** TODO
**Priority:** High
**Estimated Time:** 2 hours

## Purpose
Set up MongoDB database with proper collections, indexes, and validation schemas optimized for Claude conversation data. Create database connection utilities and seed data generation scripts.

## Current State
- No database configuration
- No MongoDB connection code
- No data models defined

## Target State
- MongoDB running in Docker for development
- Database connection utilities implemented
- Collections created with proper indexes
- Validation schemas in place
- Sample data generation script working

## Implementation Details

### 1. Docker Compose for MongoDB

**`docker/docker-compose.dev.yml`:**
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: claudelens_mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: admin123
      MONGO_INITDB_DATABASE: claudelens
    volumes:
      - claudelens_mongodb_data:/data/db
      - ./init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
    command: mongod --auth
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/claudelens --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  mongo-express:
    image: mongo-express:latest
    container_name: claudelens_mongo_express
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: admin
      ME_CONFIG_MONGODB_ADMINPASSWORD: admin123
      ME_CONFIG_MONGODB_URL: mongodb://admin:admin123@mongodb:27017/
      ME_CONFIG_BASICAUTH_USERNAME: admin
      ME_CONFIG_BASICAUTH_PASSWORD: admin123
    depends_on:
      mongodb:
        condition: service_healthy

volumes:
  claudelens_mongodb_data:
    name: claudelens_mongodb_data
```

### 2. MongoDB Initialization Script

**`docker/init-mongo.js`:**
```javascript
// Switch to the claudelens database
db = db.getSiblingDB('claudelens');

// Create application user
db.createUser({
  user: 'claudelens_app',
  pwd: 'claudelens_password',
  roles: [
    {
      role: 'readWrite',
      db: 'claudelens'
    }
  ]
});

// Create collections with validation
db.createCollection('projects', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'path', 'createdAt'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'Project name extracted from path'
        },
        path: {
          bsonType: 'string',
          description: 'Full path to project directory'
        },
        description: {
          bsonType: 'string',
          description: 'Optional project description'
        },
        createdAt: {
          bsonType: 'date'
        },
        updatedAt: {
          bsonType: 'date'
        }
      }
    }
  }
});

db.createCollection('sessions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['sessionId', 'projectId', 'startedAt'],
      properties: {
        sessionId: {
          bsonType: 'string',
          description: 'Unique session identifier from Claude'
        },
        projectId: {
          bsonType: 'objectId',
          description: 'Reference to project'
        },
        summary: {
          bsonType: 'string',
          description: 'AI-generated session summary'
        },
        startedAt: {
          bsonType: 'date'
        },
        endedAt: {
          bsonType: 'date'
        },
        messageCount: {
          bsonType: 'int'
        },
        totalCost: {
          bsonType: 'decimal'
        },
        metadata: {
          bsonType: 'object'
        }
      }
    }
  }
});

// Messages collection - flexible schema for Claude's varying message types
db.createCollection('messages');

// Sync state collection for CLI tool
db.createCollection('sync_state', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['projectPath', 'lastSync'],
      properties: {
        projectPath: {
          bsonType: 'string'
        },
        lastSync: {
          bsonType: 'date'
        },
        lastFile: {
          bsonType: 'string'
        },
        lastLine: {
          bsonType: 'int'
        },
        syncedHashes: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          }
        }
      }
    }
  }
});

// Create indexes
db.projects.createIndex({ path: 1 }, { unique: true });
db.projects.createIndex({ name: 'text' });

db.sessions.createIndex({ sessionId: 1 }, { unique: true });
db.sessions.createIndex({ projectId: 1 });
db.sessions.createIndex({ startedAt: -1 });
db.sessions.createIndex({ summary: 'text' });

db.messages.createIndex({ sessionId: 1, timestamp: 1 });
db.messages.createIndex({ uuid: 1 }, { unique: true });
db.messages.createIndex({ parentUuid: 1 });
db.messages.createIndex({ 'message.content': 'text', 'toolUseResult': 'text' });
db.messages.createIndex({ type: 1 });
db.messages.createIndex({ timestamp: -1 });
db.messages.createIndex({ 'message.model': 1 });
db.messages.createIndex({ costUsd: 1 });

db.sync_state.createIndex({ projectPath: 1 }, { unique: true });

print('Database initialization completed successfully');
```

### 3. Database Connection Module

**`backend/app/core/database.py`:**
```python
"""MongoDB database connection and utilities."""
from typing import Optional
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import errors
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


db = MongoDB()


async def connect_to_mongodb() -> None:
    """Create database connection."""
    try:
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=settings.MAX_CONNECTIONS_COUNT,
            minPoolSize=settings.MIN_CONNECTIONS_COUNT,
        )
        db.database = db.client[settings.DATABASE_NAME]

        # Verify connection
        await db.client.admin.command("ping")
        logger.info("Successfully connected to MongoDB")

    except errors.ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise


async def close_mongodb_connection() -> None:
    """Close database connection."""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if not db.database:
        await connect_to_mongodb()
    return db.database


# Collection accessors
async def get_projects_collection():
    """Get projects collection."""
    database = await get_database()
    return database.projects


async def get_sessions_collection():
    """Get sessions collection."""
    database = await get_database()
    return database.sessions


async def get_messages_collection():
    """Get messages collection."""
    database = await get_database()
    return database.messages


async def get_sync_state_collection():
    """Get sync state collection."""
    database = await get_database()
    return database.sync_state
```

### 4. Configuration Settings

**`backend/app/core/config.py`:**
```python
"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "ClaudeLens"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    MONGODB_URL: str = "mongodb://claudelens_app:claudelens_password@localhost:27017/claudelens?authSource=claudelens"
    DATABASE_NAME: str = "claudelens"
    MAX_CONNECTIONS_COUNT: int = 10
    MIN_CONNECTIONS_COUNT: int = 10

    # API
    API_V1_STR: str = "/api/v1"
    API_KEY: str = "default-api-key"

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis (for caching/rate limiting)
    REDIS_URL: Optional[str] = "redis://localhost:6379"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### 5. Pydantic Models

**`backend/app/models/project.py`:**
```python
"""Project models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class ProjectBase(BaseModel):
    name: str
    path: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectInDB(ProjectBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
```

### 6. Sample Data Generator

**`backend/scripts/generate_sample_data.py`:**
```python
"""Generate sample Claude conversation data for testing."""
import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bson import ObjectId
import motor.motor_asyncio
from faker import Faker

fake = Faker()

# Sample models for different Claude versions
MODELS = [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-opus-4-20250514"
]

# Sample code snippets for conversations
CODE_SAMPLES = [
    ("python", "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"),
    ("javascript", "const sum = (arr) => arr.reduce((a, b) => a + b, 0);"),
    ("typescript", "interface User {\n  id: string;\n  name: string;\n  email: string;\n}"),
    ("react", "const Button = ({ onClick, children }) => (\n  <button onClick={onClick}>{children}</button>\n);"),
]


async def generate_sample_data(db_url: str = "mongodb://localhost:27017/claudelens"):
    """Generate sample data for testing."""
    client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
    db = client.claudelens

    # Clear existing data
    await db.projects.delete_many({})
    await db.sessions.delete_many({})
    await db.messages.delete_many({})

    # Generate projects
    projects = []
    for i in range(5):
        project = {
            "_id": ObjectId(),
            "name": fake.word() + "-project",
            "path": f"/Users/testuser/projects/{fake.word()}-project",
            "description": fake.sentence(),
            "createdAt": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
            "updatedAt": datetime.utcnow()
        }
        projects.append(project)

    await db.projects.insert_many(projects)

    # Generate sessions and messages
    for project in projects:
        # 5-20 sessions per project
        for _ in range(random.randint(5, 20)):
            session_id = fake.uuid4()
            start_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))

            session = {
                "_id": ObjectId(),
                "sessionId": session_id,
                "projectId": project["_id"],
                "summary": fake.sentence(),
                "startedAt": start_time,
                "endedAt": start_time + timedelta(hours=random.uniform(0.1, 3)),
                "messageCount": 0,
                "totalCost": 0.0,
                "metadata": {
                    "gitBranch": random.choice(["main", "develop", "feature/test"]),
                    "version": "1.0.55"
                }
            }

            # Generate conversation messages
            messages = []
            parent_uuid = None
            current_time = start_time
            total_cost = 0.0

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
                        "message": {
                            "role": "user",
                            "content": fake.paragraph()
                        },
                        "timestamp": current_time,
                        "userType": "external",
                        "cwd": project["path"]
                    }
                else:
                    model = random.choice(MODELS)
                    cost = random.uniform(0.001, 0.05)
                    total_cost += cost

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
                            "model": model
                        },
                        "timestamp": current_time,
                        "costUsd": cost,
                        "durationMs": random.randint(500, 5000)
                    }

                messages.append(message)
                parent_uuid = msg_uuid
                current_time += timedelta(seconds=random.randint(5, 60))

            session["messageCount"] = len(messages)
            session["totalCost"] = round(total_cost, 6)

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
```

### 7. Update Development Script

**Update `scripts/dev.sh`:**
```bash
#!/bin/bash
set -e

# ... existing code ...

# Start MongoDB
start_mongodb() {
    echo "Starting MongoDB..."

    if [ "$PERSISTENT_DB" = true ]; then
        docker-compose -f docker/docker-compose.dev.yml up -d mongodb mongo-express

        # Wait for MongoDB to be ready
        echo "Waiting for MongoDB to be ready..."
        until docker exec claudelens_mongodb mongosh --eval "db.adminCommand('ping')" &>/dev/null; do
            sleep 1
        done
        echo "MongoDB is ready!"
    else
        # Use testcontainers (implemented in Python test code)
        echo "Using testcontainers for MongoDB (ephemeral)"
    fi
}

# Load sample data
load_sample_data() {
    echo "Loading sample data..."
    cd backend
    poetry run python scripts/generate_sample_data.py
    cd ..
}

# Main execution
if [ "$BACKEND_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
    start_mongodb

    if [ "$LOAD_SAMPLES" = true ]; then
        load_sample_data
    fi
fi

# ... rest of the script
```

### 8. Test Database Connection

**`backend/tests/test_database.py`:**
```python
"""Test database connections and operations."""
import pytest
from app.core.database import connect_to_mongodb, get_database, close_mongodb_connection


@pytest.mark.asyncio
async def test_mongodb_connection():
    """Test MongoDB connection."""
    await connect_to_mongodb()

    db = await get_database()
    assert db is not None

    # Test ping
    result = await db.client.admin.command("ping")
    assert result["ok"] == 1

    await close_mongodb_connection()


@pytest.mark.asyncio
async def test_collections_exist():
    """Test that required collections exist."""
    await connect_to_mongodb()
    db = await get_database()

    collections = await db.list_collection_names()

    assert "projects" in collections
    assert "sessions" in collections
    assert "messages" in collections
    assert "sync_state" in collections

    await close_mongodb_connection()
```

## Required Technologies
- Docker & Docker Compose
- MongoDB 7.0
- Motor (async MongoDB driver for Python)
- Testcontainers (for testing)

## Success Criteria
- [ ] MongoDB running in Docker container
- [ ] Database initialization script working
- [ ] All collections created with proper validation
- [ ] Indexes created for optimal query performance
- [ ] Database connection module implemented
- [ ] Pydantic models for data validation
- [ ] Sample data generator working
- [ ] Development script updated to manage MongoDB
- [ ] Basic database tests passing

## Notes
- Use MongoDB 7.0 for latest features
- Indexes are crucial for search performance
- Text indexes enable full-text search
- Keep validation flexible for messages collection
- Sample data should represent real Claude conversations
