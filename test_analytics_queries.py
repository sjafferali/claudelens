#!/usr/bin/env python3
"""Test MongoDB queries from analytics service to measure performance."""

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
            # For aggregation pipelines
            cursor = collection.aggregate(pipeline_or_filter)
            results = await cursor.to_list(None)
        else:
            # For regular find queries
            cursor = collection.find(pipeline_or_filter)
            results = await cursor.to_list(None)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n{'='*60}")
        print(f"Query: {name}")
        print(f"Collection: {collection.name}")
        print(f"Type: {'Aggregation' if is_aggregate else 'Find'}")
        print(f"\nFull Query:")
        if is_aggregate:
            print(f"db.{collection.name}.aggregate([")
            for i, stage in enumerate(pipeline_or_filter):
                print(f"  {json.dumps(stage, indent=2, default=str)}")
                if i < len(pipeline_or_filter) - 1:
                    print(",")
            print("])")
        else:
            print(f"db.{collection.name}.find({json.dumps(pipeline_or_filter, indent=2, default=str)})")
        print(f"\nDuration: {duration:.3f} seconds")
        print(f"Result count: {len(results)}")

        # Get explain if possible (only for aggregation)
        if is_aggregate:
            try:
                explain = await collection.aggregate(pipeline_or_filter, explain=True).to_list(None)
                if explain and 'stages' in explain[0]:
                    print(f"Pipeline stages: {len(explain[0]['stages'])}")
            except:
                pass

        return duration, len(results)
    except Exception as e:
        print(f"\nError in {name}: {e}")
        return None, 0

