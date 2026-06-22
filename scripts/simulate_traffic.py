#!/usr/bin/env python3
"""
Traffic simulation script for performance testing.

Simulates realistic user behavior:
- Random prefix queries (suggest API)
- Random search submissions (search API)
- Warmup phase to populate cache
- Sustained traffic for metrics capture

Usage:
    python scripts/simulate_traffic.py --queries 500
    python scripts/simulate_traffic.py --queries 1000 --warmup 100
"""

import argparse
import asyncio
import random
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp
from typing import List


API_BASE_URL = "http://localhost:8000"

# Common search prefixes for realistic traffic
COMMON_PREFIXES = [
    "iphone", "samsung", "wireless", "laptop", "phone", "headphones",
    "keyboard", "mouse", "monitor", "camera", "tablet", "watch",
    "speaker", "charger", "cable", "case", "screen", "battery",
    "gaming", "computer", "desk", "chair", "light", "fan",
    "usb", "bluetooth", "wifi", "smart", "portable", "mini",
    "pro", "plus", "air", "ultra", "max", "lite",
    "black", "white", "blue", "red", "silver", "gold",
    "apple", "sony", "lg", "dell", "hp", "asus",
    "amazon", "kindle", "echo", "fire", "alexa", "google",
    "home", "office", "outdoor", "travel", "sport", "fitness"
]


async def fetch_suggestions(session: aiohttp.ClientSession, prefix: str) -> dict:
    """
    Fetch suggestions for a prefix.
    
    Args:
        session: aiohttp session
        prefix: Search prefix
    
    Returns:
        Response dict with suggestions
    """
    try:
        async with session.get(f"{API_BASE_URL}/suggest", params={"q": prefix}) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"ERROR: GET /suggest?q={prefix} returned {response.status}")
                return []
    except Exception as e:
        print(f"ERROR: Failed to fetch suggestions for '{prefix}': {e}")
        return []


async def submit_search(session: aiohttp.ClientSession, query: str) -> dict:
    """
    Submit a search query.
    
    Args:
        session: aiohttp session
        query: Search query
    
    Returns:
        Response dict
    """
    try:
        async with session.post(
            f"{API_BASE_URL}/search",
            json={"query": query}
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"ERROR: POST /search returned {response.status}")
                return {}
    except Exception as e:
        print(f"ERROR: Failed to submit search for '{query}': {e}")
        return {}


async def simulate_user_session(session: aiohttp.ClientSession, session_id: int):
    """
    Simulate a single user session.
    
    A realistic session:
    1. Types a prefix (fetches suggestions)
    2. Maybe types more characters (more suggestions)
    3. Submits a search
    
    Args:
        session: aiohttp session
        session_id: User session ID for logging
    """
    # Pick a random base prefix
    base_prefix = random.choice(COMMON_PREFIXES)
    
    # Simulate typing by querying progressively longer prefixes
    # (60% chance of typing 2-3 characters, 40% chance of full prefix)
    if random.random() < 0.6:
        # Partial typing (2-3 chars)
        prefix_len = min(random.randint(2, 3), len(base_prefix))
        prefix = base_prefix[:prefix_len]
    else:
        # Full prefix
        prefix = base_prefix
    
    # Fetch suggestions
    suggestions = await fetch_suggestions(session, prefix)
    
    # Small delay (simulating user reading suggestions)
    await asyncio.sleep(random.uniform(0.05, 0.15))
    
    # 70% chance of submitting a search
    if random.random() < 0.7:
        if suggestions and len(suggestions) > 0:
            # 60% pick from suggestions, 40% use typed prefix
            if random.random() < 0.6 and len(suggestions) > 0:
                selected = random.choice(suggestions)
                query = selected.get("query", prefix)
            else:
                query = prefix
        else:
            query = prefix
        
        # Submit search
        await submit_search(session, query)


async def warmup_cache(session: aiohttp.ClientSession, num_requests: int):
    """
    Warmup phase to populate cache.
    
    Args:
        session: aiohttp session
        num_requests: Number of warmup requests
    """
    print(f"\n🔥 Warmup phase: {num_requests} requests...")
    
    start_time = time.time()
    
    # Create tasks for parallel requests
    tasks = [
        simulate_user_session(session, i)
        for i in range(num_requests)
    ]
    
    # Execute with limited concurrency (max 50 at once)
    for i in range(0, len(tasks), 50):
        batch = tasks[i:i+50]
        await asyncio.gather(*batch)
        
        # Progress indicator
        completed = min(i + 50, len(tasks))
        print(f"  Completed {completed}/{num_requests} warmup requests...")
    
    elapsed = time.time() - start_time
    print(f"✅ Warmup complete in {elapsed:.2f}s")


