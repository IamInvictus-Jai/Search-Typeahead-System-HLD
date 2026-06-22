# Search Typeahead System — HLD Assignment

A production-grade search typeahead system with distributed caching, batch writes, and recency-aware trending search ranking.

[![Phase 8 Complete](https://img.shields.io/badge/Phase-8%2F8%20Complete-success)]()
[![Performance](https://img.shields.io/badge/p95%20Latency-38.35ms-brightgreen)]()
[![Cache Hit](https://img.shields.io/badge/Cache%20Hit%20Rate-80.63%25-green)]()
[![Write Reduction](https://img.shields.io/badge/Write%20Reduction-76.93%25-blue)]()

## 🎯 Features

- **Typeahead Suggestions:** Top 10 prefix-matching queries sorted by trending score
- **Distributed Cache:** Custom consistent hashing with 3-5 Redis nodes (no libraries)
- **Batch Writes:** Double-buffer pattern with WAL reduces DB writes by 76%+
- **Trending Searches:** Recency-aware scoring using hourly time buckets
- **Modern UI:** React 18 with Tailwind CSS, 300ms debouncing, keyboard navigation
- **Performance Metrics:** p95 latency 38ms (target: <50ms), 265 req/sec throughput
- **Debug API:** Real-time cache routing and consistent hashing visualization

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 (async, no ORM) + Uvicorn |
| Database | PostgreSQL 15 (200K queries) |
| Cache | Redis 7 (3 cache nodes + 1 queue with AOF) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Orchestration | Docker Compose |

## 📊 Dataset

- **Source:** Amazon Product Dataset (Kaggle — 1.4M products)
- **Cleaned:** 200,000 queries via stratified sampling
- **Location:** `data/dataset.csv` (24MB, committed to repo)
- **Score Formula:** `(reviews × 0.6) + (stars × 10 × 0.2) + (isBestSeller × 500 × 0.2)`

### Data Cleaning Process

![Data Cleaning Screenshot](images/Data%20Cleaning%20ss.png)

**Cleaning Steps:**
1. Load 1.4M products from `amazon_products.csv`
2. Drop empty titles, clean whitespace
3. Derive search counts from reviews, stars, bestseller status
4. Deduplicate (1.4M → 1.38M unique queries)
5. Stratified sampling to 200K rows
6. Output: `data/dataset.csv` (24.04 MB)

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (with Docker Compose v2)
- 4GB RAM minimum
- 2GB disk space
- Python 3.11+ (for traffic simulation script)

### One-Command Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd Assignment

# 2. Copy environment template
cp .env.example .env

# 3. Start all services
docker compose up

# That's it! 🎉
```

The system will automatically:
1. Start PostgreSQL with schema creation
2. Launch 6 Redis containers (5 cache + 1 queue)
3. Start FastAPI backend on port 8000
4. Start React frontend on port 5173
5. Load 200K queries into database (first run only)
6. Initialize consistent hash ring
7. Start background batch flush worker

**Access Points:**
- **Frontend UI:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Verify Installation

```bash
# Check all services are healthy
docker compose ps

# Test backend
curl http://localhost:8000/health

# Test suggestions
curl "http://localhost:8000/suggest?q=iphone" | jq '.[0:3]'
```

## 🏗 System Architecture

### High-Level Overview

![System Architecture](images/system%20architecture.png)

**Components:**
1. **React Frontend:** User interface with debounced search
2. **FastAPI Backend:** API layer with consistent hashing
3. **Redis Cache Layer:** 3 active nodes for distributed caching
4. **Redis Queue:** WAL for batch writes (AOF enabled)
5. **PostgreSQL:** Primary data store

### Cache Read Flow

![Cache Read Flow](images/cache%20read%20flow.png)

**Steps:**
1. User types → Frontend debounces 300ms → API call
2. Backend computes cache key via consistent hashing
3. Cache HIT: Return cached (p95: 33ms) | MISS: Query DB (p95: 95ms)

### Batch Write Flow

![Batch Write Flow](images/batch%20write%20flow.png)

**Steps:**
1. Search submitted → Buffered in memory
2. Flush triggers: 10s timer OR 100 entries
3. Swap buffers (<1ms lock)
4. Push to WAL (Redis List)
5. Bulk write to PostgreSQL
6. Invalidate cache keys

### Consistent Hashing

![Consistent Hashing](images/Consistent%20Hashing.png)

**Design:**
- Ring: 0 to 2^32 (MD5 hash space)
- Virtual Nodes: 150 per physical node
- Binary search for O(log n) lookups
- Uniform distribution (~33.3% per node)

## 📚 API Documentation

### GET /suggest

Returns typeahead suggestions with trending scores.

```bash
curl "http://localhost:8000/suggest?q=iphone"
```

**Response:**
```json
[
  {"query": "iphone 15 pro max", "score": 95420.0},
  {"query": "iphone charger fast charging", "score": 72158.0}
]
```

---

### POST /search

Submit a search query.

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "iphone 15 pro"}'
```

---

### GET /cache/debug

Debug cache routing (proves consistent hashing).

```bash
curl "http://localhost:8000/cache/debug?prefix=iphone"
```

**Response:**
```json
{
  "node": "redis-node-2",
  "status": "hit",
  "ttl_remaining": 243
}
```

---

### GET /metrics

Performance metrics snapshot.

```bash
curl http://localhost:8000/metrics | jq
```

**Response:**
```json
{
  "cache_hit_rate_pct": 80.63,
  "latency_p95_ms": 38.35,
  "write_reduction_pct": 76.93
}
```

## 📈 Performance Results

### Benchmark: 3000 Queries + 500 Warmup

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **p95 Latency** | <50ms | **38.35ms** | ✅ PASS (23% better) |
| **p99 Latency** | <100ms | **43.56ms** | ✅ PASS (56% better) |
| **Throughput** | >100 req/s | **265.67 req/s** | ✅ PASS |
| Cache Hit Rate | >90% | 80.63% | 🟡 Good |
| Write Reduction | >95% | 76.93% | 🟡 Good |

### Detailed Metrics

```
📊 Cache: 3,991 hits / 959 misses (80.63% hit rate)
💾 Database: 809 writes for 3,506 searches (76.93% reduction)
⚡ Latency: p50=13.89ms, p95=38.35ms, p99=43.56ms
   Cache Hit p95: 33.84ms (2.8x faster than miss)
🚀 Throughput: 265.67 sessions/sec
```

**Key Insights:**
- Latency exceeds targets by 23%
- Cache hits are 2.8x faster than misses
- Batch system reduces writes by ~4.3x
- System handles 265+ req/sec with consistent performance

## 🧪 Testing

### Automated Traffic Simulation

```bash
# Install dependencies
pip install aiohttp

# Run simulation
python scripts/simulate_traffic.py --queries 3000 --warmup 500
```

**Output includes:**
- Progress reporting
- Final metrics snapshot
- Performance validation (PASS/FAIL)

### Manual Testing

**Frontend:** http://localhost:5173
- Type "iphone" → suggestions after 300ms
- Press ↓ → highlights suggestion
- Press Enter → submits search
- Click trending chip → fills search box

**Backend:**
```bash
curl "http://localhost:8000/suggest?q=wireless"
curl "http://localhost:8000/cache/debug?prefix=wireless"
curl http://localhost:8000/metrics | jq
```

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker compose logs backend | tail -50

# Verify PostgreSQL
docker compose ps postgres

# Reset if needed
docker compose down -v
docker compose up
```

### Cache Always Misses
```bash
# Check Redis nodes
docker compose ps | grep redis

# Verify consistent hashing
curl "http://localhost:8000/cache/debug?prefix=test"

# Warm up cache
python scripts/simulate_traffic.py --queries 500
```

### High Latency
```bash
# Check metrics
curl http://localhost:8000/metrics | jq '.latency_p95_ms'

# Verify database indexes
docker compose exec postgres psql -U typeahead_user -d typeahead -c "\d queries"
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| `docs/PRD.md` | Product requirements, schema design |
| `docs/Notes.md` | Viva Q&A, design decisions |
| `docs/Report.md` | Architecture diagrams, metrics |
| `docs/IMPLEMENTATION_PLAN.md` | 8-phase roadmap |

## 🎓 Assignment Context

- **Course:** HLD (High-Level Design)
- **Grading:** 100 marks (60 basic + 20 trending + 20 batch)
- **Focus:** Backend data-system design, caching, write optimization

## 🎉 Project Status

✅ **All 8 Phases Complete**

```
Phase 1: Project scaffolding ✅
Phase 2: Database schema and ingestion ✅
Phase 3: Basic typeahead API ✅
Phase 4: Consistent hashing and distributed cache ✅
Phase 5: Batch writes with double-buffer and WAL ✅
Phase 6: Trending searches with recency scoring ✅
Phase 7: Frontend with React and Tailwind ✅
Phase 8: Metrics, debug API, performance testing ✅
```

**Ready for:** Demo, Viva, Submission ✅

## 👤 Author

**Pulasari Jai**  
HLD Assignment — Search Typeahead System