async def main():
    """Test all analytics queries."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.claudelens

    # Collections
    messages_collection = db.messages
    sessions_collection = db.sessions
    projects_collection = db.projects

    # Time range for queries (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    print(f"Testing analytics queries for time range: {start_date} to {end_date}")
    print(f"Database: {db.name}")

    # Test 1: Analytics Summary - Message Count
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {"$count": "total"}
    ]
    await time_query("Analytics Summary - Message Count", messages_collection, pipeline)

    # Test 2: Analytics Summary - Cost Aggregation
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": None,
            "totalCost": {"$sum": "$cost"},
            "inputCost": {"$sum": "$inputCost"},
            "outputCost": {"$sum": "$outputCost"},
            "totalTokens": {"$sum": "$totalTokens"},
            "inputTokens": {"$sum": "$inputTokens"},
            "outputTokens": {"$sum": "$outputTokens"}
        }}
    ]
    await time_query("Analytics Summary - Cost Aggregation", messages_collection, pipeline)

    # Test 3: Activity Heatmap
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "hour": {"$hour": "$createdAt"}
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1, "_id.hour": 1}}
    ]
    await time_query("Activity Heatmap", messages_collection, pipeline)

    # Test 4: Model Usage Stats
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": "$model",
            "count": {"$sum": 1},
            "totalCost": {"$sum": "$cost"},
            "inputTokens": {"$sum": "$inputTokens"},
            "outputTokens": {"$sum": "$outputTokens"}
        }},
        {"$sort": {"count": -1}}
    ]
    await time_query("Model Usage Stats", messages_collection, pipeline)

    # Test 5: Tool Usage Summary
    pipeline = [
        {"$match": {
            "createdAt": {"$gte": start_date, "$lte": end_date},
            "toolCalls": {"$exists": True, "$ne": None}
        }},
        {"$unwind": "$toolCalls"},
        {"$group": {
            "_id": "$toolCalls.name",
            "count": {"$sum": 1},
            "totalExecutionTime": {"$sum": "$toolCalls.executionTime"}
        }},
        {"$sort": {"count": -1}}
    ]
    await time_query("Tool Usage Summary", messages_collection, pipeline)

    # Test 6: Response Times
    pipeline = [
        {"$match": {
            "createdAt": {"$gte": start_date, "$lte": end_date},
            "responseTime": {"$exists": True, "$ne": None}
        }},
        {"$group": {
            "_id": None,
            "responseTimes": {"$push": "$responseTime"},
            "count": {"$sum": 1},
            "avgResponseTime": {"$avg": "$responseTime"},
            "minResponseTime": {"$min": "$responseTime"},
            "maxResponseTime": {"$max": "$responseTime"}
        }}
    ]
    await time_query("Response Times", messages_collection, pipeline)

    # Test 7: Directory Usage (Complex)
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": "$directory",
            "messageCount": {"$sum": 1},
            "totalCost": {"$sum": "$cost"},
            "totalTokens": {"$sum": "$totalTokens"},
            "sessions": {"$addToSet": "$sessionId"},
            "models": {"$addToSet": "$model"},
            "avgResponseTime": {"$avg": "$responseTime"},
            "toolUsage": {
                "$push": {
                    "$cond": [
                        {"$and": [
                            {"$ne": ["$toolCalls", None]},
                            {"$gt": [{"$size": {"$ifNull": ["$toolCalls", []]}}, 0]}
                        ]},
                        "$toolCalls",
                        "$$REMOVE"
                    ]
                }
            }
        }},
        {"$project": {
            "_id": 1,
            "messageCount": 1,
            "totalCost": 1,
            "totalTokens": 1,
            "sessionCount": {"$size": "$sessions"},
            "modelCount": {"$size": "$models"},
            "avgResponseTime": 1,
            "toolCallCount": {"$size": "$toolUsage"}
        }}
    ]
    await time_query("Directory Usage", messages_collection, pipeline)

    # Test 8: Session Depth Analytics
    pipeline = [
        {"$match": {"updatedAt": {"$gte": start_date, "$lte": end_date}}},
        {"$project": {
            "messageCount": 1,
            "totalCost": 1,
            "totalTokens": 1,
            "avgResponseTime": 1
        }},
        {"$group": {
            "_id": None,
            "depths": {"$push": "$messageCount"},
            "count": {"$sum": 1},
            "avgDepth": {"$avg": "$messageCount"},
            "maxDepth": {"$max": "$messageCount"},
            "totalCost": {"$sum": "$totalCost"},
            "avgCostPerSession": {"$avg": "$totalCost"}
        }}
    ]
    await time_query("Session Depth Analytics", sessions_collection, pipeline)

    # Test 9: Cost Breakdown by Model
    pipeline = [
        {"$match": {"createdAt": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": {
                "model": "$model",
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}}
            },
            "cost": {"$sum": "$cost"},
            "count": {"$sum": 1}
        }},
        {"$group": {
            "_id": "$_id.model",
            "dailyCosts": {
                "$push": {
                    "date": "$_id.date",
                    "cost": "$cost",
                    "count": "$count"
                }
            },
            "totalCost": {"$sum": "$cost"},
            "totalCount": {"$sum": "$count"}
        }},
        {"$sort": {"totalCost": -1}}
    ]
    await time_query("Cost Breakdown by Model", messages_collection, pipeline)

    # Test 10: Conversation Flow Pattern
    pipeline = [
        {"$match": {"updatedAt": {"$gte": start_date, "$lte": end_date}}},
        {"$lookup": {
            "from": "messages",
            "localField": "_id",
            "foreignField": "sessionId",
            "as": "messages"
        }},
        {"$project": {
            "messageCount": {"$size": "$messages"},
            "patterns": {
                "$map": {
                    "input": "$messages",
                    "as": "msg",
                    "in": {
                        "role": "$$msg.role",
                        "hasTools": {"$gt": [{"$size": {"$ifNull": ["$$msg.toolCalls", []]}}, 0]}
                    }
                }
            }
        }},
        {"$limit": 100}  # Limit for performance
    ]
    await time_query("Conversation Flow Pattern", sessions_collection, pipeline)

    # Summary
    print(f"\n{'='*60}")
    print("Query Performance Test Complete")
    print(f"{'='*60}")

    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
