from pymongo import MongoClient
import requests
import json

def check_session_errors():
    # Connect to MongoDB
    client = MongoClient("mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin")
    db = client.claudelens

    # Sessions with known errors from previous analysis
    test_sessions = [
        "00ab2347-080b-4b61-b3aa-870a4ef270e7",  # Has 1 API error
        "087f3e57-4167-42d3-860c-a7a16ae3e326",  # Has 3 API errors
        "156aa89c-6de9-41cc-af45-d291930ee019",  # Has 1 API error
    ]

    api_url = "http://c-rat.local.samir.systems:21855/api/v1/analytics/errors/detailed"
    headers = {"X-API-Key": "ohc3EeG9Ibai5uerieg2ahp7oheeYaec"}

    print("=== CHECKING ERROR DETECTION FOR SPECIFIC SESSIONS ===\n")

    for session_id in test_sessions:
        print(f"\n--- Session: {session_id} ---")

        # Check database directly
        error_count = db.messages.count_documents({
            "sessionId": session_id,
            "content": {"$regex": "API Error:", "$options": "i"}
        })
        print(f"Database: Found {error_count} messages with 'API Error:'")

        # Check all error patterns
        all_error_count = db.messages.count_documents({
            "sessionId": session_id,
            "$or": [
                {"content": {"$regex": "error", "$options": "i"}},
                {"content": {"$regex": "failed", "$options": "i"}},
                {"content": {"$regex": "exception", "$options": "i"}}
            ]
        })
        print(f"Database: Found {all_error_count} messages with any error pattern")

        # Check API response
        try:
            response = requests.get(
                f"{api_url}?time_range=all&session_id={session_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                api_errors = len(data.get('errors', []))
                print(f"API: Returns {api_errors} errors for this session")

                if api_errors == 0 and error_count > 0:
                    print("❌ PROBLEM: Database has errors but API returns none!")

                    # Get the actual error message
                    error_msg = db.messages.find_one({
                        "sessionId": session_id,
                        "content": {"$regex": "API Error:", "$options": "i"}
                    })
                    if error_msg:
                        print(f"Example error timestamp: {error_msg.get('timestamp')}")
                        print(f"Error content preview: {error_msg.get('content', '')[:200]}...")
                elif api_errors > 0:
                    print("✓ API correctly returns errors")
                    print(f"First error: {json.dumps(data['errors'][0], indent=2)}")
            else:
                print(f"API returned status code: {response.status_code}")
        except Exception as e:
            print(f"API request failed: {e}")

    # Also check a session without errors as control
    print("\n\n--- Control Test: Session without errors ---")
    # Find a session without API errors
    sessions_without_errors = db.sessions.find({
        "sessionId": {"$nin": test_sessions}
    }).limit(1)

    for session in sessions_without_errors:
        session_id = session['sessionId']
        print(f"Session: {session_id}")

        error_count = db.messages.count_documents({
            "sessionId": session_id,
            "content": {"$regex": "API Error:", "$options": "i"}
        })
        print(f"Database: Found {error_count} messages with 'API Error:'")

        try:
            response = requests.get(
                f"{api_url}?time_range=all&session_id={session_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                api_errors = len(data.get('errors', []))
                print(f"API: Returns {api_errors} errors for this session")
        except Exception as e:
            print(f"API request failed: {e}")

    client.close()

if __name__ == "__main__":
    check_session_errors()
