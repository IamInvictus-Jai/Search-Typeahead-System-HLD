"""
FastAPI application entry point.
Phase 2: Database setup and ingestion on startup.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.logger import logger
from app.db import get_pool, close_pool, create_tables
from app.ingestion import ensure_data_loaded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown logic.
    """
    # Startup
    logger.info("Starting Search Typeahead System...")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Redis nodes configured: {settings.num_redis_nodes}")
    
    try:
        # Validate configuration
        settings.validate_redis_nodes()
        logger.info("Configuration validated")
        
        # Create database connection pool
        await get_pool()
        
        # Create tables (idempotent)
        await create_tables()
        
        # Ensure data is loaded (idempotent)
        await ensure_data_loaded()
        
        logger.info("✅ Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_pool()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Search Typeahead System",
    description="A production-grade search typeahead system with distributed caching",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "typeahead-backend",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Search Typeahead System API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "suggest": "/suggest?q=<prefix> (Phase 3)",
            "search": "/search (Phase 3)",
            "cache_debug": "/cache/debug?prefix=<prefix> (Phase 4)",
            "metrics": "/metrics (Phase 8)"
        }
    }
