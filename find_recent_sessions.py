from pymongo import MongoClient
from datetime import datetime, timedelta

def find_recent_sessions():
    # Connect to MongoDB
    client = MongoClient("mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin")
    db = client.claudelens

    print("=== RECENT SESSIONS WITH ERROR ANALYSIS ===\n")

    # Find recent sessions (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)

    recent_sessions = list(db.sessions.find({
        "startedAt": {"$gte": thirty_days_ago}
    }).sort("startedAt", -1).limit(10))

    for session in recent_sessions:
        session_id = session['sessionId']
        print(f"\nSession: {session_id}")
        print(f"Started: {session.get('startedAt')}")
        print(f"Message count: {session.get('messageCount')}")

        # Check for errors in this session
        error_count = db.messages.count_documents({
            "sessionId": session_id,
            "$or": [
                {"content": {"$regex": "API Error:", "$options": "i"}},
                {"content": {"$regex": "error", "$options": "i"}},
                {"type": "tool_result", "toolUseResult.error": {"$exists": True}}
            ]
        })

        api_error_count = db.messages.count_documents({
            "sessionId": session_id,
            "content": {"$regex": "API Error:", "$options": "i"}
        })

        print(f"Total error patterns found: {error_count}")
        print(f"API errors found: {api_error_count}")

        if api_error_count > 0:
            print("✓ This session has API errors that should be displayed")

    client.close()

if __name__ == "__main__":
    find_recent_sessions()
