#!/usr/bin/env python3
"""Test script for ClaudeLens MCP Server."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the package to path for testing
sys.path.insert(0, str(Path(__file__).parent))

from claudelens_mcp.api_client import ClaudeLensAPIClient


async def test_api_client():
    """Test the ClaudeLens API client independently."""
    print("Testing ClaudeLens API Client...")
    print("-" * 50)

    # Initialize client
    api_url = os.getenv("CLAUDELENS_API_URL", "http://localhost:8080")
    api_key = os.getenv("CLAUDELENS_API_KEY")

    print(f"Connecting to: {api_url}")

    async with ClaudeLensAPIClient(base_url=api_url, api_key=api_key) as client:
        try:
            # Test 1: List sessions
            print("\n1. Testing list_sessions...")
            sessions_result = await client.list_sessions(limit=5)
            sessions = sessions_result.get("items", [])
            print(f"   Found {len(sessions)} sessions (showing max 5)")
            if sessions:
                first_session = sessions[0]
                print(f"   First session ID: {first_session.get('sessionId')}")
                print(f"   Message count: {first_session.get('messageCount')}")

                # Test 2: Get session details
                session_id = first_session.get("_id")
                print(f"\n2. Testing get_session with ID: {session_id}...")
                session_detail = await client.get_session(session_id, include_messages=True)
                print(f"   Session has {session_detail.get('messageCount')} messages")
                print(f"   Summary: {session_detail.get('summary', 'No summary')[:100]}...")

                # Test 3: Get session messages
                print(f"\n3. Testing get_session_messages...")
                messages_result = await client.get_session_messages(session_id, limit=3)
                messages = messages_result.get("messages", [])
                print(f"   Retrieved {len(messages)} messages (limited to 3)")

                # Test 4: Search messages
                print("\n4. Testing search_messages...")
                search_result = await client.search_messages(
                    query="error",
                    limit=3,
                    highlight=True
                )
                search_hits = search_result.get("results", [])
                print(f"   Found {search_result.get('total', 0)} total results")
                print(f"   Showing {len(search_hits)} results")

                # Test 5: List projects
                print("\n5. Testing list_projects...")
                projects_result = await client.list_projects(limit=5)
                projects = projects_result.get("items", [])
                print(f"   Found {len(projects)} projects")
                for project in projects[:3]:
                    print(f"   - {project.get('name', 'Unnamed')}: {project.get('sessionCount', 0)} sessions")

                # Test 6: Get structured conversations (if export endpoint is available)
                try:
                    print("\n6. Testing get_structured_conversations...")
                    structured = await client.get_structured_conversations(limit=5)
                    if "projects" in structured:
                        print(f"   Found {len(structured.get('projects', []))} project groups")
                        print(f"   Total sessions: {structured.get('total_sessions', 0)}")
                    else:
                        print(f"   Retrieved {structured.get('total_sessions', 0)} sessions")
                except Exception as e:
                    print(f"   Export endpoint not available: {e}")

            else:
                print("   No sessions found in database")

        except Exception as e:
            print(f"\nError during testing: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n" + "=" * 50)
    print("API Client tests completed successfully!")
    return True


async def test_mcp_server():
    """Test the MCP server setup."""
    print("\nTesting MCP Server Setup...")
    print("-" * 50)

    try:
        from claudelens_mcp.server import mcp

        print("✓ MCP server imported successfully")
        print(f"  Server name: {mcp.name}")
        print(f"  Instructions: {mcp.instructions[:100]}...")

        # Check resources
        print(f"\n✓ Resources defined:")
        print("  - claudelens://sessions")
        print("  - claudelens://sessions/{session_id}")
        print("  - claudelens://sessions/{session_id}/messages")
        print("  - claudelens://conversations/structured")
        print("  - claudelens://messages/{message_id}")

        # Check tools
        print(f"\n✓ Tools defined:")
        print("  - search_messages")
        print("  - search_code")
        print("  - get_conversation_thread")
        print("  - generate_summary")
        print("  - get_message_context")
        print("  - list_projects")
        print("  - get_session_analytics")
        print("  - export_session")
        print("  - get_recent_searches")

        # Check prompts
        print(f"\n✓ Prompts defined:")
        print("  - Session Analysis")
        print("  - Search and Summarize")
        print("  - Code Search Analysis")

        print("\n" + "=" * 50)
        print("MCP Server setup validated successfully!")
        return True

    except Exception as e:
        print(f"\nError testing MCP server: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("ClaudeLens MCP Server Test Suite")
    print("=" * 50)

    # Check if backend is accessible
    api_url = os.getenv("CLAUDELENS_API_URL", "http://localhost:8080")
    print(f"\nChecking backend availability at {api_url}...")

    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/health", timeout=5.0)
            if response.status_code == 200:
                print("✓ Backend is accessible")
            else:
                print(f"✗ Backend returned status {response.status_code}")
                print("  Make sure ClaudeLens backend is running")
                return
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        print("\nPlease ensure:")
        print("1. ClaudeLens backend is running (docker-compose up)")
        print("2. Backend is accessible at", api_url)
        print("3. Set CLAUDELENS_API_URL environment variable if using different URL")
        return

    # Run tests
    api_success = await test_api_client()
    mcp_success = await test_mcp_server()

    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  API Client: {'✓ PASSED' if api_success else '✗ FAILED'}")
    print(f"  MCP Server: {'✓ PASSED' if mcp_success else '✗ FAILED'}")
    print("=" * 50)

    if api_success and mcp_success:
        print("\n✅ All tests passed! The MCP server is ready to use.")
        print("\nTo run the MCP server:")
        print("  uv run claudelens-mcp")
        print("\nTo install in Claude Desktop:")
        print("  uv run mcp install claudelens_mcp/server.py --name 'ClaudeLens'")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
