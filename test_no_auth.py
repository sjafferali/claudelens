#!/usr/bin/env python3
import httpx

# Test if endpoints work without auth
api_url = "http://c-rat.local.samir.systems:21855/api/v1"
client = httpx.Client(base_url=api_url, timeout=10.0)

print("=== Testing Endpoints Without Auth ===\n")

endpoints = [
    ("/projects/", "GET"),
    ("/sessions/", "GET"),
    ("/health", "GET"),
]

for endpoint, method in endpoints:
    try:
        if method == "GET":
            response = client.get(endpoint)
        print(f"{method} {endpoint}: {response.status_code}")
        if response.status_code == 200:
            print(f"  Success - no auth required")
        elif response.status_code == 401:
            print(f"  Auth required: {response.json().get('detail', 'Unknown')}")
    except Exception as e:
        print(f"{method} {endpoint}: Error - {e}")
