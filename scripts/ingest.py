"""
Bulk data ingestion script.
Called by backend on startup if ingestion not complete.

Reads data/dataset.csv and bulk loads into PostgreSQL.
"""

import asyncio
import asyncpg
import csv
import sys
from pathlib import Path


async def ingest_dataset(dsn: str, dataset_path: str):
    """
    Bulk load dataset into PostgreSQL using COPY.
    
    Args:
        dsn: PostgreSQL connection string
        dataset_path: Path to dataset.csv
    """
    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    print(f"Connecting to database...")
    conn = await asyncpg.connect(dsn)
    
    try:
        # Read CSV
        print(f"Reading dataset from {dataset_path}...")
        with open(dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = [(row['query'], int(row['count'])) for row in reader]
        
        print(f"Loaded {len(records):,} records from CSV")
        
        # Bulk insert using COPY
        print("Bulk inserting into PostgreSQL...")
        await conn.copy_records_to_table(
            'queries',
            records=records,
            columns=['query', 'total_count']
        )
        
        print(f"✅ Successfully inserted {len(records):,} queries")
        
        return len(records)
    
    finally:
        await conn.close()


async def main():
    if len(sys.argv) < 3:
        print("Usage: python ingest.py <postgres_dsn> <dataset_path>")
        sys.exit(1)
    
    dsn = sys.argv[1]
    dataset_path = sys.argv[2]
    
    try:
        count = await ingest_dataset(dsn, dataset_path)
        print(f"\n✅ Ingestion complete: {count:,} rows loaded")
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
