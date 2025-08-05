from pymongo import MongoClient
from datetime import datetime, timedelta
import json

def analyze_errors():
    # Connect to MongoDB
    client = MongoClient("mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin")
    db = client.claudelens

    print("=== ERROR ANALYSIS REPORT ===\n")

    # 1. Count total messages with error patterns
    error_patterns = [
        {"content": {"$regex": "API Error:", "$options": "i"}},
        {"content": {"$regex": "error", "$options": "i"}},
        {"content": {"$regex": "failed", "$options": "i"}},
        {"content": {"$regex": "exception", "$options": "i"}}
    ]

    error_count_by_pattern = {}
    for pattern in error_patterns:
        count = db.messages.count_documents(pattern)
        pattern_str = str(pattern["content"]["$regex"])
        error_count_by_pattern[pattern_str] = count
        print(f"Messages containing '{pattern_str}': {count}")

    # 2. Find sessions with errors
    print("\n=== SESSIONS WITH ERRORS ===")

    # Get messages with API errors
    api_error_messages = list(db.messages.find({
        "content": {"$regex": "API Error:", "$options": "i"}
    }).limit(10))

    sessions_with_errors = {}
    for msg in api_error_messages:
        session_id = msg.get('sessionId')
        if session_id:
            if session_id not in sessions_with_errors:
                sessions_with_errors[session_id] = {
                    'count': 0,
                    'examples': []
                }
            sessions_with_errors[session_id]['count'] += 1
            if len(sessions_with_errors[session_id]['examples']) < 2:
                sessions_with_errors[session_id]['examples'].append({
                    'timestamp': msg.get('timestamp'),
                    'content_preview': msg.get('content', '')[:100] + '...'
                })

    # Print sessions with error counts
    for session_id, data in sorted(sessions_with_errors.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
        print(f"\nSession ID: {session_id}")
        print(f"Error count: {data['count']}")
        print("Example errors:")
        for ex in data['examples']:
            print(f"  - {ex['timestamp']}: {ex['content_preview']}")

    # 3. Check tool_result messages for errors
    print("\n=== TOOL RESULT ERRORS ===")
    tool_results_with_errors = list(db.messages.find({
        "type": "tool_result",
        "toolUseResult.error": {"$exists": True}
    }).limit(5))

    print(f"Found {len(tool_results_with_errors)} tool_result messages with error field")

    # 4. Sample session analysis
    print("\n=== DETAILED SESSION ANALYSIS ===")

    # Pick a session with errors
    if sessions_with_errors:
        sample_session_id = list(sessions_with_errors.keys())[0]
        print(f"\nAnalyzing session: {sample_session_id}")

        # Count all messages in this session
        total_messages = db.messages.count_documents({"sessionId": sample_session_id})
        print(f"Total messages in session: {total_messages}")

        # Count error messages in this session
        error_messages = db.messages.count_documents({
            "sessionId": sample_session_id,
            "$or": [
                {"content": {"$regex": "error", "$options": "i"}},
                {"content": {"$regex": "failed", "$options": "i"}},
                {"type": "tool_result", "toolUseResult.error": {"$exists": True}}
            ]
        })
        print(f"Messages with error patterns: {error_messages}")

        # Get session details
        session = db.sessions.find_one({"sessionId": sample_session_id})
        if session:
            print(f"Session started: {session.get('startedAt')}")
            print(f"Message count in session doc: {session.get('messageCount')}")

    # 5. Test API endpoint
    print("\n=== API ENDPOINT TEST ===")
    import requests

    api_url = "http://c-rat.local.samir.systems:21855/api/v1/analytics/errors/detailed"
    headers = {"X-API-Key": "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"}

    # Test without session_id (should return all errors)
    print("\nTesting API without session_id filter:")
    try:
        response = requests.get(f"{api_url}?time_range=30d", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Total errors returned: {len(data.get('errors', []))}")
            if data.get('error_summary'):
                print("Error summary:", json.dumps(data['error_summary'], indent=2))
        else:
            print(f"API returned status code: {response.status_code}")
    except Exception as e:
        print(f"API request failed: {e}")

    # Test with a specific session_id
    if sessions_with_errors:
        test_session_id = list(sessions_with_errors.keys())[0]
        print(f"\nTesting API with session_id={test_session_id}:")
        try:
            response = requests.get(
                f"{api_url}?time_range=30d&session_id={test_session_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"Errors returned for session: {len(data.get('errors', []))}")
                if data.get('errors'):
                    print("First error:", json.dumps(data['errors'][0], indent=2))
            else:
                print(f"API returned status code: {response.status_code}")
        except Exception as e:
            print(f"API request failed: {e}")

    client.close()

if __name__ == "__main__":
    analyze_errors()
