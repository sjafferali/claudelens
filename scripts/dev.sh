#!/bin/bash
set -e

# Development environment setup script
echo "ClaudeLens Development Environment"
echo "=================================="

# Parse arguments
PERSISTENT_DB=false
LOAD_SAMPLES=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --persistent-db)
      PERSISTENT_DB=true
      shift
      ;;
    --load-samples)
      LOAD_SAMPLES=true
      shift
      ;;
    --backend-only)
      BACKEND_ONLY=true
      shift
      ;;
    --frontend-only)
      FRONTEND_ONLY=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Start MongoDB
start_mongodb() {
    echo "Starting MongoDB..."
    
    if [ "$PERSISTENT_DB" = true ]; then
        docker-compose -f docker/docker-compose.dev.yml up -d mongodb mongo-express
        
        # Wait for MongoDB to be ready
        echo "Waiting for MongoDB to be ready..."
        until docker exec claudelens_mongodb mongosh --eval "db.adminCommand('ping')" &>/dev/null; do
            sleep 1
        done
        echo "MongoDB is ready!"
    else
        # Use testcontainers (implemented in Python test code)
        echo "Using testcontainers for MongoDB (ephemeral)"
    fi
}

# Load sample data
load_sample_data() {
    echo "Loading sample data..."
    cd backend
    poetry run python scripts/generate_sample_data.py
    cd ..
}

# Main execution
if [ "$BACKEND_ONLY" = false ] && [ "$FRONTEND_ONLY" = false ]; then
    start_mongodb
    
    if [ "$LOAD_SAMPLES" = true ]; then
        load_sample_data
    fi
fi

# Implementation will be completed in later tasks
echo "Development script ready. Additional implementation pending."