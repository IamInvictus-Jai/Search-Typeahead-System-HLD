"""
Startup ingestion logic.
Checks if data is already loaded, runs ingestion if needed.
"""

import asyncio
import subprocess
from pathlib import Path
from app.db import get_pool, fetchval, execute
from app.config import settings
from app.logger import logger


async def check_ingestion_status() -> bool:
    """
    Check if ingestion has already been completed.
    
    Returns:
        True if ingestion is complete, False otherwise
    """
    try:
        status = await fetchval(
            "SELECT value FROM meta WHERE key = 'ingestion_status'"
        )
        return status == 'complete'
    except Exception as e:
        logger.warning(f"Could not check ingestion status: {e}")
        return False


async def mark_ingestion_complete():
    """Mark ingestion as complete in meta table."""
    await execute(
        """
        INSERT INTO meta (key, value) 
        VALUES ('ingestion_status', 'complete')
        ON CONFLICT (key) DO UPDATE 
        SET value = 'complete', updated_at = NOW()
        """
    )
    logger.info("Ingestion status marked as complete")


async def run_ingestion(dataset_path: str = "data/dataset.csv"):
    """
    Run the ingestion script to load data from CSV.
    
    Args:
        dataset_path: Path to dataset.csv relative to app root
    """
    # Verify dataset file exists
    dataset_file = Path(dataset_path)
    if not dataset_file.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}\n"
            f"Please run: python scripts/clean.py\n"
            f"to generate the cleaned dataset first."
        )
    
    logger.info(f"Starting ingestion from {dataset_path}...")
    
    # Run the ingestion script
    cmd = [
        "python",
        "scripts/ingest.py",
        settings.postgres_dsn,
        dataset_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Ingestion output:\n{result.stdout}")
        
        # Mark as complete
        await mark_ingestion_complete()
        
        logger.info("✅ Ingestion completed successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Ingestion failed: {e.stderr}")
        raise RuntimeError(f"Data ingestion failed: {e.stderr}")


async def ensure_data_loaded():
    """
    Ensure data is loaded into database.
    Called on application startup.
    """
    try:
        is_complete = await check_ingestion_status()
        
        if is_complete:
            logger.info("Data already loaded, skipping ingestion")
            
            # Log row count for verification
            count = await fetchval("SELECT COUNT(*) FROM queries")
            logger.info(f"Database contains {count:,} queries")
        else:
            logger.info("No ingestion record found, starting data load...")
            await run_ingestion()
            
            # Verify row count
            count = await fetchval("SELECT COUNT(*) FROM queries")
            logger.info(f"✅ Ingestion complete: {count:,} queries loaded")
    
    except Exception as e:
        logger.error(f"Error during data loading: {e}", exc_info=True)
        raise
