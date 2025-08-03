#!/usr/bin/env python3
import httpx
import json

# API endpoint
api_url = "http://c-rat.local.samir.systems:21855/api/v1"

# Test queries
def test_api():
    client = httpx.Client(base_url=api_url)

    print("=== Testing API Endpoints ===\n")

    # Get projects
    print("1. Getting projects:")
    response = client.get("/projects/")
    projects = response.json()
    print(f"   Total projects: {projects['total']}")
    for project in projects['items']:
        print(f"   - {project['name']} (ID: {project['_id']})")
        print(f"     Path: {project['path']}")
        print(f"     Stats: {project.get('stats', {})}")

    # Get sessions (all)
    print("\n2. Getting all sessions:")
    response = client.get("/sessions/")
    sessions = response.json()
    print(f"   Total sessions: {sessions['total']}")

    # Get sessions for each project
    print("\n3. Getting sessions by project:")
    for project in projects['items']:
        response = client.get(f"/sessions/?project_id={project['_id']}")
        sessions = response.json()
        print(f"   Project {project['name']}: {sessions['total']} sessions")

    # Check ingest status
    print("\n4. Checking ingest status:")
    try:
        response = client.get("/ingest/status")
        if response.status_code == 401:
            print("   API key required for ingest status")
        else:
            status = response.json()
            print(f"   Status: {json.dumps(status, indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_api()
