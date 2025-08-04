import pymongo

# Connect to MongoDB
client = pymongo.MongoClient('mongodb://admin:AeSh3sewoodeing3ujatoo3ohphee8oh@c-rat.local.samir.systems:27017/claudelens?authSource=admin')
db = client.claudelens

# Check if costUsd field exists in any messages
with_cost = db.messages.find({'costUsd': {'$exists': True}}).limit(5)
with_cost_list = list(with_cost)
print(f'Messages with costUsd field: {len(with_cost_list)}')
for msg in with_cost_list:
    print(f"  - uuid: {msg.get('uuid')}, costUsd: {msg.get('costUsd')}, type: {msg.get('type')}")

# Check assistant messages without costUsd
no_cost = db.messages.find({'costUsd': {'$exists': False}, 'type': 'assistant'}).limit(5)
no_cost_list = list(no_cost)
print(f'\nAssistant messages without costUsd field: {len(no_cost_list)}')
for msg in no_cost_list:
    print(f"  - uuid: {msg.get('uuid')}, type: {msg.get('type')}")

# Total counts
total_with_cost = db.messages.count_documents({'costUsd': {'$exists': True}})
total_assistant = db.messages.count_documents({'type': 'assistant'})
print(f'\nTotal messages with costUsd: {total_with_cost}')
print(f'Total assistant messages: {total_assistant}')

# Check a specific session
session_id = 'c2017c7e-c211-419c-a1d8-857a97bccbf6'
session_msgs = db.messages.find({'sessionId': session_id, 'type': 'assistant'}).limit(3)
print(f'\nAssistant messages from session {session_id}:')
for msg in session_msgs:
    print(f"  - uuid: {msg.get('uuid')}, costUsd: {msg.get('costUsd', 'NOT PRESENT')}")
