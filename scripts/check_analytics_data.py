#!/usr/bin/env python3
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def check_data():
    # Use the same connection as the backend
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017/claudelens")
    client = AsyncIOMotorClient(mongodb_url)
    db = client.get_default_database()

    # Check unique session IDs
    session_ids = await db.messages.distinct('sessionId')
    print(f'Unique session IDs: {len(session_ids)}')

    # Check message count per session
    pipeline = [
        {'$group': {
            '_id': '$sessionId',
            'count': {'$sum': 1},
            'cost': {'$sum': '$costUsd'}
        }}
    ]
    cursor = db.messages.aggregate(pipeline)
    results = await cursor.to_list(None)
    print(f'\nMessages per session:')
    total_messages = 0
    total_cost = 0
    for r in results:
        count = r['count']
        cost = float(r['cost']) if r['cost'] else 0
        total_messages += count
        total_cost += cost
        print(f'  Session {r["_id"]}: {count} messages, ${cost:.2f}')

    print(f'\nTotal messages: {total_messages}')
    print(f'Total cost: ${total_cost:.2f}')

    # Check directory grouping
    dir_pipeline = [
        {'$match': {'cwd': {'$exists': True, '$ne': None}}},
        {'$group': {
            '_id': '$cwd',
            'total_cost': {'$sum': '$costUsd'},
            'message_count': {'$sum': 1},
            'session_ids': {'$addToSet': '$sessionId'}
        }}
    ]
    dir_cursor = db.messages.aggregate(dir_pipeline)
    dir_results = await dir_cursor.to_list(None)
    print(f'\nDirectory analysis:')
    for r in dir_results[:5]:
        cost = float(r['total_cost']) if r['total_cost'] else 0
        print(f'  Dir {r["_id"]}: {r["message_count"]} messages, ${cost:.2f}, {len(r["session_ids"])} sessions')

if __name__ == '__main__':
    asyncio.run(check_data())
