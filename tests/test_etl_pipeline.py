"""Unit tests for the Walmart retail data pipeline functions."""
from pathlib import Path
import json

import pandas as pd
import pytest

from etl_pipeline import (
    extract,
    transform,
    avg_weekly_sales_per_month,
    load,
    validation,
)


def test_extract_merges_on_index(tmp_path: Path) -> None:
    # Prepare store data with index and other columns
    store_df = pd.DataFrame({
        "index": [1, 2],
        "Weekly_Sales": [12000, 13000],
        "Date": ["2024-01-05", "2024-01-12"],
    })
    # Prepare extra data and write to Parquet
    extra_df = pd.DataFrame({
        "index": [1, 2],
        "Temperature": [70, 65],
    })
    parquet_path = tmp_path / "extra.parquet"
    extra_df.to_parquet(parquet_path)

    merged = extract(store_df, parquet_path)

    assert len(merged) == 2
    assert "Temperature" in merged.columns
    assert merged.loc[merged["index"] == 1, "Temperature"].iloc[0] == 70


def test_transform_cleans_and_filters() -> None:
    # Create a DataFrame with missing values and multiple columns
    raw = pd.DataFrame({
        "index": [1, 2, 3],
        "Weekly_Sales": [12000.0, None, 9000.0],
        "CPI": [2.5, None, 3.0],
        "Unemployment": [4.0, 5.0, None],
        "Date": ["2024-01-05", "2024-02-15", "2024-03-22"],
        "Temperature": [70, 65, 75],
        "Type": ["A", "B", "C"],
        "Size": [1000, 2000, 3000],
    })

    clean = transform(raw)

    # Should drop rows with Weekly_Sales <= 10000
    assert len(clean) == 2
    # Should add Month column
    assert "Month" in clean.columns
    # Should not include dropped columns
    for col in ["Temperature", "Type", "Size", "Date", "index"]:
        assert col not in clean.columns


def test_avg_weekly_sales_per_month() -> None:
    clean = pd.DataFrame({
        "Month": [1, 1, 2, 2],
        "Weekly_Sales": [10000, 20000, 15000, 25000],
    })
    agg = avg_weekly_sales_per_month(clean)
    # Two months
    assert len(agg) == 2
    # Check column names
    assert list(agg.columns) == ["Month", "Avg_Sales"]
    # Check values rounded to two decimals
    jan_sales = agg.loc[agg["Month"] == 1, "Avg_Sales"].iloc[0]
    feb_sales = agg.loc[agg["Month"] == 2, "Avg_Sales"].iloc[0]
    assert abs(jan_sales - 15000.00) < 1e-2
    assert abs(feb_sales - 20000.00) < 1e-2


def test_load_and_validation(tmp_path: Path) -> None:
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"b": [3, 4]})
    clean_path = tmp_path / "clean.csv"
    agg_path = tmp_path / "agg.csv"
    load(df1, clean_path, df2, agg_path)
    # Validate writes
    assert clean_path.exists()
    assert agg_path.exists()
    # Use validation function
    validation(clean_path)
    validation(agg_path)

    # Test that validation raises on missing file
    missing = tmp_path / "missing.csv"
    with pytest.raises(Exception):
        validation(missing)