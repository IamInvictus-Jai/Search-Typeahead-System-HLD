# Search Typeahead System — HLD Assignment

A production-grade search typeahead system with distributed caching, batch writes, and recency-aware trending search ranking.

## 🎯 Features

- **Typeahead Suggestions:** Top 10 prefix-matching queries sorted by popularity
- **Distributed Cache:** Custom consistent hashing with 5 Redis nodes
- **Batch Writes:** Double-buffer pattern reduces DB writes by >95%
- **Trending Searches:** Recency-aware scoring using hourly time buckets
- **Debug API:** Demonstrates consistent hashing distribution
- **Performance Metrics:** p95 latency < 50ms, cache hit rate > 90%

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 + Uvicorn |
| Database | PostgreSQL 15 |
| Cache | Redis 7 (5 cache nodes + 1 queue) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Orchestration | Docker Compose |

## 📊 Dataset

- **Source:** Amazon Product Dataset (Kaggle)
- **Size:** 200,000 cleaned queries
- **Location:** `data/dataset.csv` (committed)
- **Derived count:** `(reviews × 0.6) + (stars × 10 × 0.2) + (isBestSeller × 500 × 0.2)`

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (with Docker Compose)
- 4GB RAM minimum
- 2GB disk space

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

The system will:
- Start PostgreSQL, 6 Redis containers, backend, and frontend
- Automatically load 200K queries into the database (first run only)
- Serve frontend at http://localhost:5173
- Serve backend API at http://localhost:8000

### Verify Installation

```bash
# Check all services are running
docker compose ps

# Test backend health
curl http://localhost:8000/health

# Test suggestions API
curl "http://localhost:8000/suggest?q=iphone"

# Test cache debug API
curl "http://localhost:8000/cache/debug?prefix=iphone"
```

## 📚 API Documentation

### GET /suggest

Returns typeahead suggestions for a given prefix.

**Request:**
```bash
curl "http://localhost:8000/suggest?q=iphone"
```

**Response:**
```json
[
  {"query": "iphone 15 pro", "score": 95000.0},
  {"query": "iphone charger", "score": 72000.0},
  {"query": "iphone case", "score": 68000.0}
]
```

### POST /search

Submit a search query (records and updates counts).

**Request:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "iphone 15"}'
```

**Response:**
```json
{"message": "Searched"}
```

### GET /cache/debug

Debug cache routing and consistent hashing.

**Request:**
```bash
curl "http://localhost:8000/cache/debug?prefix=iphone"
```

**Response:**
```json
{
  "prefix": "iphone",
  "cache_key": "suggest:iphone",
  "node": "redis-node-2",
  "node_port": 6380,
  "status": "hit",
  "ttl_remaining": 243,
  "result_count": 10
}
```

### GET /metrics

Performance metrics snapshot.

**Request:**
```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "cache_hits": 8423,
  "cache_misses": 312,
  "cache_hit_rate_pct": 96.4,
  "db_reads": 312,
  "total_searches": 5000,
  "db_writes": 48,
  "write_reduction_pct": 99.04,
  "latency_p50_ms": 3.2,
  "latency_p95_ms": 11.4
}
```

## 🏗 Architecture

```
┌─────────────┐
│   Browser   │
│  (React UI) │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────┐
│   FastAPI Backend       │
│  • Consistent Hashing   │
│  • Double-Buffer Batch  │
│  • Trending Scoring     │
└───┬─────────────┬───────┘
    │             │
    ▼             ▼
┌──────────┐  ┌────────────────────┐
│PostgreSQL│  │   Redis Layer      │
│  Queries │  │  • 5 Cache Nodes   │
│  Recent  │  │  • 1 Queue (WAL)   │
└──────────┘  └────────────────────┘
```

## 🎯 Design Highlights

### Consistent Hashing
- **Custom implementation** (no libraries)
- 150 virtual nodes per physical node
- Ensures uniform key distribution
- Minimizes remapping on topology changes

### Double-Buffer Batch Writes
- In-memory buffering with async lock
- Flush triggers: 10s interval or 100 entries
- Redis List as Write-Ahead Log (WAL)
- >95% write reduction

### Trending Score Formula
```
score = total_count + (recent_count_last_24h × 0.3)
```
- Combines historical popularity with recent activity
- Hourly time buckets prevent unbounded storage
- Recent queries rank higher than old ones

### Cache Invalidation
- Invalidates after successful DB write (not before)
- Uses `dirty_prefixes` set for deduplication
- Groups by node for bulk delete (fewer round trips)

## 📈 Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Cache Hit Rate | >90% | TBD* |
| p95 Latency | <50ms | TBD* |
| Write Reduction | >95% | TBD* |
| Dataset Size | 200K | 200K ✅ |

*Run `python scripts/simulate_traffic.py --queries 500` to populate metrics

## 🧪 Testing

### Run Traffic Simulation
```bash
# Warm up cache and generate metrics
python scripts/simulate_traffic.py --queries 500

# Capture metrics
curl http://localhost:8000/metrics | jq .
```

### Manual Testing
1. Open http://localhost:5173 in browser
2. Type "iphone" in search box
3. Suggestions appear after 300ms debounce
4. Press Enter or click suggestion to submit search
5. Check trending section for popular queries

## 📁 Project Structure

```
Assignment/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, routes
│   │   ├── config.py         # Environment config
│   │   ├── hashing.py        # Consistent hashing
│   │   ├── cache.py          # Redis operations
│   │   ├── batch.py          # Double-buffer + WAL
│   │   ├── trending.py       # Recency scoring
│   │   ├── db.py             # Database queries
│   │   └── metrics.py        # Performance tracking
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── hooks/
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   ├── clean.py              # Dataset cleaning
│   ├── ingest.py             # Bulk loader
│   └── simulate_traffic.py  # Load testing
├── data/
│   └── dataset.csv           # 200K cleaned queries
├── docs/
│   ├── PRD.md
│   ├── Notes.md
│   ├── Report.md
│   └── IMPLEMENTATION_PLAN.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker compose logs backend

# Verify PostgreSQL is healthy
docker compose ps postgres

# Ensure .env exists
cp .env.example .env
```

### Frontend Can't Connect
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS settings in backend/app/main.py
# Should allow http://localhost:5173
```

### Cache Always Misses
```bash
# Check Redis nodes are running
docker compose ps | grep redis

# Verify consistent hashing
curl "http://localhost:8000/cache/debug?prefix=test"
```

### Ingestion Fails
```bash
# Check dataset exists
ls -lh data/dataset.csv

# Check PostgreSQL logs
docker compose logs postgres

# Reset database
docker compose down -v
docker compose up
```

## 📖 Documentation

- **PRD:** `docs/PRD.md` — Complete product requirements
- **Notes:** `docs/Notes.md` — Viva preparation, design Q&A
- **Report:** `docs/Report.md` — Architecture, performance metrics
- **Implementation Plan:** `docs/IMPLEMENTATION_PLAN.md` — 8-phase roadmap

## 🎓 Assignment Context

- **Course:** HLD (High-Level Design)
- **Grading:** 100 marks (60 basic + 20 trending + 20 batch writes)
- **Focus:** Backend data-system design, caching, write optimization

## 📝 License

This is an academic assignment project.

## 👤 Author

Amritesh Indal
