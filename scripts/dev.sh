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
TEST_DB=false

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
    --test-db)
      TEST_DB=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate flag combinations
if [ "$TEST_DB" = true ] && [ "$PERSISTENT_DB" = true ]; then
    echo "Error: --test-db and --persistent-db cannot be used together"
    exit 1
fi

if [ "$TEST_DB" = true ] && [ "$FRONTEND_ONLY" = true ]; then
    echo "Error: --test-db and --frontend-only cannot be used together"
    exit 1
fi

# Start MongoDB
start_mongodb() {
    echo "Starting MongoDB..."

    if [ "$PERSISTENT_DB" = true ]; then
        docker compose -f docker/docker-compose.dev.yml up -d mongodb mongo-express

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
    # Only start MongoDB if not using testcontainers
    if [ "$TEST_DB" = false ]; then
        start_mongodb

        if [ "$LOAD_SAMPLES" = true ]; then
            load_sample_data
        fi
    fi
fi

# Start backend with testcontainers
start_backend_with_testcontainers() {
    echo "Starting backend with testcontainers MongoDB..."
    cd backend

    # Check if poetry is installed
    if ! command -v poetry &> /dev/null; then
        echo "Poetry is not installed. Please install it first."
        exit 1
    fi

    # Install dependencies if needed
    if [ ! -d ".venv" ]; then
        echo "Installing backend dependencies..."
        poetry install
    fi

    # Set environment variable to use testcontainers
    export USE_TEST_DB=true
    export DEBUG=true
    export LOG_LEVEL=info

    # Note: Sample data loading happens after backend starts

    # Start the backend server
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID (using testcontainers)"

    # Wait for backend to be ready
    echo "Waiting for backend to be ready..."
    until curl -s http://localhost:8000/health > /dev/null 2>&1; do
        sleep 1
    done
    echo "Backend is ready!"

    # Load sample data if requested
    if [ "$LOAD_SAMPLES" = true ]; then
        echo "Loading sample data into testcontainer..."
        # Wait a moment to ensure the testcontainer is fully initialized
        sleep 3

        # When using testcontainers, we need to connect to the same instance
        # The backend sets USE_TEST_DB=true, so the sample script will use the same logic
        echo "Running sample data script with testcontainer configuration..."
        USE_TEST_DB=true poetry run python scripts/generate_sample_data.py
    fi

    cd ..
}

# Start backend
start_backend() {
    echo "Starting backend..."
    cd backend

    # Check if poetry is installed
    if ! command -v poetry &> /dev/null; then
        echo "Poetry is not installed. Please install it first."
        exit 1
    fi

    # Install dependencies if needed
    if [ ! -d ".venv" ]; then
        echo "Installing backend dependencies..."
        poetry install
    fi

    # Export environment variables (using root user from docker-compose.dev.yml)
    export MONGODB_URL="mongodb://admin:admin123@localhost:27017/claudelens?authSource=admin"
    export DEBUG=true
    export LOG_LEVEL=info

    # Start the backend server
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"

    # Wait for backend to be ready
    echo "Waiting for backend to be ready..."
    until curl -s http://localhost:8000/health > /dev/null 2>&1; do
        sleep 1
    done
    echo "Backend is ready!"

    cd ..
}

# Start frontend
start_frontend() {
    echo "Starting frontend..."
    cd frontend

    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        echo "npm is not installed. Please install Node.js first."
        exit 1
    fi

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi

    # Start the frontend dev server
    npm run dev &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"

    cd ..
}

# Cleanup function
cleanup() {
    echo -e "\nShutting down services..."

    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi


    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    if [ "$PERSISTENT_DB" = true ]; then
        docker compose -f docker/docker-compose.dev.yml down
    fi

    echo "All services stopped."
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Main execution
if [ "$FRONTEND_ONLY" = false ]; then
    if [ "$TEST_DB" = true ]; then
        # Use testcontainers for MongoDB
        start_backend_with_testcontainers
    else
        # Use Docker Compose for MongoDB
        start_mongodb

        if [ "$LOAD_SAMPLES" = true ]; then
            load_sample_data
        fi

        start_backend
    fi
fi

if [ "$BACKEND_ONLY" = false ]; then
    start_frontend
fi

# Show access information
echo -e "\n=================================="
echo "ClaudeLens Development Environment is ready!"
echo "=================================="
echo "MongoDB: localhost:27017"
echo "Mongo Express: http://localhost:8081 (admin/admin123)"
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo -e "==================================\n"
echo "Press Ctrl+C to stop all services"
echo -e "==================================\n"

# Keep script running
wait
