# Scripts — Dataset Preparation & Testing

## Dataset Preparation (Phase 2)

### Step 1: Download Amazon Product Dataset

Download the dataset from Kaggle and place files in the `dataset/` directory:
- `dataset/amazon_products.csv` (1.4M rows, ~345MB)
- `dataset/amazon_categories.csv` (270 rows)

**Note:** The `dataset/` folder is ignored by git due to large file size.

### Step 2: Run Cleaning Script

```bash
# From project root
python scripts/clean.py \
  --products dataset/amazon_products.csv \
  --categories dataset/amazon_categories.csv \
  --output data/dataset.csv \
  --sample 200000
```

**Output:** `data/dataset.csv` (200K rows, ~20-30MB) — this file will be committed to git.

### Step 3: Verify Cleaned Dataset

```bash
# Check file exists
ls -lh data/dataset.csv

# Check row count
wc -l data/dataset.csv
# Should show: 200001 (200K rows + 1 header)

# Peek at data
head data/dataset.csv
```

### Step 4: Start Docker Compose

```bash
docker compose up
```

The backend will automatically:
1. Create database schema
2. Check if data is loaded
3. If not loaded → run `ingest.py` → load 200K rows
4. Mark ingestion as complete
5. On subsequent restarts → skip ingestion

## Ingestion Script (Automatic)

**`ingest.py`** — Bulk loads `data/dataset.csv` into PostgreSQL

Called automatically by backend on startup. Can also be run manually:

```bash
python scripts/ingest.py \
  "postgresql://typeahead_user:typeahead_pass@localhost:5432/typeahead" \
  data/dataset.csv
```

## Clean Script Details

**`clean.py`** — Cleans raw Amazon dataset

### What it does:
1. Loads products and categories
2. Derives `search_count` from:
   - Reviews (60% weight)
   - Stars (20% weight)
   - isBestSeller flag (20% weight)
3. Cleans titles (lowercase, strip, remove extra spaces)
4. Deduplicates (keeps highest count)
5. Stratified sampling by category (ensures diversity)
6. Caps count at 1M, floors at 1
7. Outputs top 200K queries by count

### Count Formula:
```python
search_count = (reviews × 0.6) + (stars × 10 × 0.2) + (isBestSeller × 500 × 0.2)
search_count = max(1, min(search_count, 1_000_000))
```

### Output Format:
```csv
query,count
iphone 15 pro max,250000
samsung galaxy s24,180000
macbook pro,150000
...
```

## Troubleshooting

### Dataset not found
```
❌ Error: Products file not found: dataset/amazon_products.csv
```

**Solution:** Download the dataset and place in `dataset/` folder.

### Pandas not installed
```
ModuleNotFoundError: No module named 'pandas'
```

**Solution:** Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Ingestion fails on startup
```
FileNotFoundError: Dataset not found: data/dataset.csv
```

**Solution:** Run `clean.py` first to generate `data/dataset.csv`.

### Ingestion runs every time
```
Ingestion running on every restart...
```

**Check meta table:**
```sql
SELECT * FROM meta WHERE key = 'ingestion_status';
```

Should return `'complete'`. If not, ingestion crashed before completion.

**Reset:**
```bash
docker compose down -v  # Removes volumes
docker compose up       # Fresh start
```
