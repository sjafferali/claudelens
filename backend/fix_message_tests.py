"""Fix all message service tests for hierarchical ownership model."""

import re


def fix_message_tests():
    # Read the test file
    with open("tests/test_services_message_old.py", "r") as f:
        content = f.read()

    # Fix list message tests that still have user_id in filter
    content = re.sub(r'"user_id": ObjectId\(user_id\),?\s*', "", content)

    # Fix assertions that expect user_id in filters
    content = re.sub(
        r'expected_filter\["user_id"\] = ObjectId\(user_id\)',
        "# user_id removed - hierarchical ownership",
        content,
    )

    # Fix assertions checking for sessionId to use $in
    content = re.sub(
        r'"sessionId": "session-123"(?=.*expected_filter)',
        '"sessionId": {"$in": ["session-123"]}',
        content,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Write the fixed content back
    with open("tests/test_services_message_old.py", "w") as f:
        f.write(content)

    print("Fixed message service tests")


if __name__ == "__main__":
    fix_message_tests()
