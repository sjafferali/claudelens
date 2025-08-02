# Task 08: Backend API Structure and Base Setup

## Status
**Status:** TODO
**Priority:** High
**Estimated Time:** 3 hours

## Purpose
Set up the FastAPI backend application structure with proper routing, dependency injection, middleware, and core utilities. This establishes the foundation for all API endpoints and services.

## Current State
- Basic backend project initialized
- Database models defined
- No API structure
- No FastAPI application

## Target State
- Complete FastAPI application structure
- API versioning setup
- Middleware for CORS, authentication, and logging
- Health check endpoint
- OpenAPI documentation configured
- Error handling framework

## Implementation Details

### 1. Main Application Entry Point

**`backend/app/main.py`:**
```python
"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.database import connect_to_mongodb, close_mongodb_connection
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ClaudeLens API...")
    await connect_to_mongodb()
    logger.info("Connected to MongoDB")

    yield

    # Shutdown
    logger.info("Shutting down ClaudeLens API...")
    await close_mongodb_connection()
    logger.info("Disconnected from MongoDB")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)
```

### 2. API Router Structure

**`backend/app/api/api_v1/api.py`:**
```python
"""Main API router."""
from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    projects,
    sessions,
    messages,
    search,
    analytics,
    ingest
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["sessions"]
)

api_router.include_router(
    messages.router,
    prefix="/messages",
    tags=["messages"]
)

api_router.include_router(
    search.router,
    prefix="/search",
    tags=["search"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

api_router.include_router(
    ingest.router,
    prefix="/ingest",
    tags=["ingest"]
)


@api_router.get("/health")
async def api_health():
    """API health check."""
    return {"status": "ok", "api_version": "v1"}
```

### 3. Dependencies

**`backend/app/api/dependencies.py`:**
```python
"""API dependencies."""
from typing import Optional, Annotated
from fastapi import Header, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.database import get_database
from app.core.security import verify_api_key


async def get_db() -> AsyncIOMotorDatabase:
    """Get database dependency."""
    return await get_database()


async def verify_api_key_header(
    x_api_key: Annotated[Optional[str], Header()] = None
) -> str:
    """Verify API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return x_api_key


# Common dependencies
CommonDeps = Annotated[AsyncIOMotorDatabase, Depends(get_db)]
AuthDeps = Annotated[str, Depends(verify_api_key_header)]
```

### 4. Logging Middleware

**`backend/app/middleware/logging.py`:**
```python
"""Logging middleware."""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests and responses."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": f"{duration:.3f}s"
                }
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration": f"{duration:.3f}s",
                    "error": str(e)
                },
                exc_info=True
            )
            raise
```

### 5. Rate Limiting Middleware

**`backend/app/middleware/rate_limit.py`:**
```python
"""Rate limiting middleware."""
import time
from typing import Dict, Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, list] = defaultdict(list)
        self._cleanup_task = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        # Get client identifier (IP or API key)
        client_id = self._get_client_id(request)

        # Check rate limit
        now = time.time()

        # Clean old entries
        self.clients[client_id] = [
            timestamp for timestamp in self.clients[client_id]
            if timestamp > now - self.period
        ]

        # Check if limit exceeded
        if len(self.clients[client_id]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.period))
                }
            )

        # Record this call
        self.clients[client_id].append(now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls - len(self.clients[client_id])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))

        # Start cleanup task if not running
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key[:8]}"

        # Fall back to IP
        if request.client:
            return f"ip:{request.client.host}"

        return "unknown"

    async def _periodic_cleanup(self):
        """Periodically clean up old entries."""
        while True:
            await asyncio.sleep(self.period)
            now = time.time()

            # Clean up old entries
            for client_id in list(self.clients.keys()):
                self.clients[client_id] = [
                    timestamp for timestamp in self.clients[client_id]
                    if timestamp > now - self.period
                ]

                # Remove empty entries
                if not self.clients[client_id]:
                    del self.clients[client_id]
```

### 6. Security Utilities

**`backend/app/core/security.py`:**
```python
"""Security utilities."""
import secrets
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_api_key(api_key: str) -> bool:
    """Verify API key."""
    # Simple comparison for now
    # In production, this should check against database
    return api_key == settings.API_KEY


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a new API key."""
    return secrets.token_urlsafe(32)
```

### 7. Common Schemas

**`backend/app/schemas/common.py`:**
```python
"""Common schemas used across the API."""
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    type: str = "error"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response schema."""
    message: str
    data: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 8. Exception Handlers

**`backend/app/core/exceptions.py`:**
```python
"""Custom exceptions."""
from typing import Optional


class ClaudeLensException(Exception):
    """Base exception for ClaudeLens."""

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_type: str = "internal_error"
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(detail)


class NotFoundError(ClaudeLensException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: Optional[str] = None):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(detail, status_code=404, error_type="not_found")


class ValidationError(ClaudeLensException):
    """Validation error."""

    def __init__(self, detail: str):
        super().__init__(detail, status_code=422, error_type="validation_error")


class AuthenticationError(ClaudeLensException):
    """Authentication error."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(detail, status_code=401, error_type="authentication_error")


class AuthorizationError(ClaudeLensException):
    """Authorization error."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail, status_code=403, error_type="authorization_error")


class RateLimitError(ClaudeLensException):
    """Rate limit error."""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail, status_code=429, error_type="rate_limit_error")
```

### 9. Update Backend Structure

**`backend/app/__init__.py`:**
```python
"""ClaudeLens Backend API."""
from app.main import app

__all__ = ["app"]
```

**`backend/app/api/__init__.py`:**
```python
"""API package."""
```

**`backend/app/api/api_v1/__init__.py`:**
```python
"""API v1 package."""
```

**`backend/app/api/api_v1/endpoints/__init__.py`:**
```python
"""API endpoints package."""
```

**`backend/app/middleware/__init__.py`:**
```python
"""Middleware package."""
```

**`backend/app/schemas/__init__.py`:**
```python
"""Schemas package."""
```

## Required Technologies
- FastAPI
- Uvicorn
- Motor (MongoDB async driver)
- python-jose (JWT handling)
- passlib (password hashing)

## Success Criteria
- [ ] FastAPI application starts successfully
- [ ] OpenAPI documentation available at /api/v1/docs
- [ ] Health check endpoint working
- [ ] CORS configured properly
- [ ] Request logging implemented
- [ ] Rate limiting working
- [ ] API key authentication functional
- [ ] Error handling framework in place
- [ ] All middleware properly configured

## Notes
- Use dependency injection for database access
- Implement proper error handling at all levels
- Rate limiting is in-memory for simplicity
- Consider Redis for production rate limiting
- All endpoints should return consistent response formats