async def run_traffic_simulation(num_queries: int, warmup_requests: int = 0):
    """
    Run traffic simulation.
    
    Args:
        num_queries: Total number of query sessions to simulate
        warmup_requests: Number of warmup requests before main test
    """
    print("=" * 70)
    print("Search Typeahead System - Traffic Simulation")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        # Health check
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status != 200:
                    print(f"ERROR: Backend not healthy (status {response.status})")
                    return
                print("✅ Backend health check passed")
        except Exception as e:
            print(f"ERROR: Cannot connect to backend at {API_BASE_URL}")
            print(f"       Make sure `docker compose up` is running")
            print(f"       Error: {e}")
            return
        
        # Warmup phase (optional)
        if warmup_requests > 0:
            await warmup_cache(session, warmup_requests)
            
            # Wait for flush
            print("\n⏳ Waiting 12 seconds for batch flush...")
            await asyncio.sleep(12)
        
        # Main traffic simulation
        print(f"\n🚀 Main traffic simulation: {num_queries} user sessions...")
        print(f"   (Each session: suggest query → maybe submit search)")
        
        start_time = time.time()
        
        # Create tasks for parallel requests
        tasks = [
            simulate_user_session(session, i)
            for i in range(num_queries)
        ]
        
        # Execute with limited concurrency (max 50 at once)
        completed = 0
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            await asyncio.gather(*batch)
            
            completed = min(i + 50, len(tasks))
            if completed % 100 == 0 or completed == num_queries:
                print(f"  Completed {completed}/{num_queries} sessions...")
        
        elapsed = time.time() - start_time
        requests_per_sec = num_queries / elapsed if elapsed > 0 else 0
        
        print(f"\n✅ Traffic simulation complete")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Throughput: {requests_per_sec:.2f} sessions/sec")
        
        # Wait for final flush
        print("\n⏳ Waiting 12 seconds for final batch flush...")
        await asyncio.sleep(12)
        
        # Fetch and display metrics
        print("\n" + "=" * 70)
        print("Performance Metrics")
        print("=" * 70)
        
        try:
            async with session.get(f"{API_BASE_URL}/metrics") as response:
                if response.status == 200:
                    metrics = await response.json()
                    
                    print(f"\n📊 Cache Performance:")
                    print(f"   Cache Hits: {metrics.get('cache_hits', 0):,}")
                    print(f"   Cache Misses: {metrics.get('cache_misses', 0):,}")
                    print(f"   Hit Rate: {metrics.get('cache_hit_rate_pct', 0):.2f}%")
                    
                    print(f"\n💾 Database Operations:")
                    print(f"   DB Reads: {metrics.get('db_reads', 0):,}")
                    print(f"   DB Writes: {metrics.get('db_writes', 0):,}")
                    
                    print(f"\n🔍 Search Metrics:")
                    print(f"   Total Searches: {metrics.get('total_searches', 0):,}")
                    print(f"   Write Reduction: {metrics.get('write_reduction_pct', 0):.2f}%")
                    
                    print(f"\n⚡ Latency (ms):")
                    print(f"   p50: {metrics.get('latency_p50_ms', 0):.2f}ms")
                    print(f"   p95: {metrics.get('latency_p95_ms', 0):.2f}ms")
                    print(f"   p99: {metrics.get('latency_p99_ms', 0):.2f}ms")
                    print(f"   Cache Hit p95: {metrics.get('latency_cache_hit_p95_ms', 0):.2f}ms")
                    print(f"   Cache Miss p95: {metrics.get('latency_cache_miss_p95_ms', 0):.2f}ms")
                    
                    print(f"\n📈 Samples:")
                    print(f"   Latency Samples: {metrics.get('latency_samples', 0):,}")
                    
                    # Validation checks
                    print("\n" + "=" * 70)
                    print("Performance Validation")
                    print("=" * 70)
                    
                    hit_rate = metrics.get('cache_hit_rate_pct', 0)
                    p95 = metrics.get('latency_p95_ms', 0)
                    write_reduction = metrics.get('write_reduction_pct', 0)
                    
                    checks = [
                        ("Cache Hit Rate > 90%", hit_rate > 90, f"{hit_rate:.2f}%"),
                        ("p95 Latency < 50ms", p95 < 50, f"{p95:.2f}ms"),
                        ("Write Reduction > 95%", write_reduction > 95, f"{write_reduction:.2f}%"),
                    ]
                    
                    for check_name, passed, value in checks:
                        status = "✅ PASS" if passed else "❌ FAIL"
                        print(f"   {status}: {check_name} ({value})")
                    
                    print("\n✅ Metrics captured successfully")
                    print(f"\nView full metrics: curl {API_BASE_URL}/metrics | jq")
                    
                else:
                    print(f"ERROR: Failed to fetch metrics (status {response.status})")
        
        except Exception as e:
            print(f"ERROR: Failed to fetch metrics: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Simulate traffic for Search Typeahead System"
    )
    parser.add_argument(
        "--queries",
        type=int,
        default=500,
        help="Number of user sessions to simulate (default: 500)"
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=0,
        help="Number of warmup requests before main test (default: 0)"
    )
    
    args = parser.parse_args()
    
    # Run simulation
    asyncio.run(run_traffic_simulation(args.queries, args.warmup))


if __name__ == "__main__":
    main()
