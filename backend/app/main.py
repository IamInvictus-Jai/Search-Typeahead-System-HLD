"""
FastAPI application entry point.
Phase 3: Basic typeahead API with direct PostgreSQL queries.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import List
from app.config import settings
from app.logger import logger
from app.db import get_pool, close_pool, create_tables, fetch, execute
from app.ingestion import ensure_data_loaded
from app.utils import normalize_prefix
from app.cache import (
    initialize_cache,
    close_cache,
    get_suggestions_from_cache,
    set_suggestions_in_cache,
    get_cache_debug_info
)
from app.batch import (
    initialize_batch_system,
    close_batch_system,
    record_search
)


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
        
        # Initialize Redis cache and consistent hashing
        await initialize_cache()
        
        # Initialize batch write system
        await initialize_batch_system()
        
        logger.info("✅ Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_batch_system()
    await close_cache()
    await close_pool()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Search Typeahead System",
    description="A production-grade search typeahead system with distributed caching",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        f"http://localhost:{settings.frontend_port}"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SuggestionResponse(BaseModel):
    query: str
    score: float


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    message: str


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
        "phase": "3",
        "endpoints": {
            "health": "/health",
            "suggest": "/suggest?q=<prefix>",
            "search": "POST /search",
            "cache_debug": "/cache/debug?prefix=<prefix> (Phase 4)",
            "metrics": "/metrics (Phase 8)"
        }
    }


@app.get("/suggest", response_model=List[SuggestionResponse])
async def get_suggestions(q: str = ""):
    """
    Get typeahead suggestions for a given prefix.
    
    Phase 4: Cache-first read path with consistent hashing.
    
    Args:
        q: Search prefix
    
    Returns:
        List of up to 10 suggestions sorted by total_count descending
    """
    # Normalize prefix
    prefix = normalize_prefix(q)
    
    # Handle empty prefix
    if not prefix:
        return []
    
    try:
        # Check cache first (Phase 4)
        cached_suggestions = await get_suggestions_from_cache(prefix)
        
        if cached_suggestions is not None:
            # Cache hit - return cached results
            return [
                SuggestionResponse(query=item['query'], score=item['score'])
                for item in cached_suggestions
            ]
        
        # Cache miss - query PostgreSQL
        query = """
            SELECT query, total_count as score
            FROM queries
            WHERE query LIKE $1
            ORDER BY total_count DESC
            LIMIT 10
        """
        
        results = await fetch(query, f"{prefix}%")
        
        # Convert to response model
        suggestions = [
            SuggestionResponse(query=row['query'], score=float(row['score']))
            for row in results
        ]
        
        # Store in cache for future requests
        cache_data = [{"query": s.query, "score": s.score} for s in suggestions]
        await set_suggestions_in_cache(prefix, cache_data)
        
        logger.info(f"Suggestions for '{prefix}': {len(suggestions)} results (from DB)")
        return suggestions
    
    except Exception as e:
        logger.error(f"Error fetching suggestions for '{prefix}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch suggestions")


@app.post("/search", response_model=SearchResponse)
async def submit_search(request: SearchRequest):
    """
    Submit a search query and update counts.
    
    Phase 5: Asynchronous batch write (buffered, flushed periodically).
    
    Args:
        request: SearchRequest with query field
    
    Returns:
        SearchResponse with confirmation message
    """
    # Normalize query
    query = normalize_prefix(request.query)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Record in active buffer (async write - Phase 5)
        await record_search(query)
        
        logger.info(f"Search buffered: '{query}'")
        return SearchResponse(message="Searched")
    
    except Exception as e:
        logger.error(f"Error buffering search for '{query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit search")


@app.get("/cache/debug")
async def cache_debug(prefix: str = ""):
    """
    Debug endpoint to show cache routing and status.
    
    Demonstrates consistent hashing distribution across nodes.
    
    Args:
        prefix: Search prefix to debug
    
    Returns:
        Debug information including node assignment, hit/miss status, TTL
    """
    if not prefix:
        raise HTTPException(status_code=400, detail="Prefix parameter required")
    
    # Normalize prefix (same as suggest endpoint)
    normalized = normalize_prefix(prefix)
    
    try:
        debug_info = await get_cache_debug_info(normalized)
        return debug_info
    
    except Exception as e:
        logger.error(f"Cache debug error for '{prefix}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Cache debug failed")
