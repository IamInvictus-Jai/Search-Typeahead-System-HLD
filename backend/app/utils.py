"""
Utility functions used across the application.
CRITICAL: normalize_prefix must be used consistently everywhere.
"""

from app.config import settings


def normalize_prefix(prefix: str) -> str:
    """
    Normalize a search prefix for consistent cache/DB operations.
    
    This function MUST be used everywhere:
    - Cache key generation
    - PostgreSQL LIKE queries
    - Cache invalidation
    - Debug API
    
    Args:
        prefix: Raw prefix from user input
    
    Returns:
        Normalized prefix (lowercase, stripped, max length capped)
    """
    if not prefix:
        return ""
    
    # Strip whitespace, convert to lowercase, cap at max length
    normalized = prefix.strip().lower()[:settings.cache_prefix_max_len]
    
    return normalized
