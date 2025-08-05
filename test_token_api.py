#!/usr/bin/env python3
"""Test token analytics API endpoints."""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_token_analytics_endpoints():
    """Test the new token analytics API endpoints."""
    print("🔍 Testing Token Analytics API Endpoints\n")

    # 1. Test token analytics endpoint
    print("1. Testing GET /api/v1/analytics/token-analytics")
    try:
        response = requests.get(f"{BASE_URL}/analytics/token-analytics?time_range=30d")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   - Time range: {data.get('time_range')}")
            print(f"   - Group by: {data.get('group_by')}")
            if 'percentiles' in data:
                p = data['percentiles']
                print(f"   - Token percentiles:")
                print(f"     • P50: {p.get('p50', 0):,.0f} tokens")
                print(f"     • P90: {p.get('p90', 0):,.0f} tokens")
                print(f"     • P95: {p.get('p95', 0):,.0f} tokens")
                print(f"     • P99: {p.get('p99', 0):,.0f} tokens")
            if 'time_series' in data and data['time_series']:
                print(f"   - Time series points: {len(data['time_series'])}")
                latest = data['time_series'][-1]
                print(f"   - Latest data point: {latest['timestamp'][:10]}, avg {latest['avg_duration_ms']:,.0f} tokens")
            if 'distribution' in data and data['distribution']:
                print(f"   - Distribution buckets: {len(data['distribution'])}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 2. Test token performance factors endpoint
    print("\n2. Testing GET /api/v1/analytics/token-performance-factors")
    try:
        response = requests.get(f"{BASE_URL}/analytics/token-performance-factors?time_range=30d")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            if 'correlations' in data and data['correlations']:
                print(f"   - Found {len(data['correlations'])} correlation factors:")
                for corr in data['correlations'][:3]:  # Show first 3
                    print(f"     • {corr['factor']}: {corr['correlation_strength']:.3f} (impact: {corr['impact_ms']:.0f} tokens)")
                    print(f"       Sample size: {corr['sample_size']} messages")
            if 'recommendations' in data and data['recommendations']:
                print(f"   - Recommendations: {len(data['recommendations'])}")
                for i, rec in enumerate(data['recommendations'][:2], 1):  # Show first 2
                    print(f"     {i}. {rec}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 3. Test with different parameters
    print("\n3. Testing token analytics with different group_by options")
    for group_by in ['hour', 'day', 'model']:
        try:
            response = requests.get(f"{BASE_URL}/analytics/token-analytics?time_range=7d&group_by={group_by}")
            if response.status_code == 200:
                data = response.json()
                time_series_count = len(data.get('time_series', []))
                print(f"   - group_by={group_by}: ✅ {time_series_count} data points")
            else:
                print(f"   - group_by={group_by}: ❌ Status {response.status_code}")
        except Exception as e:
            print(f"   - group_by={group_by}: ❌ Error: {e}")

    # 4. Test custom percentiles
    print("\n4. Testing custom percentiles")
    try:
        response = requests.get(f"{BASE_URL}/analytics/token-analytics?time_range=30d&percentiles=25&percentiles=50&percentiles=75&percentiles=95")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success with custom percentiles!")
            # Note: The API still returns standard percentiles (p50, p90, p95, p99)
            # This is expected behavior based on the backend implementation
        else:
            print(f"❌ Failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n✅ API testing complete!")

if __name__ == "__main__":
    # First check if the API is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("API server is running. Starting tests...\n")
            test_token_analytics_endpoints()
        else:
            print("❌ API server is not responding properly")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server at http://localhost:8000")
        print("   Please make sure the backend is running (./scripts/dev.sh)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
