"""Command-line entrypoint for the Walmart retail data pipeline.

This script orchestrates the ETL process by reading the sales data from a
CSV file, merging it with complementary features from a Parquet file,
cleaning and transforming the merged dataset, computing average weekly
sales by month, saving the results to disk and validating that the files
were created successfully.

Example usage:

```bash
python main.py \
  --sales grocery_sales.csv \
  --extra extra_data.parquet \
  --clean-path clean_data.csv \
  --agg-path agg_data.csv
```
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from etl_pipeline import (
    extract,
    transform,
    avg_weekly_sales_per_month,
    load,
    validation,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the pipeline.

    Returns
    -------
    argparse.Namespace
        The parsed arguments with attributes: sales, extra, clean_path,
        agg_path.
    """
    parser = argparse.ArgumentParser(description="Run the Walmart ETL pipeline")
    parser.add_argument(
        "--sales",
        required=True,
        help="Path to the CSV file containing the grocery sales data",
    )
    parser.add_argument(
        "--extra",
        required=True,
        help="Path to the Parquet file containing the complementary data",
    )
    parser.add_argument(
        "--clean-path",
        default="clean_data.csv",
        help="Output path for the cleaned data CSV file",
    )
    parser.add_argument(
        "--agg-path",
        default="agg_data.csv",
        help="Output path for the aggregated data CSV file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Read sales data from CSV
    sales_path = Path(args.sales)
    if not sales_path.exists():
        print(f"❌ Sales file not found: {sales_path}", file=sys.stderr)
        sys.exit(1)
    try:
        store_data = pd.read_csv(sales_path)
    except Exception as exc:
        print(f"❌ Failed to read sales data: {exc}", file=sys.stderr)
        sys.exit(1)

    # Extract: merge store data with extra data
    merged_df = extract(store_data, args.extra)

    # Transform: clean and filter the merged DataFrame
    cleaned_df = transform(merged_df)

    # Aggregate: average weekly sales per month
    agg_df = avg_weekly_sales_per_month(cleaned_df)

    # Load: write CSV outputs
    load(cleaned_df, args.clean_path, agg_df, args.agg_path)

    # Validate outputs
    try:
        validation(args.clean_path)
        validation(args.agg_path)
    except Exception as exc:
        print(f"❌ Validation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print("✅ Pipeline completed successfully!")
    print(f"Cleaned data written to {Path(args.clean_path).resolve()}")
    print(f"Aggregated data written to {Path(args.agg_path).resolve()}")


if __name__ == "__main__":
    main()