"""
Dataset cleaning script - Run once offline before Docker deployment.

Reads raw Amazon Product Dataset, derives search counts, cleans, and samples.
Output: data/dataset.csv (200K rows, ~20-30MB)

Usage:
    python scripts/clean.py --products dataset/amazon_products.csv \
                            --categories dataset/amazon_categories.csv \
                            --output data/dataset.csv \
                            --sample 200000
"""

import pandas as pd
import argparse
import sys
from pathlib import Path


def derive_search_count(row) -> int:
    """
    Derive search count from available signals.
    
    Formula: (reviews × 0.6) + (stars × 10 × 0.2) + (isBestSeller × 500 × 0.2)
    
    Args:
        row: DataFrame row with reviews, stars, isBestSeller columns
    
    Returns:
        Derived search count (capped between 1 and 1,000,000)
    """
    reviews = row.get('reviews', 0) or 0
    stars = row.get('stars', 0) or 0
    is_best_seller = 1 if row.get('isBestSeller', False) else 0
    
    count = (reviews * 0.6) + (stars * 10 * 0.2) + (is_best_seller * 500 * 0.2)
    
    # Floor at 1, cap at 1M
    count = max(1, min(int(count), 1_000_000))
    
    return count


def clean_dataset(products_path: str, categories_path: str, output_path: str, sample_size: int = 200000):
    """
    Clean and sample the Amazon Product Dataset.
    
    Steps:
    1. Load products and categories
    2. Drop rows with null/empty titles
    3. Derive search_count
    4. Clean and normalize titles
    5. Deduplicate (keep highest count)
    6. Stratified sampling by category
    7. Save to output
    
    Args:
        products_path: Path to amazon_products.csv
        categories_path: Path to amazon_categories.csv
        output_path: Path to save cleaned dataset
        sample_size: Target number of rows (default 200K)
    """
    print(f"Loading products from {products_path}...")
    products = pd.read_csv(products_path)
    print(f"Loaded {len(products):,} products")
    
    print(f"Loading categories from {categories_path}...")
    categories = pd.read_csv(categories_path)
    print(f"Loaded {len(categories):,} categories")
    
    # Merge with categories (optional, for stratified sampling)
    if 'category_id' in products.columns and 'category_id' in categories.columns:
        products = products.merge(categories, on='category_id', how='left')
        print("Merged with categories")
    
    # Drop rows with null or empty titles
    print("Cleaning titles...")
    products = products.dropna(subset=['title'])
    products = products[products['title'].str.strip() != '']
    print(f"After dropping empty titles: {len(products):,} rows")
    
    # Derive search_count
    print("Deriving search counts...")
    products['search_count'] = products.apply(derive_search_count, axis=1)
    
    # Clean titles: strip, lowercase, remove extra whitespace
    products['query'] = products['title'].str.strip().str.lower()
    products['query'] = products['query'].str.replace(r'\s+', ' ', regex=True)
    
    # Drop duplicates, keep highest count
    print("Deduplicating queries...")
    products = products.sort_values('search_count', ascending=False)
    products = products.drop_duplicates(subset=['query'], keep='first')
    print(f"After deduplication: {len(products):,} unique queries")
    
    # Select only needed columns
    dataset = products[['query', 'search_count']].copy()
    dataset.columns = ['query', 'count']
    
    # Stratified sampling by category (if available)
    if 'category_id' in products.columns and len(dataset) > sample_size:
        print(f"Stratified sampling to {sample_size:,} rows...")
        
        # Calculate samples per category proportionally
        category_counts = products['category_id'].value_counts()
        samples_per_category = (category_counts / len(products) * sample_size).astype(int)
        
        sampled_dfs = []
        for category, n_samples in samples_per_category.items():
            category_data = products[products['category_id'] == category]
            n_samples = min(n_samples, len(category_data))
            
            if n_samples > 0:
                # Take top N by search_count for this category
                sampled = category_data.nlargest(n_samples, 'search_count')
                sampled_dfs.append(sampled[['query', 'search_count']])
        
        dataset = pd.concat(sampled_dfs, ignore_index=True)
        dataset.columns = ['query', 'count']
        
        # If we're short of target, add more from top overall
        if len(dataset) < sample_size:
            remaining = sample_size - len(dataset)
            additional = products[~products['query'].isin(dataset['query'])]
            additional = additional.nlargest(remaining, 'search_count')
            additional_df = additional[['query', 'search_count']].copy()
            additional_df.columns = ['query', 'count']
            dataset = pd.concat([dataset, additional_df], ignore_index=True)
    
    elif len(dataset) > sample_size:
        # Simple sampling if no categories
        print(f"Sampling top {sample_size:,} rows by count...")
        dataset = dataset.nlargest(sample_size, 'count')
    
    # Final sort by count descending
    dataset = dataset.sort_values('count', ascending=False).reset_index(drop=True)
    
    # Save to output
    print(f"Saving to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False)
    
    print(f"\n✅ Dataset cleaning complete!")
    print(f"   Output: {output_path}")
    print(f"   Rows: {len(dataset):,}")
    print(f"   Columns: {list(dataset.columns)}")
    print(f"   File size: {Path(output_path).stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   Count range: {dataset['count'].min():,} - {dataset['count'].max():,}")


def main():
    parser = argparse.ArgumentParser(description='Clean Amazon Product Dataset for typeahead system')
    parser.add_argument('--products', type=str, default='dataset/amazon_products.csv',
                        help='Path to amazon_products.csv')
    parser.add_argument('--categories', type=str, default='dataset/amazon_categories.csv',
                        help='Path to amazon_categories.csv')
    parser.add_argument('--output', type=str, default='data/dataset.csv',
                        help='Output path for cleaned dataset')
    parser.add_argument('--sample', type=int, default=200000,
                        help='Target sample size (default: 200,000)')
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not Path(args.products).exists():
        print(f"❌ Error: Products file not found: {args.products}")
        print("   Please download the Amazon Product Dataset and place it in the dataset/ folder")
        sys.exit(1)
    
    if not Path(args.categories).exists():
        print(f"❌ Error: Categories file not found: {args.categories}")
        print("   Please download the Amazon Product Dataset and place it in the dataset/ folder")
        sys.exit(1)
    
    try:
        clean_dataset(args.products, args.categories, args.output, args.sample)
    except Exception as e:
        print(f"\n❌ Error during cleaning: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
