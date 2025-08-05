#!/usr/bin/env python3
"""Test optimized MongoDB queries to measure performance improvements."""

import asyncio
import time
import json
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import sys

# MongoDB connection string
MONGO_URI = "mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin"

async def time_query(name: str, collection, pipeline_or_filter, is_aggregate=True):
    """Time a MongoDB query and return execution stats."""
    start_time = time.time()

    try:
        if is_aggregate:
            cursor = collection.aggregate(pipeline_or_filter)
            results = await cursor.to_list(None)
        else:
            cursor = collection.find(pipeline_or_filter)
            results = await cursor.to_list(None)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n{'='*60}")
        print(f"Query: {name}")
        print(f"Duration: {duration:.3f} seconds")
        print(f"Result count: {len(results)}")

        return duration, len(results)
    except Exception as e:
        print(f"\nError in {name}: {e}")
        return None, 0

async def main():
    """Test optimized analytics queries."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.claudelens

    # Collections
    messages_collection = db.messages
    sessions_collection = db.sessions

    # Time range for queries (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    print(f"Testing OPTIMIZED analytics queries")
    print(f"Time range: {start_date} to {end_date}")
    print(f"Database: {db.name}")

    # Test 1: OPTIMIZED Analytics Summary using $facet
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {
            "$facet": {
                # Count messages and calculate cost
                "messageCostStats": [
                    {
                        "$group": {
                            "_id": None,
                            "count": {"$sum": 1},
                            "totalCost": {"$sum": "$cost"},
                            "inputCost": {"$sum": "$inputCost"},
                            "outputCost": {"$sum": "$outputCost"},
                            "totalTokens": {"$sum": "$totalTokens"},
                            "inputTokens": {"$sum": "$inputTokens"},
                            "outputTokens": {"$sum": "$outputTokens"}
                        }
                    }
                ],
                # Count unique sessions
                "sessionStats": [
                    {"$group": {"_id": "$sessionId"}},
                    {"$count": "count"}
                ],
                # Most used model
                "modelStats": [
                    {"$match": {"model": {"$exists": True}}},
                    {"$group": {"_id": "$model", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 1}
                ]
            }
        }
    ]
    await time_query("OPTIMIZED Analytics Summary (Combined with $facet)", messages_collection, pipeline)

    # Test 2: OPTIMIZED Response Time Percentiles using $percentile
    pipeline = [
        {"$match": {
            "createdAt": {"$gte": start_date, "$lte": end_date},
            "responseTime": {"$exists": True, "$ne": None}
        }},
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "avgResponseTime": {"$avg": "$responseTime"},
                "minResponseTime": {"$min": "$responseTime"},
                "maxResponseTime": {"$max": "$responseTime"},
                "percentiles": {
                    "$percentile": {
                        "input": "$responseTime",
                        "p": [0.5, 0.9, 0.95, 0.99],
                        "method": "approximate"
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "count": 1,
                "avgResponseTime": 1,
                "minResponseTime": 1,
                "maxResponseTime": 1,
                "p50": {"$arrayElemAt": ["$percentiles", 0]},
                "p90": {"$arrayElemAt": ["$percentiles", 1]},
                "p95": {"$arrayElemAt": ["$percentiles", 2]},
                "p99": {"$arrayElemAt": ["$percentiles", 3]}
            }
        }
    ]
    await time_query("OPTIMIZED Response Times (Using $percentile)", messages_collection, pipeline)

    # Test 3: OPTIMIZED Directory Usage without collecting arrays
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {
            "$facet": {
                # Main metrics
                "metrics": [
                    {"$group": {
                        "_id": "$directory",
                        "messageCount": {"$sum": 1},
                        "totalCost": {"$sum": "$cost"},
                        "totalTokens": {"$sum": "$totalTokens"},
                        "avgResponseTime": {"$avg": "$responseTime"},
                        "toolCallCount": {
                            "$sum": {
                                "$cond": [
                                    {"$and": [
                                        {"$ne": ["$toolCalls", None]},
                                        {"$gt": [{"$size": {"$ifNull": ["$toolCalls", []]}}, 0]}
                                    ]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }}
                ],
                # Count unique sessions per directory
                "sessionCounts": [
                    {"$group": {
                        "_id": {"directory": "$directory", "session": "$sessionId"}
                    }},
                    {"$group": {
                        "_id": "$_id.directory",
                        "sessionCount": {"$sum": 1}
                    }}
                ],
                # Count unique models per directory
                "modelCounts": [
                    {"$group": {
                        "_id": {"directory": "$directory", "model": "$model"}
                    }},
                    {"$group": {
                        "_id": "$_id.directory",
                        "modelCount": {"$sum": 1}
                    }}
                ]
            }
        }
    ]
    await time_query("OPTIMIZED Directory Usage (No arrays collected)", messages_collection, pipeline)

    # Test 4: OPTIMIZED Cost Breakdown - limit array sizes
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": {
                "model": "$model",
                "week": {"$dateToString": {"format": "%Y-W%V", "date": "$createdAt"}}
            },
            "cost": {"$sum": "$cost"},
            "count": {"$sum": 1}
        }},
        {"$group": {
            "_id": "$_id.model",
            "weeklyData": {
                "$push": {
                    "week": "$_id.week",
                    "cost": "$cost",
                    "count": "$count"
                }
            },
            "totalCost": {"$sum": "$cost"},
            "totalCount": {"$sum": "$count"}
        }},
        {"$project": {
            "_id": 1,
            "totalCost": 1,
            "totalCount": 1,
            "avgCostPerMessage": {"$divide": ["$totalCost", "$totalCount"]},
            # Limit to most recent 8 weeks
            "recentWeeks": {"$slice": ["$weeklyData", -8]}
        }},
        {"$sort": {"totalCost": -1}}
    ]
    await time_query("OPTIMIZED Cost Breakdown (Weekly aggregation, limited arrays)", messages_collection, pipeline)

    # Compare with original approach for reference
    print(f"\n{'='*60}")
    print("COMPARISON: Original problematic queries")
    print(f"{'='*60}")

    # Original Response Times (pushes ALL values)
    pipeline = [
        {"$match": {
            "createdAt": {"$gte": start_date, "$lte": end_date},
            "responseTime": {"$exists": True, "$ne": None}
        }},
        {"$group": {
            "_id": None,
            "responseTimes": {"$push": "$responseTime"},  # PROBLEM!
            "count": {"$sum": 1}
        }}
    ]
    await time_query("ORIGINAL Response Times (Pushes all values)", messages_collection, pipeline)

    # Summary
    print(f"\n{'='*60}")
    print("Optimization Test Complete")
    print(f"{'='*60}")
    print("\nKey optimizations implemented:")
    print("1. Used MongoDB 7.0 $percentile operator instead of pushing all values")
    print("2. Combined multiple queries using $facet")
    print("3. Avoided collecting large arrays with $addToSet")
    print("4. Limited array sizes and used weekly aggregation for time series")
    print("5. Removed unnecessary $lookup operations")

    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
