"""
Metrics collection and aggregation for performance monitoring.
Tracks cache hits/misses, DB operations, latencies, and write reduction.
"""

from typing import List, Dict
from collections import deque
import time
import statistics
from app.logger import logger


class MetricsCollector:
    """
    Singleton metrics collector.
    Stores performance data in memory for /metrics endpoint.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Database metrics
        self.db_reads = 0
        self.db_writes = 0
        
        # Search metrics
        self.total_searches = 0
        
        # Latency tracking (store last 1000 samples)
        self.latencies = deque(maxlen=1000)
        self.cache_hit_latencies = deque(maxlen=1000)
        self.cache_miss_latencies = deque(maxlen=1000)
        
        self._initialized = True
        logger.info("MetricsCollector initialized")
    
    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss and corresponding DB read."""
        self.cache_misses += 1
        self.db_reads += 1
    
    def record_db_write(self, count: int = 1):
        """
        Record database write operations.
        
        Args:
            count: Number of queries written in batch
        """
        self.db_writes += count
    
    def record_search(self):
        """Record a search submission."""
        self.total_searches += 1
    
    def record_latency(self, latency_ms: float, cache_hit: bool = None):
        """
        Record request latency.
        
        Args:
            latency_ms: Request latency in milliseconds
            cache_hit: True if cache hit, False if miss, None if unknown
        """
        self.latencies.append(latency_ms)
        
        if cache_hit is True:
            self.cache_hit_latencies.append(latency_ms)
        elif cache_hit is False:
            self.cache_miss_latencies.append(latency_ms)
    
    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate percentage.
        
        Returns:
            Hit rate as percentage (0-100)
        """
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100
    
    def get_write_reduction(self) -> float:
        """
        Calculate write reduction percentage.
        Formula: (1 - db_writes / total_searches) * 100
        
        Returns:
            Write reduction as percentage (0-100)
        """
        if self.total_searches == 0:
            return 0.0
        return (1 - (self.db_writes / self.total_searches)) * 100
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """
        Calculate percentile from sorted data.
        
        Args:
            data: List of numeric values
            percentile: Percentile to calculate (0-100)
        
        Returns:
            Percentile value, or 0.0 if no data
        """
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def get_latency_stats(self) -> Dict[str, float]:
        """
        Calculate latency percentiles.
        
        Returns:
            Dictionary with p50, p95, p99 latencies in ms
        """
        if not self.latencies:
            return {
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
            }
        
        latencies_list = list(self.latencies)
        
        return {
            "p50_ms": round(self._percentile(latencies_list, 50), 2),
            "p95_ms": round(self._percentile(latencies_list, 95), 2),
            "p99_ms": round(self._percentile(latencies_list, 99), 2),
        }
    
    def get_cache_latency_stats(self) -> Dict[str, float]:
        """
        Calculate cache hit/miss latency percentiles.
        
        Returns:
            Dictionary with cache hit and miss p95 latencies
        """
        hit_p95 = 0.0
        miss_p95 = 0.0
        
        if self.cache_hit_latencies:
            hit_p95 = round(self._percentile(list(self.cache_hit_latencies), 95), 2)
        
        if self.cache_miss_latencies:
            miss_p95 = round(self._percentile(list(self.cache_miss_latencies), 95), 2)
        
        return {
            "cache_hit_p95_ms": hit_p95,
            "cache_miss_p95_ms": miss_p95,
        }
    
    def get_snapshot(self) -> Dict:
        """
        Get complete metrics snapshot.
        
        Returns:
            Dictionary with all metrics
        """
        latency_stats = self.get_latency_stats()
        cache_latency_stats = self.get_cache_latency_stats()
        
        return {
            # Cache metrics
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate_pct": round(self.get_cache_hit_rate(), 2),
            
            # Database metrics
            "db_reads": self.db_reads,
            "db_writes": self.db_writes,
            
            # Search metrics
            "total_searches": self.total_searches,
            "write_reduction_pct": round(self.get_write_reduction(), 2),
            
            # Latency metrics
            "latency_p50_ms": latency_stats["p50_ms"],
            "latency_p95_ms": latency_stats["p95_ms"],
            "latency_p99_ms": latency_stats["p99_ms"],
            "latency_cache_hit_p95_ms": cache_latency_stats["cache_hit_p95_ms"],
            "latency_cache_miss_p95_ms": cache_latency_stats["cache_miss_p95_ms"],
            
            # Sample counts
            "latency_samples": len(self.latencies),
            "cache_hit_samples": len(self.cache_hit_latencies),
            "cache_miss_samples": len(self.cache_miss_latencies),
        }
    
    def reset(self):
        """Reset all metrics (useful for testing)."""
        self.cache_hits = 0
        self.cache_misses = 0
        self.db_reads = 0
        self.db_writes = 0
        self.total_searches = 0
        self.latencies.clear()
        self.cache_hit_latencies.clear()
        self.cache_miss_latencies.clear()
        logger.info("Metrics reset")


# Global singleton instance
metrics = MetricsCollector()
