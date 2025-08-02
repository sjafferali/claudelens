"""Testcontainers MongoDB integration for development."""
import os
import atexit
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global container instance
_mongo_container: Optional[object] = None


def get_testcontainer_mongodb_url() -> Optional[str]:
    """Start and return testcontainers MongoDB URL if enabled."""
    global _mongo_container
    
    # Check if testcontainers is enabled
    if not os.getenv("USE_TEST_DB", "").lower() == "true":
        return None
    
    # First check if we have a URL in the environment (from a parent process)
    existing_url = os.getenv("TESTCONTAINER_MONGODB_URL")
    if existing_url:
        logger.info(f"Using existing testcontainer URL from environment: {existing_url}")
        return existing_url
    
    # Return existing container URL if already started
    if _mongo_container:
        url = _mongo_container.get_connection_url().rsplit('/', 1)[0] + '/claudelens?authSource=admin'
        return url
    
    try:
        # Import testcontainers only when needed
        from testcontainers.mongodb import MongoDbContainer
        
        logger.info("Starting MongoDB testcontainer...")
        _mongo_container = MongoDbContainer("mongo:7.0")
        _mongo_container.start()
        
        # Register cleanup on exit
        atexit.register(stop_testcontainer_mongodb)
        
        # Get connection URL and change database name
        connection_url = _mongo_container.get_connection_url()
        logger.info(f"Original testcontainer URL: {connection_url}")
        
        # MongoDB URL format: mongodb://user:pass@host:port/database
        # Testcontainers typically gives us: mongodb://test:test@localhost:port
        # We want: mongodb://test:test@localhost:port/claudelens
        
        # Remove any trailing slash
        base_url = connection_url.rstrip('/')
        
        # If there's already a database name after the port, replace it
        # Otherwise just append /claudelens
        import re
        # Match mongodb://user:pass@host:port(/database)?
        match = re.match(r'(mongodb://[^/]+)(/.+)?', base_url)
        if match:
            base_part = match.group(1)
            # Add authSource=admin since testcontainers creates the user in admin db
            app_url = f"{base_part}/claudelens?authSource=admin"
        else:
            app_url = f"{base_url}/claudelens?authSource=admin"
        
        logger.info(f"Final app URL: {app_url}")
        
        # Export URL for sample data loading
        os.environ["TESTCONTAINER_MONGODB_URL"] = app_url
        
        # Also write to a temp file for cross-process communication
        import tempfile
        url_file = os.path.join(tempfile.gettempdir(), "claudelens_testcontainer_url.txt")
        try:
            with open(url_file, "w") as f:
                f.write(app_url)
            logger.info(f"Wrote testcontainer URL to {url_file}")
        except Exception as e:
            logger.warning(f"Failed to write URL to temp file: {e}")
        
        return app_url
        
    except Exception as e:
        logger.error(f"Failed to start MongoDB testcontainer: {e}")
        return None


def stop_testcontainer_mongodb():
    """Stop the MongoDB testcontainer if running."""
    global _mongo_container
    
    if _mongo_container:
        try:
            logger.info("Stopping MongoDB testcontainer...")
            _mongo_container.stop()
            _mongo_container = None
            logger.info("MongoDB testcontainer stopped")
            
            # Clean up temp file
            import tempfile
            url_file = os.path.join(tempfile.gettempdir(), "claudelens_testcontainer_url.txt")
            if os.path.exists(url_file):
                os.remove(url_file)
        except Exception as e:
            logger.error(f"Error stopping MongoDB testcontainer: {e}")


def is_testcontainer_active() -> bool:
    """Check if testcontainer is currently active."""
    return _mongo_container is not None