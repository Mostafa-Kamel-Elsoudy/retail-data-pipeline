"""ETL pipeline functions for the Walmart retail data project.

This module defines a set of functions to extract data from disparate
sources, transform it for analysis, compute aggregate metrics, load the
results to disk and validate the outputs.  Each function is documented
below and can be used independently or composed together.
"""
from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

__all__ = [
    "extract",
    "transform",
    "avg_weekly_sales_per_month",
    "load",
    "validation",
]


def extract(store_data: pd.DataFrame, extra_data_path: str | Path) -> pd.DataFrame:
    """Merge a store sales DataFrame with complementary data from a Parquet file.

    The `store_data` DataFrame should contain an ``index`` column that
    corresponds to the same column in the Parquet file.  The Parquet file
    may include additional features such as temperature, fuel prices and
    markdown information.  The two datasets are merged on ``index``.

    Parameters
    ----------
    store_data : pandas.DataFrame
        DataFrame containing store sales data with an ``index`` column.
    extra_data_path : str or pathlib.Path
        Path to a Parquet file containing additional features keyed on
        ``index``.

    Returns
    -------
    pandas.DataFrame
        The merged DataFrame containing columns from both sources.
    """
    extra_data_path = Path(extra_data_path)
    extra_df = pd.read_parquet(extra_data_path)
    merged_df = store_data.merge(extra_df, on="index")
    return merged_df


def transform(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich the merged data for analysis.

    This function performs the following operations in order:

    * Fills missing values in the ``CPI``, ``Weekly_Sales`` and
      ``Unemployment`` columns with their respective column means.
    * Converts the ``Date`` column to a ``datetime64`` dtype and extracts the
      numeric month into a new ``Month`` column.
    * Filters the data to retain only rows where ``Weekly_Sales`` exceeds
      10,000.
    * Drops columns that are not needed for analysis, including markdown
      promotions, `Type`, `Size`, and `Date`.

    Parameters
    ----------
    raw_data : pandas.DataFrame
        The merged DataFrame produced by :func:`extract`.

    Returns
    -------
    pandas.DataFrame
        A cleaned and trimmed DataFrame suitable for downstream analysis.
    """
    # Work on a copy to avoid mutating the caller's DataFrame
    data = raw_data.copy()

    # Fill missing numeric columns with column means
    for col in ["CPI", "Weekly_Sales", "Unemployment"]:
        if col in data.columns:
            data[col].fillna(data[col].mean(), inplace=True)

    # Ensure Date column is datetime and extract month
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data["Month"] = data["Date"].dt.month
    else:
        # If no date column, create a Month column of NaNs
        data["Month"] = pd.NA

    # Filter rows where Weekly_Sales > 10,000
    if "Weekly_Sales" in data.columns:
        data = data.loc[data["Weekly_Sales"] > 10000].copy()

    # Drop unnecessary columns if present
    drop_cols = [
        "index",
        "Temperature",
        "Fuel_Price",
        "MarkDown1",
        "MarkDown2",
        "MarkDown3",
        "MarkDown4",
        "MarkDown5",
        "Type",
        "Size",
        "Date",
    ]
    existing = [c for c in drop_cols if c in data.columns]
    data.drop(existing, axis=1, inplace=True)

    return data


def avg_weekly_sales_per_month(clean_data: pd.DataFrame) -> pd.DataFrame:
    """Compute the average weekly sales for each month.

    Groups the cleaned sales data by ``Month`` and calculates the mean of
    ``Weekly_Sales``.  The result is returned as a DataFrame with two
    columns: ``Month`` and ``Avg_Sales``, rounded to two decimal places.

    Parameters
    ----------
    clean_data : pandas.DataFrame
        The cleaned DataFrame returned by :func:`transform`.  Must contain
        ``Month`` and ``Weekly_Sales`` columns.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with the average weekly sales for each month.
    """
    # Select only the relevant columns
    sales = clean_data[["Month", "Weekly_Sales"]].copy()

    # Group by Month and compute mean
    result = (
        sales.groupby("Month")
        .agg(Avg_Sales=("Weekly_Sales", "mean"))
        .reset_index()
        .round(2)
    )
    return result


def load(
    full_data: pd.DataFrame,
    full_data_file_path: str | Path,
    agg_data: pd.DataFrame,
    agg_data_file_path: str | Path,
) -> None:
    """Write the cleaned and aggregated DataFrames to CSV files.

    Parameters
    ----------
    full_data : pandas.DataFrame
        The cleaned DataFrame to write to disk.
    full_data_file_path : str or pathlib.Path
        Path to the CSV file for the cleaned data.
    agg_data : pandas.DataFrame
        The aggregated DataFrame returned by
        :func:`avg_weekly_sales_per_month`.
    agg_data_file_path : str or pathlib.Path
        Path to the CSV file for the aggregated data.

    Notes
    -----
    The CSV files are written without index columns.
    """
    full_data_file_path = Path(full_data_file_path)
    agg_data_file_path = Path(agg_data_file_path)

    full_data.to_csv(full_data_file_path, index=False)
    agg_data.to_csv(agg_data_file_path, index=False)


def validation(file_path: str | Path) -> None:
    """Check that a file exists and raise an exception if it does not.

    Parameters
    ----------
    file_path : str or pathlib.Path
        Path to a file expected to exist on disk.

    Raises
    ------
    Exception
        If the file does not exist at the given path.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise Exception(f"There is no file at the path {file_path}")