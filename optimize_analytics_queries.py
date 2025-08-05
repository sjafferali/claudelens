#!/usr/bin/env python3
"""Optimized MongoDB queries for analytics service."""

# ANALYSIS OF PROBLEMATIC QUERIES AND OPTIMIZATIONS:

# 1. Response Times Query - MAJOR ISSUE
# Original pushes ALL response times into memory:
original_response_times = {
    "pipeline": [
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"},
                   "responseTime": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": None,
            "responseTimes": {"$push": "$responseTime"},  # PROBLEM: Pushes ALL values!
            "count": {"$sum": 1},
            "avgResponseTime": {"$avg": "$responseTime"},
            "minResponseTime": {"$min": "$responseTime"},
            "maxResponseTime": {"$max": "$responseTime"}
        }}
    ]
}

# OPTIMIZED: Use MongoDB's $percentile operator (available in MongoDB 7.0+)
# Or use bucketing approach for older versions
optimized_response_times_modern = {
    "pipeline": [
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"},
                   "responseTime": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": None,
            "count": {"$sum": 1},
            "avgResponseTime": {"$avg": "$responseTime"},
            "minResponseTime": {"$min": "$responseTime"},
            "maxResponseTime": {"$max": "$responseTime"},
            "p50": {"$percentile": {"input": "$responseTime", "p": [0.5], "method": "approximate"}},
            "p90": {"$percentile": {"input": "$responseTime", "p": [0.9], "method": "approximate"}},
            "p95": {"$percentile": {"input": "$responseTime", "p": [0.95], "method": "approximate"}},
            "p99": {"$percentile": {"input": "$responseTime", "p": [0.99], "method": "approximate"}}
        }}
    ]
}

# For older MongoDB versions, use sampling:
optimized_response_times_sampling = {
    "pipeline": [
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"},
                   "responseTime": {"$exists": True, "$ne": None}}},
        {"$sample": {"size": 10000}},  # Sample up to 10k documents
        {"$sort": {"responseTime": 1}},
        {"$group": {
            "_id": None,
            "responseTimes": {"$push": "$responseTime"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "count": 1,
            "avgResponseTime": {"$avg": "$responseTimes"},
            "minResponseTime": {"$min": "$responseTimes"},
            "maxResponseTime": {"$max": "$responseTimes"},
            "p50": {"$arrayElemAt": ["$responseTimes", {"$floor": {"$multiply": [0.5, "$count"]}}]},
            "p90": {"$arrayElemAt": ["$responseTimes", {"$floor": {"$multiply": [0.9, "$count"]}}]},
            "p95": {"$arrayElemAt": ["$responseTimes", {"$floor": {"$multiply": [0.95, "$count"]}}]},
            "p99": {"$arrayElemAt": ["$responseTimes", {"$floor": {"$multiply": [0.99, "$count"]}}]}
        }}
    ]
}

