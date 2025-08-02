"""Clean sample data from the database."""
import asyncio
import os

import motor.motor_asyncio


async def clean_sample_data(db_url: str | None = None):
    """Remove sample data from the database."""
    # Use environment variable if no URL provided
    if db_url is None:
        db_url = os.getenv("MONGODB_URL") or "mongodb://admin:changeme-use-strong-password-in-production@localhost:27017/claudelens?authSource=admin"
    
    print(f"Connecting to MongoDB: {db_url}")
    client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
    db = client.claudelens
    
    print("Checking for sample data patterns...")
    
    # Identify sample data patterns
    sample_patterns = {
        "projects": {
            "path": {"$regex": "^/Users/testuser/projects/"}
        },
        "sessions": {
            "metadata.version": "1.0.55"  # Sample data uses this specific version
        }
    }
    
    # Count and remove sample data
    for collection_name, query in sample_patterns.items():
        collection = db[collection_name]
        count = await collection.count_documents(query)
        
        if count > 0:
            print(f"Found {count} sample {collection_name}")
            
            # If sessions, also remove associated messages
            if collection_name == "sessions":
                sessions = await collection.find(query, {"sessionId": 1}).to_list(None)
                session_ids = [s["sessionId"] for s in sessions]
                
                if session_ids:
                    message_count = await db.messages.count_documents({"sessionId": {"$in": session_ids}})
                    print(f"Found {message_count} associated messages")
                    
                    # Remove messages
                    result = await db.messages.delete_many({"sessionId": {"$in": session_ids}})
                    print(f"Removed {result.deleted_count} messages")
            
            # Remove from collection
            result = await collection.delete_many(query)
            print(f"Removed {result.deleted_count} {collection_name}")
    
    # Final statistics
    project_count = await db.projects.count_documents({})
    session_count = await db.sessions.count_documents({})
    message_count = await db.messages.count_documents({})
    
    print("\nDatabase statistics after cleanup:")
    print(f"  Projects: {project_count}")
    print(f"  Sessions: {session_count}")
    print(f"  Messages: {message_count}")
    
    print("\nCleanup completed!")


if __name__ == "__main__":
    # Confirm before running
    print("This script will remove sample data from the database.")
    print("Sample data is identified by:")
    print("  - Projects with path starting with '/Users/testuser/projects/'")
    print("  - Sessions with metadata.version = '1.0.55'")
    print("  - All messages associated with those sessions")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(clean_sample_data())
    else:
        print("Cleanup cancelled.")