"""Fix all message test methods to work with hierarchical ownership."""

import re


def add_hierarchical_mocks_to_tests():
    with open("tests/test_services_message_old.py", "r") as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Check if this is a test_list_messages* method that needs hierarchical mocks
        if "async def test_list_messages" in line and i + 1 < len(lines):
            # Look for the Setup comment
            j = i + 1
            while j < min(i + 10, len(lines)):
                if "# Setup" in lines[j]:
                    new_lines.append(lines[j])
                    j += 1

                    # Check if hierarchical mocks already exist
                    has_hierarchical = False
                    for k in range(j, min(j + 10, len(lines))):
                        if "mock_db.projects.find" in lines[k]:
                            has_hierarchical = True
                            break

                    if not has_hierarchical:
                        # Add hierarchical mocks after Setup
                        hierarchical_setup = """        user_id = str(ObjectId())
        project_id = ObjectId()

        # Mock projects for user
        mock_db.projects.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": project_id}]
        )

        # Mock sessions for project
        mock_db.sessions.find.return_value.to_list = AsyncMock(
            return_value=[{"sessionId": "session-123"}]
        )

"""
                        new_lines.append(hierarchical_setup)

                    # Skip to after we added the setup
                    i = j
                    continue
                else:
                    new_lines.append(lines[j])
                    j += 1
            i = j
        else:
            i += 1

    # Write back the modified content
    with open("tests/test_services_message_old.py", "w") as f:
        f.writelines(new_lines)


def fix_assertions():
    """Fix assertions that expect user_id in filters."""
    with open("tests/test_services_message_old.py", "r") as f:
        content = f.read()

    # Remove user_id from expected filters
    content = re.sub(r',?\s*"user_id":\s*ObjectId\([^)]+\)', "", content)

    # Fix sessionId filters to use $in when it's the base filter
    # This regex looks for patterns where sessionId is being set to a string in filters
    content = re.sub(
        r'filter_dict\["sessionId"\]\s*=\s*\{"\$in":\s*\[[^\]]+\]\}',
        'filter_dict["sessionId"] = {"$in": session_ids}',
        content,
    )

    # Write back
    with open("tests/test_services_message_old.py", "w") as f:
        f.write(content)

    print("Fixed message test assertions")


if __name__ == "__main__":
    add_hierarchical_mocks_to_tests()
    fix_assertions()
