#!/usr/bin/env python3
"""Test token analytics implementation."""

import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# MongoDB connection
MONGO_URL = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"

async def test_token_analytics():
    """Test the new token analytics endpoints."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.claudelens

    print("🔍 Testing Token Analytics Implementation\n")

    # 1. Check if messages have token data
    print("1. Checking messages for token data...")
    sample_messages = await db.messages.find(
        {
            "type": "assistant",
            "$or": [
                {"metadata.usage": {"$exists": True}},
                {"inputTokens": {"$exists": True}},
                {"outputTokens": {"$exists": True}},
                {"tokensInput": {"$exists": True}},
                {"tokensOutput": {"$exists": True}},
            ]
        }
    ).limit(5).to_list(None)

    print(f"Found {len(sample_messages)} messages with token data")
    if sample_messages:
        msg = sample_messages[0]
        print(f"\nSample message token fields:")
        if "metadata" in msg and "usage" in msg["metadata"]:
            print(f"  - metadata.usage: {msg['metadata']['usage']}")
        for field in ["inputTokens", "outputTokens", "tokensInput", "tokensOutput"]:
            if field in msg:
                print(f"  - {field}: {msg[field]}")

    # 2. Test token percentile calculation
    print("\n2. Testing token percentile calculation...")

    # Calculate total tokens expression
    total_tokens_expr = {
        "$add": [
            {"$ifNull": ["$inputTokens", 0]},
            {"$ifNull": ["$outputTokens", 0]},
            {"$ifNull": ["$tokensInput", 0]},
            {"$ifNull": ["$tokensOutput", 0]},
            {"$ifNull": ["$metadata.usage.input_tokens", 0]},
            {"$ifNull": ["$metadata.usage.output_tokens", 0]},
            {"$ifNull": ["$metadata.usage.cache_creation_input_tokens", 0]},
            {"$ifNull": ["$metadata.usage.cache_read_input_tokens", 0]},
        ]
    }

    pipeline = [
        {
            "$match": {
                "type": "assistant",
                "$or": [
                    {"metadata.usage": {"$exists": True}},
                    {"inputTokens": {"$exists": True}},
                    {"outputTokens": {"$exists": True}},
                    {"tokensInput": {"$exists": True}},
                    {"tokensOutput": {"$exists": True}},
                ]
            }
        },
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "percentiles": {
                    "$percentile": {
                        "input": total_tokens_expr,
                        "p": [0.5, 0.9, 0.95, 0.99],
                        "method": "approximate"
                    }
                }
            }
        }
    ]

    try:
        result = await db.messages.aggregate(pipeline).to_list(1)
        if result and result[0]["count"] > 0:
            data = result[0]
            print(f"Messages analyzed: {data['count']}")
            print(f"Token percentiles:")
            print(f"  - P50 (median): {data['percentiles'][0]:,.0f} tokens")
            print(f"  - P90: {data['percentiles'][1]:,.0f} tokens")
            print(f"  - P95: {data['percentiles'][2]:,.0f} tokens")
            print(f"  - P99: {data['percentiles'][3]:,.0f} tokens")
        else:
            print("No data available for percentile calculation")
    except Exception as e:
        print(f"Error calculating percentiles: {e}")

    # 3. Test token time series
    print("\n3. Testing token time series aggregation...")

    time_series_pipeline = [
        {
            "$match": {
                "type": "assistant",
                "createdAt": {"$gte": datetime.utcnow() - timedelta(days=30)},
                "$or": [
                    {"metadata.usage": {"$exists": True}},
                    {"inputTokens": {"$exists": True}},
                    {"outputTokens": {"$exists": True}},
                ]
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp"
                    }
                },
                "tokens": {"$push": total_tokens_expr},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": -1}},
        {"$limit": 5}
    ]

    try:
        time_series_result = await db.messages.aggregate(time_series_pipeline).to_list(None)
        if time_series_result:
            print(f"Recent daily token usage:")
            for day in time_series_result:
                tokens = day["tokens"]
                avg_tokens = sum(tokens) / len(tokens) if tokens else 0
                print(f"  - {day['_id']}: {day['count']} messages, avg {avg_tokens:,.0f} tokens")
        else:
            print("No time series data available")
    except Exception as e:
        print(f"Error getting time series: {e}")

    # 4. Test token distribution
    print("\n4. Testing token distribution buckets...")

    distribution_pipeline = [
        {
            "$match": {
                "type": "assistant",
                "$or": [
                    {"metadata.usage": {"$exists": True}},
                    {"inputTokens": {"$exists": True}},
                    {"outputTokens": {"$exists": True}},
                ]
            }
        },
        {"$addFields": {"totalTokens": total_tokens_expr}},
        {
            "$bucket": {
                "groupBy": "$totalTokens",
                "boundaries": [0, 100, 500, 1000, 5000, 10000, 50000, float("inf")],
                "default": "50000+",
                "output": {"count": {"$sum": 1}}
            }
        }
    ]

    try:
        distribution_result = await db.messages.aggregate(distribution_pipeline).to_list(None)
        if distribution_result:
            print("Token usage distribution:")
            bucket_labels = {
                0: "0-100",
                100: "100-500",
                500: "500-1k",
                1000: "1k-5k",
                5000: "5k-10k",
                10000: "10k-50k",
                50000: "50k+",
                "50000+": "50k+"
            }

            total_count = sum(r["count"] for r in distribution_result)
            for bucket in distribution_result:
                label = bucket_labels.get(bucket["_id"], str(bucket["_id"]))
                percentage = (bucket["count"] / total_count * 100) if total_count > 0 else 0
                print(f"  - {label}: {bucket['count']} messages ({percentage:.1f}%)")
        else:
            print("No distribution data available")
    except Exception as e:
        print(f"Error getting distribution: {e}")

    # 5. Test performance factors
    print("\n5. Testing token performance factors...")

    # Message length correlation
    length_correlation_pipeline = [
        {
            "$match": {
                "type": "assistant",
                "$or": [
                    {"metadata.usage": {"$exists": True}},
                    {"inputTokens": {"$exists": True}},
                ]
            }
        },
        {
            "$addFields": {
                "messageLength": {"$strLenCP": {"$toString": "$message"}},
                "totalTokens": total_tokens_expr
            }
        },
        {
            "$group": {
                "_id": None,
                "data": {
                    "$push": {"length": "$messageLength", "tokens": "$totalTokens"}
                },
                "count": {"$sum": 1}
            }
        }
    ]

    try:
        correlation_result = await db.messages.aggregate(length_correlation_pipeline).to_list(1)
        if correlation_result and correlation_result[0]["count"] >= 10:
            data_count = correlation_result[0]["count"]
            print(f"Analyzed {data_count} messages for length/token correlation")

            # Simple correlation insight
            data_points = correlation_result[0]["data"][:10]  # Sample
            avg_length = sum(d["length"] for d in data_points) / len(data_points)
            avg_tokens = sum(d["tokens"] for d in data_points) / len(data_points)
            print(f"  - Average message length: {avg_length:,.0f} characters")
            print(f"  - Average token count: {avg_tokens:,.0f} tokens")
            print(f"  - Tokens per character ratio: {avg_tokens/avg_length:.2f}")
        else:
            print("Not enough data for correlation analysis")
    except Exception as e:
        print(f"Error analyzing correlations: {e}")

    print("\n✅ Token analytics testing complete!")

    client.close()

if __name__ == "__main__":
    asyncio.run(test_token_analytics())
