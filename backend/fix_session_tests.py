"""Fix all session service tests for hierarchical ownership."""

import re


def fix_session_tests():
    with open("tests/test_services_session_old.py", "r") as f:
        content = f.read()

    # Remove user_id from filter assertions
    content = re.sub(
        r'"user_id":\s*ObjectId\([^)]+\)', '"projectId": {"$in": project_ids}', content
    )

    # Fix get_session tests to use hierarchical chain
    content = re.sub(
        r"mock_db\.sessions\.find_one = AsyncMock\(return_value=([^)]+)\)",
        r"""mock_db.sessions.find_one = AsyncMock(return_value=\1)
        mock_db.projects.find_one = AsyncMock(return_value={
            "_id": ObjectId(),
            "user_id": ObjectId(user_id)
        })""",
        content,
    )

    # Add hierarchical mocks to test methods
    lines = content.split("\n")
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Check if this is a test_list_sessions* or test_get_session* method
        if (
            "async def test_list_sessions" in line
            or "async def test_get_session" in line
        ) and i + 1 < len(lines):
            # Look for the Setup comment
            j = i + 1
            while j < min(i + 10, len(lines)):
                if "# Setup" in lines[j]:
                    new_lines.append(lines[j])
                    j += 1

                    # Check if user_id is defined but hierarchical mocks are missing
                    has_user_id = False
                    has_hierarchical = False
                    for k in range(j, min(j + 10, len(lines))):
                        if "user_id = str(ObjectId())" in lines[k]:
                            has_user_id = True
                        if "mock_db.projects.find" in lines[k]:
                            has_hierarchical = True

                    if has_user_id and not has_hierarchical:
                        # Add user_id line if it exists
                        if j < len(lines) and "user_id = str(ObjectId())" in lines[j]:
                            new_lines.append(lines[j])
                            j += 1

                        # Add hierarchical mocks
                        hierarchical_setup = """        project_id = ObjectId()

        # Mock projects for user
        mock_db.projects.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": project_id}]
        )

"""
                        new_lines.append(hierarchical_setup)

                    # Skip to after we processed
                    i = j
                    break
                else:
                    new_lines.append(lines[j])
                    j += 1
            else:
                i = j
        else:
            i += 1

    content = "\n".join(new_lines)

    # Write back
    with open("tests/test_services_session_old.py", "w") as f:
        f.write(content)

    print("Fixed session service tests")


if __name__ == "__main__":
    fix_session_tests()
