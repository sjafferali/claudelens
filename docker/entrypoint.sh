#!/bin/bash
set -e

# Function to handle signals
handle_signal() {
    echo "Received signal, shutting down gracefully..."
    supervisorctl stop all
    exit 0
}

# Trap signals
trap handle_signal SIGTERM SIGINT

# Wait for MongoDB to be ready (if MONGODB_URL is set)
if [ ! -z "$MONGODB_URL" ]; then
    echo "Waiting for MongoDB to be ready..."
    python -c "
import time
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

url = '$MONGODB_URL'
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        client = MongoClient(url, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print('MongoDB is ready!')
        break
    except ConnectionFailure:
        attempt += 1
        print(f'Waiting for MongoDB... ({attempt}/{max_attempts})')
        time.sleep(2)
else:
    print('MongoDB connection failed!')
    sys.exit(1)
"
fi

# Start supervisor
echo "Starting ClaudeLens services..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
