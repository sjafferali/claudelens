# Task 05: Docker Infrastructure Setup

## Status
**Status:** TODO  
**Priority:** High  
**Estimated Time:** 2 hours

## Purpose
Create a unified Docker setup that runs both frontend and backend in a single container, along with development and production Docker Compose configurations. This simplifies deployment and ensures consistency across environments.

## Current State
- No Docker configuration
- No containerization strategy
- No deployment setup

## Target State
- Single Docker image containing both frontend and backend
- Nginx serving frontend and proxying API requests
- Development and production Docker Compose files
- Optimized multi-stage builds
- Health checks and proper signal handling

## Implementation Details

### 1. Main Dockerfile

**`docker/Dockerfile`:**
```dockerfile
# Multi-stage Dockerfile for ClaudeLens

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy source code
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 2: Build backend
FROM python:3.11-slim AS backend-builder

# Install Poetry
RUN pip install poetry==1.6.1

WORKDIR /app/backend

# Copy Poetry files
COPY backend/pyproject.toml backend/poetry.lock ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# Copy backend source
COPY backend/ .

# Stage 3: Final image
FROM python:3.11-slim

# Install nginx and supervisor
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nginx \
        supervisor \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Copy nginx config
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Copy supervisor config
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy backend from builder
WORKDIR /app
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /app/backend /app/backend

# Copy frontend from builder
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create necessary directories and set permissions
RUN mkdir -p /var/log/supervisor /var/log/nginx /var/run && \
    chown -R appuser:appuser /app /var/log/nginx /var/log/supervisor /var/run && \
    chmod 755 /var/run

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost/api/v1/health || exit 1

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Start services
ENTRYPOINT ["/app/entrypoint.sh"]
```

### 2. Nginx Configuration

**`docker/nginx.conf`:**
```nginx
user appuser;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;

    # Performance settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # Upstream for backend API
    upstream backend {
        server 127.0.0.1:8000;
        keepalive 32;
    }

    server {
        listen 80;
        server_name _;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # Frontend static files
        location / {
            root /app/frontend/dist;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API proxy
        location /api {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffering
            proxy_buffering off;
            proxy_request_buffering off;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### 3. Supervisor Configuration

**`docker/supervisord.conf`:**
```ini
[supervisord]
nodaemon=true
user=appuser
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/nginx.stdout.log
stderr_logfile=/var/log/supervisor/nginx.stderr.log
priority=10

[program:backend]
command=python -m uvicorn app.main:app --host %(ENV_API_HOST)s --port %(ENV_API_PORT)s --workers 4
directory=/app/backend
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/backend.stdout.log
stderr_logfile=/var/log/supervisor/backend.stderr.log
environment=PYTHONPATH="/app/backend",PYTHONUNBUFFERED="1"
priority=20

[group:claudelens]
programs=nginx,backend
```

### 4. Entrypoint Script

**`docker/entrypoint.sh`:**
```bash
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
```

### 5. Production Docker Compose

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  claudelens:
    image: ghcr.io/sjafferali/claudelens:latest
    container_name: claudelens
    restart: unless-stopped
    ports:
      - "${CLAUDELENS_PORT:-3000}:80"
    environment:
      - MONGODB_URL=mongodb://claudelens_app:${MONGODB_PASSWORD}@mongodb:27017/claudelens?authSource=claudelens
      - REDIS_URL=redis://redis:6379
      - API_KEY=${API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - BACKEND_CORS_ORIGINS=${BACKEND_CORS_ORIGINS:-http://localhost:3000}
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - claudelens-network

  mongodb:
    image: mongo:7.0
    container_name: claudelens_mongodb
    restart: unless-stopped
    ports:
      - "${MONGODB_PORT:-27017}:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGODB_ROOT_USER:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: claudelens
    volumes:
      - mongodb_data:/data/db
      - ./docker/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
    command: mongod --auth --wiredTigerCacheSizeGB 1
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/claudelens --quiet
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - claudelens-network

  redis:
    image: redis:7-alpine
    container_name: claudelens_redis
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - claudelens-network

  # Optional: Backup service
  backup:
    image: mongo:7.0
    container_name: claudelens_backup
    profiles: ["backup"]
    environment:
      MONGO_HOST: mongodb
      MONGO_PORT: 27017
      MONGO_DATABASE: claudelens
      MONGO_USERNAME: ${MONGODB_ROOT_USER:-admin}
      MONGO_PASSWORD: ${MONGODB_ROOT_PASSWORD}
    volumes:
      - ./backups:/backups
    command: |
      sh -c 'mongodump --host=$${MONGO_HOST}:$${MONGO_PORT} --username=$${MONGO_USERNAME} --password=$${MONGO_PASSWORD} --authenticationDatabase=admin --db=$${MONGO_DATABASE} --out=/backups/backup-$$(date +%Y%m%d-%H%M%S)'
    networks:
      - claudelens-network

volumes:
  mongodb_data:
    name: claudelens_mongodb_data
  redis_data:
    name: claudelens_redis_data

networks:
  claudelens-network:
    name: claudelens_network
    driver: bridge
```