# 2. Directory Usage Query - OPTIMIZATION
# Original collects all sessions and models in arrays
original_directory_usage = {
    "pipeline": [
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"}}},
        {"$group": {
            "_id": "$directory",
            "messageCount": {"$sum": 1},
            "totalCost": {"$sum": "$cost"},
            "totalTokens": {"$sum": "$totalTokens"},
            "sessions": {"$addToSet": "$sessionId"},  # Collects ALL unique sessions
            "models": {"$addToSet": "$model"},        # Collects ALL unique models
            "avgResponseTime": {"$avg": "$responseTime"},
            "toolUsage": {
                "$push": {  # Complex conditional push
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
        }}
    ]
}

# OPTIMIZED: Don't collect arrays, just count unique values
optimized_directory_usage = {
    "pipeline": [
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"}}},
        {"$facet": {
            # Main aggregation
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
        }},
        # Merge the results
        {"$project": {
            "results": {
                "$map": {
                    "input": "$metrics",
                    "as": "metric",
                    "in": {
                        "$mergeObjects": [
                            "$$metric",
                            {
                                "sessionCount": {
                                    "$ifNull": [
                                        {"$arrayElemAt": [
                                            {"$filter": {
                                                "input": "$sessionCounts",
                                                "cond": {"$eq": ["$$this._id", "$$metric._id"]}
                                            }},
                                            0
                                        ]}.sessionCount,
                                        0
                                    ]
                                },
                                "modelCount": {
                                    "$ifNull": [
                                        {"$arrayElemAt": [
                                            {"$filter": {
                                                "input": "$modelCounts",
                                                "cond": {"$eq": ["$$this._id", "$$metric._id"]}
                                            }},
                                            0
                                        ]}.modelCount,
                                        0
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }},
        {"$unwind": "$results"},
        {"$replaceRoot": {"newRoot": "$results"}}
    ]
}

# 3. Conversation Flow Pattern - MAJOR ISSUE
# Original uses $lookup to load ALL messages for each session
original_conversation_flow = {
    "pipeline": [
        {"$match": {"updatedAt": {"$gte": "start_date", "$lte": "end_date"}}},
        {"$lookup": {
            "from": "messages",
            "localField": "_id",
            "foreignField": "sessionId",
            "as": "messages"  # Loads ALL messages for EACH session!
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
        {"$limit": 100}
    ]
}

# OPTIMIZED: Aggregate patterns without loading all messages
optimized_conversation_flow = {
    "pipeline": [
        # Start from messages collection instead
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"}}},
        {"$sort": {"sessionId": 1, "timestamp": 1}},
        {"$group": {
            "_id": "$sessionId",
            "messageCount": {"$sum": 1},
            "roles": {"$push": "$role"},
            "toolUsageCount": {
                "$sum": {
                    "$cond": [
                        {"$gt": [{"$size": {"$ifNull": ["$toolCalls", []]}}, 0]},
                        1,
                        0
                    ]
                }
            },
            "firstMessage": {"$first": "$timestamp"},
            "lastMessage": {"$last": "$timestamp"}
        }},
        {"$limit": 100},
        # Now get session details if needed
        {"$lookup": {
            "from": "sessions",
            "localField": "_id",
            "foreignField": "_id",
            "as": "session"
        }},
        {"$unwind": {"path": "$session", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "messageCount": 1,
            "rolePattern": "$roles",
            "toolUsageRate": {"$divide": ["$toolUsageCount", "$messageCount"]},
            "duration": {"$subtract": ["$lastMessage", "$firstMessage"]},
            "sessionSummary": "$session.summary"
        }}
    ]
}

# 4. Cost Breakdown by Model - OPTIMIZATION
# Original creates arrays of all daily costs
original_cost_breakdown = {
    "pipeline": [
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"}}},
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
            "dailyCosts": {  # Creates array of ALL daily costs
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
}

# OPTIMIZED: Limit to recent days or aggregate by week/month for longer ranges
optimized_cost_breakdown = {
    "pipeline": [
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"}}},
        {"$group": {
            "_id": {
                "model": "$model",
                # Use week grouping for ranges > 30 days
                "period": {
                    "$dateToString": {
                        "format": "%Y-W%V",  # Year-Week format
                        "date": "$createdAt"
                    }
                }
            },
            "cost": {"$sum": "$cost"},
            "count": {"$sum": 1}
        }},
        {"$group": {
            "_id": "$_id.model",
            "periodCosts": {
                "$push": {
                    "period": "$_id.period",
                    "cost": "$cost",
                    "count": "$count"
                }
            },
            "totalCost": {"$sum": "$cost"},
            "totalCount": {"$sum": "$count"},
            "avgCostPerMessage": {"$avg": {"$divide": ["$cost", "$count"]}}
        }},
        {"$sort": {"totalCost": -1}},
        {"$project": {
            "_id": 1,
            "totalCost": 1,
            "totalCount": 1,
            "avgCostPerMessage": 1,
            # Limit array size to most recent 30 periods
            "recentPeriods": {"$slice": ["$periodCosts", -30]}
        }}
    ]
}

# 5. Analytics Summary - Cost Aggregation
# Can be optimized by using a single pass with $facet
optimized_analytics_summary = {
    "pipeline": [
        {"$match": {"createdAt": {"$gte": "start_date", "$lte": "end_date"}}},
        {"$facet": {
            "count": [{"$count": "total"}],
            "costs": [{
                "$group": {
                    "_id": None,
                    "totalCost": {"$sum": "$cost"},
                    "inputCost": {"$sum": "$inputCost"},
                    "outputCost": {"$sum": "$outputCost"},
                    "totalTokens": {"$sum": "$totalTokens"},
                    "inputTokens": {"$sum": "$inputTokens"},
                    "outputTokens": {"$sum": "$outputTokens"}
                }
            }]
        }},
        {"$project": {
            "total": {"$arrayElemAt": ["$count.total", 0]},
            "costs": {"$arrayElemAt": ["$costs", 0]}
        }}
    ]
}
