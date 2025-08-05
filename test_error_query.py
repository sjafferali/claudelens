from pymongo import MongoClient
from bson import ObjectId

def check_errors():
    # Connect to MongoDB
    client = MongoClient("mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin")
    db = client.claudelens

    # Query messages with errors
    print("=== Checking for error messages ===")

    # Find tool_result messages (which contain errors)
    tool_results = list(db.messages.find({
        "type": "tool_result",
        "toolUseResult": {"$exists": True}
    }).limit(5))

    print(f"\nFound {len(tool_results)} tool_result messages")

    for msg in tool_results:
        print(f"\nMessage ID: {msg.get('_id')}")
        print(f"Session ID: {msg.get('sessionId')}")
        print(f"Type: {msg.get('type')}")
        if 'toolUseResult' in msg:
            result = msg['toolUseResult']
            print(f"Tool result type: {type(result)}")
            if isinstance(result, dict):
                print(f"Tool result keys: {result.keys()}")
                if 'error' in result:
                    print(f"ERROR FOUND: {result['error']}")
                elif 'toolResult' in result:
                    print(f"Tool result content preview: {str(result['toolResult'])[:100]}...")
            else:
                print(f"Tool result preview: {str(result)[:100]}...")
        print("-" * 50)

    # Check for messages with error-like content
    print("\n=== Checking for error patterns in content ===")
    error_messages = list(db.messages.find({
        "$or": [
            {"content": {"$regex": "error", "$options": "i"}},
            {"content": {"$regex": "failed", "$options": "i"}},
            {"content": {"$regex": "exception", "$options": "i"}}
        ],
        "type": {"$in": ["tool_result", "assistant"]}
    }).limit(5))

    print(f"\nFound {len(error_messages)} messages with error patterns")
    for msg in error_messages:
        print(f"\nMessage ID: {msg.get('_id')}")
        print(f"Session ID: {msg.get('sessionId')}")
        print(f"Type: {msg.get('type')}")
        print(f"Content preview: {msg.get('content', '')[:200]}...")
        print("-" * 50)

    client.close()

if __name__ == "__main__":
    check_errors()
