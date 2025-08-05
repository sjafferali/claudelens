#!/usr/bin/env python3
"""Test script to verify directory analytics are working correctly."""

import requests
import json

API_URL = "http://localhost:8080/api/v1"


def test_directory_analytics():
    """Test the directory analytics endpoint."""

    print("=== Testing Directory Analytics API ===")

    # Test with different depth levels
    for depth in [1, 2, 3]:
        print(f"\n--- Testing with depth={depth} ---")

        response = requests.get(f"{API_URL}/analytics/directory-usage?time_range=30d&depth={depth}")

        if response.status_code == 200:
            data = response.json()

            print(f"\nAPI Response Summary:")
            print(f"  Total Cost: ${data['total_metrics']['total_cost']}")
            print(f"  Total Messages: {data['total_metrics']['total_messages']}")
            print(f"  Unique Directories: {data['total_metrics']['unique_directories']}")

            print(f"\nRoot Node:")
            root = data['root']
            print(f"  Path: {root['path']}")
            print(f"  Name: {root['name']}")
            print(f"  Cost: ${root['metrics']['cost']}")
            print(f"  Messages: {root['metrics']['messages']}")
            print(f"  Sessions: {root['metrics']['sessions']}")
            print(f"  Children: {len(root.get('children', []))}")

            if root.get('children'):
                print(f"\nTop {min(5, len(root['children']))} directories:")
                for i, child in enumerate(root['children'][:5]):
                    print(f"  {i+1}. {child['name']} ({child['path']})")
                    print(f"     Cost: ${child['metrics']['cost']:.2f}")
                    print(f"     Messages: {child['metrics']['messages']}")
                    print(f"     Sessions: {child['metrics']['sessions']}")
                    print(f"     Percentage: {child['percentage_of_total']:.1f}%")
                    if child.get('children'):
                        print(f"     Subdirectories: {len(child['children'])}")
            else:
                print("\n⚠️  No children found in root directory!")

        else:
            print(f"\n❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")


if __name__ == "__main__":
    test_directory_analytics()
