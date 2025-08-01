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