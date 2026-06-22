"""
Database connection pool and query helpers using asyncpg.
No ORM - raw SQL queries for transparency and performance.
"""

import asyncpg
from typing import Optional, List, Any
from app.config import settings
from app.logger import logger


# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """
    Get or create the database connection pool.
    
    Returns:
        asyncpg.Pool instance
    """
    global _pool
    if _pool is None:
        logger.info(f"Creating database connection pool: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
        _pool = await asyncpg.create_pool(
            settings.postgres_dsn,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database connection pool created")
    return _pool


async def close_pool():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("Database connection pool closed")
        _pool = None


async def create_tables():
    """
    Create all required database tables and indexes.
    Safe to run multiple times (uses IF NOT EXISTS).
    """
    pool = await get_pool()
    
    schema_sql = """
    -- Main queries table
    CREATE TABLE IF NOT EXISTS queries (
        query TEXT PRIMARY KEY,
        total_count BIGINT DEFAULT 1,
        last_searched_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Index for sorting by count
    CREATE INDEX IF NOT EXISTS idx_queries_count ON queries (total_count DESC);
    
    -- Index for prefix queries (helps with LIKE 'prefix%')
    CREATE INDEX IF NOT EXISTS idx_queries_prefix ON queries (query text_pattern_ops);
    
    -- Recent searches for trending (hourly buckets)
    CREATE TABLE IF NOT EXISTS recent_searches (
        query TEXT NOT NULL,
        bucket_time TIMESTAMP NOT NULL,
        count INTEGER DEFAULT 1,
        PRIMARY KEY (query, bucket_time)
    );
    
    -- Index for cleanup queries
    CREATE INDEX IF NOT EXISTS idx_recent_searches_bucket ON recent_searches (bucket_time);
    
    -- Metadata table for tracking ingestion status
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    async with pool.acquire() as conn:
        await conn.execute(schema_sql)
        logger.info("Database schema created/verified")


async def execute(query: str, *args) -> str:
    """
    Execute a query that doesn't return results (INSERT, UPDATE, DELETE).
    
    Args:
        query: SQL query string
        *args: Query parameters
    
    Returns:
        Status string from database
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(query, *args)
        return result


async def fetch(query: str, *args) -> List[asyncpg.Record]:
    """
    Execute a query and fetch all results.
    
    Args:
        query: SQL query string
        *args: Query parameters
    
    Returns:
        List of records
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        results = await conn.fetch(query, *args)
        return results


async def fetchrow(query: str, *args) -> Optional[asyncpg.Record]:
    """
    Execute a query and fetch a single row.
    
    Args:
        query: SQL query string
        *args: Query parameters
    
    Returns:
        Single record or None
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(query, *args)
        return result


async def fetchval(query: str, *args) -> Any:
    """
    Execute a query and fetch a single value.
    
    Args:
        query: SQL query string
        *args: Query parameters
    
    Returns:
        Single value or None
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval(query, *args)
        return result


async def bulk_insert_queries(queries_data: List[tuple]) -> int:
    """
    Bulk insert queries using COPY for performance.
    
    Args:
        queries_data: List of (query, count) tuples
    
    Returns:
        Number of rows inserted
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Use COPY for fast bulk insert
        result = await conn.copy_records_to_table(
            'queries',
            records=queries_data,
            columns=['query', 'total_count']
        )
        return len(queries_data)
