"""Main FastAPI application."""

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.api_v1.api import api_router
from app.api.api_v1.endpoints.websocket import router as websocket_router
from app.core.config import settings
from app.core.database import close_mongodb_connection, connect_to_mongodb, get_database
from app.core.db_init import initialize_database
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.logging import get_logger, setup_logging
from app.middleware.forwarded_headers import ForwardedHeadersMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit_tracking import RateLimitTrackingMiddleware

# Configure logging
setup_logging(
    log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO"
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ClaudeLens API...")
    await connect_to_mongodb()
    logger.info("Connected to MongoDB")

    # Initialize database (create collections, indexes, etc.)
    try:
        db = await get_database()
        await initialize_database(db)

        # Start background tasks
        from app.services.background_tasks import start_background_tasks

        await start_background_tasks(db)
        logger.info("Started background tasks")
    except Exception:
        logger.exception("Failed to initialize database")
        raise

    yield

    # Shutdown
    logger.info("Shutting down ClaudeLens API...")

    # Stop background tasks
    from app.services.background_tasks import stop_background_tasks

    await stop_background_tasks()
    logger.info("Stopped background tasks")

    await close_mongodb_connection()
    logger.info("Disconnected from MongoDB")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Add middleware
# IMPORTANT: ForwardedHeadersMiddleware must be added first to handle proxy headers
app.add_middleware(ForwardedHeadersMiddleware)

# IMPORTANT: SessionMiddleware must be added before OAuth initialization
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY
    if hasattr(settings, "SESSION_SECRET_KEY")
    else secrets.token_urlsafe(32),
    session_cookie=settings.SESSION_COOKIE_NAME
    if hasattr(settings, "SESSION_COOKIE_NAME")
    else "claudelens_session",
    https_only=settings.SESSION_COOKIE_SECURE
    if hasattr(settings, "SESSION_COOKIE_SECURE")
    else False,
    same_site="lax",  # type: ignore
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitTrackingMiddleware, calls=500, period=60)


# Exception handlers
@app.exception_handler(NotFoundError)
async def not_found_exception_handler(
    request: Request, exc: NotFoundError
) -> JSONResponse:
    """Handle NotFoundError exceptions."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "type": "not_found"},
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle ValidationError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"},
    )


@app.exception_handler(AuthenticationError)
async def auth_exception_handler(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    """Handle AuthenticationError exceptions."""
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc), "type": "authentication_error"},
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # In debug mode, show the actual error
    if settings.DEBUG:
        return JSONResponse(
            status_code=500, content={"detail": str(exc), "type": type(exc).__name__}
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "internal_error"},
    )


# Root endpoint
@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {"name": settings.APP_NAME, "version": settings.VERSION, "status": "running"}


# Health check
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include WebSocket endpoints at root level
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])