### 6. Environment Template

**`.env.example`:**
```env
# MongoDB
MONGODB_ROOT_USER=admin
MONGODB_ROOT_PASSWORD=your-secure-password
MONGODB_PASSWORD=app-password
MONGODB_PORT=27017

# Redis
REDIS_PORT=6379

# Application
CLAUDELENS_PORT=3000
API_KEY=your-api-key-here
JWT_SECRET=your-jwt-secret-here
BACKEND_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Optional
LOG_LEVEL=info
```

### 7. Docker Compose Override for Development

**`docker-compose.override.yml`:**
```yaml
version: '3.8'

services:
  claudelens:
    build:
      context: .
      dockerfile: docker/Dockerfile
    volumes:
      - ./backend:/app/backend:ro
      - ./frontend/dist:/app/frontend/dist:ro
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug

  mongodb:
    ports:
      - "27017:27017"

  mongo-express:
    image: mongo-express:latest
    container_name: claudelens_mongo_express_dev
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: ${MONGODB_ROOT_USER:-admin}
      ME_CONFIG_MONGODB_ADMINPASSWORD: ${MONGODB_ROOT_PASSWORD}
      ME_CONFIG_MONGODB_URL: mongodb://${MONGODB_ROOT_USER:-admin}:${MONGODB_ROOT_PASSWORD}@mongodb:27017/
    depends_on:
      - mongodb
    networks:
      - claudelens-network
```

### 8. Build Script

**`scripts/build.sh`:**
```bash
#!/bin/bash
set -e

# Build script for ClaudeLens Docker image

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get version from package.json or use git commit
VERSION=${VERSION:-$(git describe --tags --always --dirty)}

echo -e "${GREEN}Building ClaudeLens Docker image v${VERSION}${NC}"

# Build the image
docker build \
    -f docker/Dockerfile \
    -t claudelens:${VERSION} \
    -t claudelens:latest \
    --build-arg VERSION=${VERSION} \
    .

echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${YELLOW}Tagged as:${NC}"
echo "  - claudelens:${VERSION}"
echo "  - claudelens:latest"

# Optionally run tests on the built image
if [ "$1" == "--test" ]; then
    echo -e "${YELLOW}Running container tests...${NC}"
    docker run --rm claudelens:${VERSION} python -m pytest /app/backend/tests/test_health.py
fi

# Show image size
echo -e "${YELLOW}Image size:${NC}"
docker images claudelens:${VERSION} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

Make executable:
```bash
chmod +x scripts/build.sh
```

### 9. Docker Ignore File

**`.dockerignore`:**
```
# Git
.git
.gitignore
.github

# Python
**/__pycache__
**/*.pyc
**/*.pyo
**/*.pyd
*.egg-info
**/.pytest_cache
**/.coverage
**/htmlcov
**/.mypy_cache
**/.ruff_cache
**/venv
**/.venv

# Node
**/node_modules
**/dist
**/build
**/.npm
**/*.log
**/coverage

# IDE
.idea
**/*.swp
**/*.swo
.DS_Store

# Project specific
.env
.env.*
!.env.example
**/logs
**/temp
**/tmp
docs
plans
**/*.md
!README.md
```

## Required Technologies
- Docker 24+
- Docker Compose v2
- Docker Buildx (for multi-platform builds)

## Success Criteria
- [ ] Multi-stage Dockerfile building successfully
- [ ] Frontend and backend running in single container
- [ ] Nginx properly routing requests
- [ ] Health checks working
- [ ] Docker Compose files tested
- [ ] Build script working
- [ ] Image size optimized (< 500MB)
- [ ] Container runs as non-root user
- [ ] Signals handled gracefully

## Notes
- Use multi-stage builds to minimize image size
- Run as non-root user for security
- Supervisor manages both nginx and backend processes
- Health checks ensure container readiness
- Support both AMD64 and ARM64 architectures