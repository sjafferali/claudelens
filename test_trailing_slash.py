#!/usr/bin/env python3
"""Test script to verify FastAPI handles trailing slashes correctly."""
import requests
import sys

# Test endpoints with and without trailing slashes
test_cases = [
    ("/api/v1/projects", "without trailing slash"),
    ("/api/v1/projects/", "with trailing slash"),
    ("/api/v1/sessions", "without trailing slash"),
    ("/api/v1/sessions/", "with trailing slash"),
    ("/api/v1/messages", "without trailing slash"),
    ("/api/v1/messages/", "with trailing slash"),
    ("/api/v1/analytics/summary", "without trailing slash"),
    ("/api/v1/analytics/summary/", "with trailing slash"),
]

def test_endpoint(base_url, path, description):
    """Test an endpoint and report results."""
    url = base_url + path
    print(f"\nTesting {description}: {url}")

    try:
        # Disable redirects to see what happens
        response = requests.get(url, allow_redirects=False)

        if response.status_code in [301, 302, 303, 307, 308]:
            print(f"  ❌ REDIRECT: {response.status_code} -> {response.headers.get('Location', 'N/A')}")
            return False
        elif response.status_code == 200:
            print(f"  ✅ SUCCESS: {response.status_code} (Direct response)")
            return True
        else:
            print(f"  ⚠️  STATUS: {response.status_code}")
            return True  # Not a redirect, which is what we want

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def main():
    # Check if base URL is provided
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = "http://localhost:8080"

    print(f"Testing trailing slash handling on: {base_url}")
    print("=" * 60)

    success_count = 0
    total_count = len(test_cases)

    for path, description in test_cases:
        if test_endpoint(base_url, path, description):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"Results: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("✅ All tests passed! No unwanted redirects detected.")
    else:
        print("❌ Some tests failed. Check for redirect issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
