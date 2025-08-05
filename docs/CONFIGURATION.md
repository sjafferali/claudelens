# ClaudeLens Configuration Guide

This guide covers all configuration options for ClaudeLens, including environment variables, deployment scenarios, and security considerations.

## Table of Contents
- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [Deployment Scenarios](#deployment-scenarios)
- [Security Configuration](#security-configuration)
- [Performance Tuning](#performance-tuning)
- [CLI Configuration](#cli-configuration)
- [Development Setup](#development-setup)
- [Troubleshooting](#troubleshooting)

## Environment Variables

ClaudeLens uses environment variables for configuration across all components. Here's a comprehensive reference:

### Required Variables

#### MongoDB Configuration
```bash
# REQUIRED: Complete MongoDB connection string
MONGODB_URL=mongodb://admin:password@localhost:27017/claudelens?authSource=admin

# REQUIRED: MongoDB root username for initialization
MONGO_INITDB_ROOT_USERNAME=admin

# REQUIRED: MongoDB root password for initialization
MONGO_INITDB_ROOT_PASSWORD=your-very-secure-password-here
```

#### Security Configuration
```bash
# REQUIRED for production: API key for authentication
API_KEY=your-secure-api-key-here

# REQUIRED for production: Restrict CORS origins
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

### Optional Backend Variables

#### Application Settings
```bash
# Database name (default: claudelens)
DATABASE_NAME=claudelens

# Debug mode (default: false)
DEBUG=false

# Logging level (default: INFO)
LOG_LEVEL=INFO

# API server host (default: 0.0.0.0)
API_HOST=0.0.0.0

# API server port (default: 8000)
API_PORT=8000

# Application environment (default: development)
ENVIRONMENT=production
```

#### Database Connection Tuning
```bash
# Maximum number of concurrent MongoDB connections (default: 100)
MAX_CONNECTIONS_COUNT=100

# Minimum number of MongoDB connections to maintain (default: 10)
MIN_CONNECTIONS_COUNT=10
```

#### Development and Testing
```bash
# Enable test database mode (default: false)
USE_TEST_DB=false

# MongoDB URL for test containers during development
TESTCONTAINER_MONGODB_URL=mongodb://localhost:54321/test_claudelens

# Initial database for MongoDB setup (default: claudelens)
MONGO_INITDB_DATABASE=claudelens
```

### Frontend Variables

Frontend environment variables are prefixed with `VITE_` for Vite build system compatibility:

```bash
# Frontend API endpoint URL (default: /api/v1)
VITE_API_URL=/api/v1

# Frontend API key for authenticated requests (optional)
VITE_API_KEY=your-api-key-here
```

### CLI Tool Variables

```bash
# ClaudeLens API URL for CLI connections (default: http://localhost:8000)
CLAUDELENS_API_URL=http://localhost:8000

# API key for CLI authentication (optional, can be set via config)
CLAUDELENS_API_KEY=your-cli-api-key

# Single Claude data directory path (default: ~/.claude)
CLAUDE_DIR=~/.claude

# Multiple Claude directories (comma-separated, alternative to CLAUDE_DIR)
CLAUDE_DIRS=/path/to/claude1,/path/to/claude2
```

## Configuration Files

### Main Configuration Files

#### 1. Docker Compose Configuration (`docker-compose.yml`)
The primary orchestration configuration for Docker-based deployment:

```yaml
version: '3.8'
services:
  claudelens:
    image: sjafferali/claudelens:latest
    environment:
      - MONGODB_URL=mongodb://admin:password@mongodb:27017/claudelens?authSource=admin
      - API_KEY=your-secure-api-key
      - DEBUG=false
      - BACKEND_CORS_ORIGINS=https://yourdomain.com
    ports:
      - "3000:8080"
    depends_on:
      mongodb:
        condition: service_healthy

  mongodb:
    image: mongo:7.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: your-secure-password
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    command: mongod --auth
```

#### 2. Backend Configuration (`backend/app/core/config.py`)
Python-based configuration management using Pydantic Settings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "claudelens"

    # API Security
    api_key: str = "default-api-key"
    backend_cors_origins: list[str] = ["*"]

    # Application
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = ".env"
```

#### 3. Frontend Configuration (`frontend/vite.config.ts`)
Vite build tool configuration with proxy settings for development:

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
});
```

#### 4. CLI Configuration (`cli/claudelens_cli/core/config.py`)
CLI tool configuration with user settings management:

```python
class CLIConfig:
    def __init__(self):
        self.config_path = Path.home() / ".claudelens" / "config.json"
        self.api_url = "http://localhost:8000"
        self.api_key = None
        self.claude_dirs = []
```

### Environment File Examples

#### Backend Environment (`.env`)
```bash
# MongoDB Configuration
MONGODB_URL=mongodb://admin:changeme@localhost:27017/claudelens?authSource=admin
DATABASE_NAME=claudelens

# Security
API_KEY=your-secure-api-key-here
BACKEND_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Database Connection Pool
MAX_CONNECTIONS_COUNT=100
MIN_CONNECTIONS_COUNT=10
```

#### Frontend Environment (`frontend/.env`)
```bash
# API Configuration
VITE_API_URL=/api/v1
VITE_API_KEY=your-api-key-here
```

## Deployment Scenarios

### 1. Production Docker Compose Deployment

**Security-hardened production configuration:**

1. **Create production environment file:**
```bash
# Create .env.production
cat > .env.production << EOF
MONGODB_URL=mongodb://claudelens_app:secure_password@mongodb:27017/claudelens?authSource=claudelens
DATABASE_NAME=claudelens
API_KEY=$(openssl rand -hex 32)
BACKEND_CORS_ORIGINS=https://yourdomain.com
DEBUG=false
LOG_LEVEL=WARNING
ENVIRONMENT=production
MAX_CONNECTIONS_COUNT=200
MIN_CONNECTIONS_COUNT=20
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=$(openssl rand -hex 32)
EOF
```

2. **Deploy with production configuration:**
```bash
docker compose --env-file .env.production up -d
```

### 2. Custom Docker Deployment

**For custom container orchestration:**

```bash
# Create dedicated network
docker network create claudelens-network

# Start MongoDB
docker run -d \
  --name claudelens-mongodb \
  --network claudelens-network \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=secure_password \
  -v claudelens_mongodb_data:/data/db \
  mongo:7.0 mongod --auth

# Start ClaudeLens
docker run -d \
  --name claudelens-app \
  --network claudelens-network \
  -p 3000:8080 \
  -e MONGODB_URL="mongodb://admin:secure_password@claudelens-mongodb:27017/claudelens?authSource=admin" \
  -e API_KEY="your-secure-api-key" \
  -e BACKEND_CORS_ORIGINS="https://yourdomain.com" \
  -e DEBUG=false \
  sjafferali/claudelens:latest
```

### 3. Kubernetes Deployment

**Example Kubernetes configuration:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: claudelens-secrets
type: Opaque
data:
  mongodb-url: <base64-encoded-mongodb-url>
  api-key: <base64-encoded-api-key>

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claudelens
spec:
  replicas: 2
  selector:
    matchLabels:
      app: claudelens
  template:
    metadata:
      labels:
        app: claudelens
    spec:
      containers:
      - name: claudelens
        image: sjafferali/claudelens:latest
        ports:
        - containerPort: 8080
        env:
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: claudelens-secrets
              key: mongodb-url
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: claudelens-secrets
              key: api-key
        - name: ENVIRONMENT
          value: "production"
```

### 4. Development Setup

**For local development with hot reload:**

```bash
# Start development services
./scripts/dev.sh --load-samples --persistent-db

# Or manually:
# Start MongoDB
docker compose -f docker/docker-compose.dev.yml up -d

# Start backend
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend
cd frontend
npm run dev
```

## Security Configuration

### Production Security Checklist

#### 1. Database Security
```bash
# Create dedicated application user (not root)
mongosh --eval "
db.createUser({
  user: 'claudelens_app',
  pwd: 'secure_password_here',
  roles: [
    { role: 'readWrite', db: 'claudelens' },
    { role: 'dbAdmin', db: 'claudelens' }
  ]
});
"

# Update connection string to use app user
MONGODB_URL=mongodb://claudelens_app:secure_password@mongodb:27017/claudelens?authSource=claudelens
```

#### 2. API Security
```bash
# Generate secure API key
API_KEY=$(openssl rand -hex 32)

# Restrict CORS origins (never use * in production)
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

#### 3. Network Security
```bash
# Bind API to specific interface (optional)
API_HOST=127.0.0.1  # localhost only
API_HOST=10.0.0.5   # specific internal IP

# Use non-standard ports if needed
API_PORT=8443
```

### TLS/SSL Configuration

**For HTTPS deployment with nginx:**

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Performance Tuning

### Database Performance

#### Connection Pool Optimization
```bash
# Adjust based on expected concurrent users
MAX_CONNECTIONS_COUNT=200    # High-traffic production
MIN_CONNECTIONS_COUNT=20     # Maintain warm connections
```

#### MongoDB Configuration
```bash
# Enable MongoDB profiling for optimization
mongosh --eval "db.setProfilingLevel(1, { slowms: 100 })"

# Create custom indexes for your usage patterns
mongosh claudelens --eval "
db.messages.createIndex({ 'content': 'text' });
db.messages.createIndex({ 'sessionId': 1, 'timestamp': 1 });
db.sessions.createIndex({ 'projectId': 1, 'startedAt': -1 });
"
```

### Application Performance

#### Backend Optimization
```bash
# Production logging
LOG_LEVEL=WARNING  # Reduce log verbosity

# Disable debug mode
DEBUG=false

# Set appropriate environment
ENVIRONMENT=production
```

#### Frontend Optimization
```bash
# Production build with optimizations
npm run build

# Enable gzip compression in nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

### Monitoring Configuration

#### Enable Application Metrics
```bash
# Optional: Enable metrics endpoint
ENABLE_METRICS=true
METRICS_PORT=9090
```

#### Database Monitoring
```bash
# MongoDB connection string with monitoring
MONGODB_URL=mongodb://user:pass@host:27017/claudelens?authSource=admin&appName=ClaudeLens&maxPoolSize=100
```

## CLI Configuration

### Initial CLI Setup

```bash
# Install CLI tool
pip install claudelens-cli

# Configure API connection
claudelens config set api_url http://localhost:8000
claudelens config set api_key your-api-key

# Add Claude directories
claudelens config add-claude-dir ~/.claude
claudelens config add-claude-dir /path/to/project/.claude

# View configuration
claudelens config show
```

### CLI Configuration File

The CLI stores configuration in `~/.claudelens/config.json`:

```json
{
  "api_url": "http://localhost:8000",
  "api_key": "your-api-key",
  "claude_dirs": [
    "/Users/username/.claude",
    "/path/to/project/.claude"
  ],
  "sync_options": {
    "watch_mode": false,
    "dry_run": false,
    "overwrite": false
  }
}
```

### Environment Variable Override

CLI configuration can be overridden with environment variables:

```bash
# Override API settings
export CLAUDELENS_API_URL=https://production-api.yourdomain.com
export CLAUDELENS_API_KEY=production-api-key

# Override Claude directories
export CLAUDE_DIRS="/path/to/claude1,/path/to/claude2"

# Run with overrides
claudelens sync
```

## Development Setup

### Local Development Environment

#### 1. Quick Setup
```bash
git clone https://github.com/sjafferali/claudelens.git
cd claudelens
./scripts/dev.sh --load-samples
```

#### 2. Manual Setup
```bash
# Backend development
cd backend
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload

# Frontend development
cd frontend
npm install
cp .env.example .env
npm run dev

# CLI development
cd cli
poetry install
poetry run claudelens --help
```

### Development Environment Variables

```bash
# Backend development (.env)
MONGODB_URL=mongodb://localhost:27017/claudelens_dev
DATABASE_NAME=claudelens_dev
API_KEY=dev-api-key
DEBUG=true
LOG_LEVEL=DEBUG
USE_TEST_DB=false

# Frontend development (.env)
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_KEY=dev-api-key
```

### Testing Configuration

```bash
# Backend testing
USE_TEST_DB=true
TESTCONTAINER_MONGODB_URL=mongodb://localhost:54321/test_claudelens

# Frontend testing
NODE_ENV=test
```

## Troubleshooting

### Common Configuration Issues

#### 1. MongoDB Connection Issues
```bash
# Check connection string format
MONGODB_URL=mongodb://username:password@host:port/database?authSource=authDb

# Test connection
mongosh "mongodb://admin:password@localhost:27017/claudelens?authSource=admin"

# Check if MongoDB is running
docker compose ps mongodb
docker compose logs mongodb
```

#### 2. CORS Issues
```bash
# For development, allow all origins
BACKEND_CORS_ORIGINS=*

# For production, specify exact origins
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

#### 3. API Authentication Issues
```bash
# Check API key configuration
echo $API_KEY

# Test API key with curl
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/health
```

#### 4. CLI Configuration Issues
```bash
# Check CLI configuration
claudelens config show

# Reset CLI configuration
claudelens config reset

# Debug CLI connection
claudelens sync --debug --dry-run
```

### Environment Validation

Create a validation script to check your configuration:

```bash
#!/bin/bash
# validate-config.sh

echo "Validating ClaudeLens configuration..."

# Check required environment variables
required_vars=("MONGODB_URL" "API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set"
        exit 1
    fi
done

# Test MongoDB connection
echo "Testing MongoDB connection..."
mongosh "$MONGODB_URL" --eval "db.admin.ping()" --quiet

# Test API endpoint
echo "Testing API endpoint..."
curl -f -H "X-API-Key: $API_KEY" "http://localhost:8000/api/v1/health"

echo "Configuration validation complete!"
```

### Performance Diagnostics

```bash
# Check MongoDB performance
mongosh --eval "db.serverStatus().connections"

# Check API performance
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/health"

# Monitor Docker resources
docker stats claudelens claudelens_mongodb
```

---

For additional configuration help, see the [main README](../README.md) or check the [troubleshooting section](../README.md#troubleshooting).
