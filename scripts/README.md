# ClaudeLens Development Scripts

This directory contains scripts to help with ClaudeLens development and deployment.

## dev.sh - Development Environment Script

The `dev.sh` script sets up and manages the complete ClaudeLens development environment, including MongoDB, backend API, and frontend services.

### Prerequisites

Before running the script, ensure you have:
- Docker and Docker Compose installed
- Python 3.11+ with Poetry installed
- Node.js and npm installed
- Port 27017 (MongoDB), 8000 (Backend), 8081 (Mongo Express), and 5173 (Frontend) available

### Basic Usage

```bash
# Make the script executable (first time only)
chmod +x scripts/dev.sh

# Run with default settings (ephemeral database, all services)
./scripts/dev.sh
```

### Command Line Options

#### `--persistent-db`
Starts MongoDB with persistent storage using Docker volumes. Without this flag, the database is ephemeral and data will be lost when the script stops.

```bash
# Start with persistent MongoDB storage
./scripts/dev.sh --persistent-db
```

#### `--load-samples`
Loads sample data into MongoDB after startup. This creates test projects, sessions, and messages for development and testing.

```bash
# Start with sample data
./scripts/dev.sh --load-samples

# Combine with persistent database
./scripts/dev.sh --persistent-db --load-samples
```

#### `--backend-only`
Starts only the backend API server and MongoDB, skipping the frontend. Useful for API development or testing.

```bash
# Start only backend services
./scripts/dev.sh --backend-only

# Backend with persistent DB and samples
./scripts/dev.sh --backend-only --persistent-db --load-samples
```

#### `--frontend-only`
Starts only the frontend development server, skipping MongoDB and backend. Assumes backend is already running or you're using a remote backend.

```bash
# Start only frontend
./scripts/dev.sh --frontend-only
```

#### `--test-db`
Starts the backend with a testcontainers MongoDB instance. This provides a quick, isolated test environment with automatic cleanup. The MongoDB container is ephemeral and will be destroyed when the script stops. Cannot be used with `--persistent-db` or `--frontend-only`.

**Key Features:**
- Automatic MongoDB container startup
- Dynamic port allocation (no port conflicts)
- Automatic cleanup on exit
- Integrated with backend lifecycle

```bash
# Start backend with testcontainers MongoDB
./scripts/dev.sh --test-db

# Backend only with testcontainers
./scripts/dev.sh --test-db --backend-only

# Full stack with testcontainers
./scripts/dev.sh --test-db
```

**Note:** The `--load-samples` flag with `--test-db` now works automatically! The script will detect the testcontainer MongoDB instance and load sample data into it.

### Usage Examples

#### Full Development Environment
```bash
# Default: All services with ephemeral database
./scripts/dev.sh

# Full environment with persistent database
./scripts/dev.sh --persistent-db

# Full environment with sample data
./scripts/dev.sh --persistent-db --load-samples
```

#### Backend Development
```bash
# Backend API with ephemeral database
./scripts/dev.sh --backend-only

# Backend API with persistent database and samples
./scripts/dev.sh --backend-only --persistent-db --load-samples
```

#### Frontend Development
```bash
# Frontend only (requires backend to be running separately)
./scripts/dev.sh --frontend-only
```

#### First Time Setup
```bash
# Recommended for first time setup
./scripts/dev.sh --persistent-db --load-samples
```

#### Quick Test Environment
```bash
# Fast startup with isolated test database and sample data
./scripts/dev.sh --test-db --load-samples

# Backend only with test database and sample data
./scripts/dev.sh --test-db --backend-only --load-samples
```

### Services Started

Depending on the flags used, the script will start:

1. **MongoDB** (unless `--frontend-only`)
   - Port: 27017
   - Credentials: admin / admin123 (root user)
   - Database: claudelens

2. **Mongo Express** (unless `--frontend-only`)
   - URL: http://localhost:8081
   - Credentials: admin / admin123

3. **Backend API** (unless `--frontend-only`)
   - URL: http://localhost:8000
   - API Docs: http://localhost:8000/api/v1/docs
   - Hot reload enabled

4. **Frontend** (unless `--backend-only`)
   - URL: http://localhost:5173
   - Hot reload enabled

### Environment Variables

The script sets the following environment variables for the backend:
- `MONGODB_URL`: Connection string for MongoDB
- `DEBUG`: Set to true for development
- `LOG_LEVEL`: Set to info

### Stopping Services

Press `Ctrl+C` to stop all services. The script will:
1. Gracefully shut down all running services
2. Stop and remove Docker containers (if using `--persistent-db`)
3. Preserve data volumes (if using `--persistent-db`)

### Troubleshooting

#### Port Already in Use
If you get a "port already in use" error:
```bash
# Check what's using the ports
lsof -i :27017  # MongoDB
lsof -i :8000   # Backend
lsof -i :8081   # Mongo Express
lsof -i :5173   # Frontend

# Kill the process using the port
kill -9 <PID>
```

#### Docker Issues
```bash
# Clean up Docker resources
docker system prune -f

# Remove MongoDB volume (WARNING: deletes all data)
docker volume rm claudelens_mongodb_data
```

#### Python Version Issues
The backend requires Python 3.11+. If you see version errors:
```bash
# Check your Python version
python --version

# Install Python 3.11+ using your package manager
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

### Notes

- The script uses Poetry for Python dependency management
- Frontend dependencies are installed automatically via npm
- All services run in the foreground and output logs to the terminal
- The script includes proper cleanup handlers to stop services on exit
- The `--test-db` flag is ideal for:
  - Quick testing without Docker Compose setup
  - Isolated test environments
  - CI/CD pipelines
  - Running multiple instances simultaneously (testcontainers uses random ports)
- When using `--test-db` with `--load-samples`, the script automatically:
  - Waits for the testcontainer to be ready
  - Detects the dynamic MongoDB URL
  - Loads sample data into the testcontainer instance
  - Provides immediate access to test data