"""
Redis cache operations with consistent hashing.
"""

import json
from typing import List, Optional, Dict
import redis.asyncio as redis
from app.config import settings
from app.logger import logger
from app.hashing import ConsistentHashRing
from app.utils import normalize_prefix


# Global cache state
_redis_clients: Dict[str, redis.Redis] = {}
_hash_ring: Optional[ConsistentHashRing] = None


async def initialize_cache():
    """
    Initialize Redis clients and consistent hash ring.
    Called on application startup.
    """
    global _redis_clients, _hash_ring
    
    # Create Redis clients for each configured node
    nodes = []
    for i in range(1, settings.num_redis_nodes + 1):
        node_name = f"redis-node-{i}"
        node_config = settings.get_redis_node_config(i)
        
        try:
            client = redis.Redis(
                host=node_config['host'],
                port=node_config['port'],
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Test connection
            await client.ping()
            
            _redis_clients[node_name] = client
            nodes.append(node_name)
            
            logger.info(f"Connected to {node_name} at {node_config['host']}:{node_config['port']}")
        
        except Exception as e:
            logger.error(f"Failed to connect to {node_name}: {e}", exc_info=True)
            raise
    
    # Create consistent hash ring
    _hash_ring = ConsistentHashRing(nodes, replicas=settings.virtual_nodes_per_ring)
    
    logger.info(f"✅ Cache initialized with {len(nodes)} nodes")


async def close_cache():
    """Close all Redis connections."""
    global _redis_clients
    
    for node_name, client in _redis_clients.items():
        await client.close()
        logger.info(f"Closed connection to {node_name}")
    
    _redis_clients = {}


def get_cache_key(prefix: str) -> str:
    """
    Generate cache key for a prefix.
    
    Args:
        prefix: Normalized search prefix
    
    Returns:
        Cache key in format "suggest:{prefix}"
    """
    return f"suggest:{prefix}"


async def get_suggestions_from_cache(prefix: str) -> Optional[List[dict]]:
    """
    Get suggestions from cache for a given prefix.
    
    Args:
        prefix: Normalized search prefix
    
    Returns:
        List of suggestion dicts or None if cache miss
    """
    if not _hash_ring or not _redis_clients:
        logger.warning("Cache not initialized")
        return None
    
    cache_key = get_cache_key(prefix)
    
    # Determine which node owns this key
    node = _hash_ring.get_node(cache_key)
    client = _redis_clients.get(node)
    
    if not client:
        logger.error(f"No client for node {node}")
        return None
    
    try:
        # Get from cache
        cached_value = await client.get(cache_key)
        
        if cached_value:
            logger.info(f"Cache HIT: '{prefix}' on {node}")
            return json.loads(cached_value)
        else:
            logger.info(f"Cache MISS: '{prefix}' on {node}")
            return None
    
    except Exception as e:
        logger.error(f"Cache read error for '{prefix}' on {node}: {e}", exc_info=True)
        return None


async def set_suggestions_in_cache(prefix: str, suggestions: List[dict]):
    """
    Store suggestions in cache for a given prefix.
    
    Args:
        prefix: Normalized search prefix
        suggestions: List of suggestion dicts to cache
    """
    if not _hash_ring or not _redis_clients:
        logger.warning("Cache not initialized")
        return
    
    cache_key = get_cache_key(prefix)
    
    # Determine which node owns this key
    node = _hash_ring.get_node(cache_key)
    client = _redis_clients.get(node)
    
    if not client:
        logger.error(f"No client for node {node}")
        return
    
    try:
        # Store with TTL
        await client.setex(
            cache_key,
            settings.redis_cache_ttl,
            json.dumps(suggestions)
        )
        logger.info(f"Cached '{prefix}' on {node} (TTL: {settings.redis_cache_ttl}s)")
    
    except Exception as e:
        logger.error(f"Cache write error for '{prefix}' on {node}: {e}", exc_info=True)


async def invalidate_cache_keys(prefixes: List[str]):
    """
    Invalidate cache keys for given prefixes.
    Groups by node for efficient bulk deletion.
    
    Args:
        prefixes: List of normalized prefixes to invalidate
    """
    if not _hash_ring or not _redis_clients:
        logger.warning("Cache not initialized")
        return
    
    if not prefixes:
        return
    
    # Group prefixes by target node
    node_to_keys: Dict[str, List[str]] = {}
    
    for prefix in prefixes:
        cache_key = get_cache_key(prefix)
        node = _hash_ring.get_node(cache_key)
        
        if node not in node_to_keys:
            node_to_keys[node] = []
        node_to_keys[node].append(cache_key)
    
    # Bulk delete per node
    for node, keys in node_to_keys.items():
        client = _redis_clients.get(node)
        if not client:
            logger.error(f"No client for node {node}")
            continue
        
        try:
            deleted = await client.delete(*keys)
            logger.info(f"Invalidated {deleted}/{len(keys)} keys on {node}")
        
        except Exception as e:
            logger.error(f"Cache invalidation error on {node}: {e}", exc_info=True)


async def get_cache_debug_info(prefix: str) -> dict:
    """
    Get debug information about cache status for a prefix.
    
    Args:
        prefix: Normalized search prefix
    
    Returns:
        Debug info dictionary
    """
    if not _hash_ring or not _redis_clients:
        return {
            "error": "Cache not initialized",
            "prefix": prefix
        }
    
    cache_key = get_cache_key(prefix)
    node = _hash_ring.get_node(cache_key)
    client = _redis_clients.get(node)
    
    if not client:
        return {
            "error": f"No client for node {node}",
            "prefix": prefix,
            "cache_key": cache_key,
            "node": node
        }
    
    try:
        # Check if key exists and get TTL
        exists = await client.exists(cache_key)
        ttl = await client.ttl(cache_key) if exists else None
        
        # Get result count if cached
        result_count = None
        if exists:
            cached_value = await client.get(cache_key)
            if cached_value:
                results = json.loads(cached_value)
                result_count = len(results)
        
        # Get node config
        node_config = settings.get_redis_node_config(int(node.split('-')[-1]))
        
        return {
            "prefix": prefix,
            "cache_key": cache_key,
            "node": node,
            "node_port": node_config['port'],
            "status": "hit" if exists else "miss",
            "ttl_remaining": ttl if ttl and ttl > 0 else None,
            "result_count": result_count
        }
    
    except Exception as e:
        logger.error(f"Cache debug error for '{prefix}': {e}", exc_info=True)
        return {
            "error": str(e),
            "prefix": prefix,
            "cache_key": cache_key,
            "node": node
        }


def get_ring() -> Optional[ConsistentHashRing]:
    """Get the hash ring instance for external use."""
    return _hash_ring
