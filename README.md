# Walmart Retail Data Pipeline

This repository implements an extract–transform–load (ETL) pipeline in Python to
analyse sales data for a multinational retailer, Walmart.  The pipeline
processes sales and complementary data, cleans and augments it, computes
monthly average weekly sales, and saves the outputs for further analysis.

## Overview

The project comprises a set of modular functions defined in
`etl_pipeline.py` that can be composed to build a data pipeline.  The key
steps are:

* **Extract** – Read a Parquet file containing complementary data and merge it
  with a DataFrame of store sales on a common `index` column.
* **Transform** – Clean missing values, extract the month component from a
  date column, filter rows where `Weekly_Sales` exceeds a threshold and
  drop unnecessary columns.
* **Aggregate** – Compute the average weekly sales per month using pandas
  `groupby`, `agg`, `reset_index` and `round`.
* **Load** – Persist the cleaned and aggregated DataFrames to CSV files.
* **Validate** – Check that the output files exist on disk.

## Files

```
retail-data-pipeline/
├── README.md            Project description and usage instructions
├── etl_pipeline.py      Core functions implementing extract, transform, aggregate, load and validate
├── main.py              Command‑line entrypoint that orchestrates the ETL pipeline
├── requirements.txt     Python dependencies
└── tests/
    └── test_etl_pipeline.py   Unit tests for the functions
```

## Usage

Install the required dependencies (see `requirements.txt`):

```bash
pip install -r requirements.txt
```

Assuming you have a CSV file `grocery_sales.csv` and a Parquet file
`extra_data.parquet` in the current working directory, you can run the ETL
pipeline as follows:

```bash
python main.py \
  --sales grocery_sales.csv \
  --extra extra_data.parquet \
  --clean-path clean_data.csv \
  --agg-path agg_data.csv
```

This will:

1. Read `grocery_sales.csv` into a DataFrame.
2. Merge it with the extra data from `extra_data.parquet` on the `index`
   column.
3. Clean the merged data by filling missing numeric values with the column
   means, extracting the month from the `Date` column, filtering rows where
   `Weekly_Sales > 10000`, and dropping extraneous columns.
4. Compute the average weekly sales per month and round to two decimal
   places.
5. Write the cleaned data to `clean_data.csv` and the aggregated data to
   `agg_data.csv`.
6. Validate that the output files exist and report success.

## Functions in `etl_pipeline.py`

The core logic lives in `etl_pipeline.py`.  Each function is documented via
docstrings and can be imported and used independently:

* `extract(store_data: pd.DataFrame, extra_data_path: str) -> pd.DataFrame` –
  merge a store sales DataFrame with complementary Parquet data on the
  `index` column.
* `transform(raw_data: pd.DataFrame) -> pd.DataFrame` – clean and transform the
  merged DataFrame as described above.
* `avg_weekly_sales_per_month(clean_data: pd.DataFrame) -> pd.DataFrame` –
  compute average weekly sales per month.
* `load(full_data: pd.DataFrame, full_data_file_path: str,
        agg_data: pd.DataFrame, agg_data_file_path: str) -> None` – write
  DataFrames to CSV files.
* `validation(file_path: str) -> None` – raise an exception if the
  specified file does not exist.

## Testing

Unit tests covering the primary functions can be executed with:

```bash
pytest -q
```

## Notes

The SQL query to retrieve the base sales data is provided for context:

```sql
SELECT * FROM grocery_sales;
```

In a production environment you would execute this query against a database
instead of reading from a CSV file.  The pipeline is written using pandas
for educational purposes and can be extended or adapted for other tools
such as Spark or dbt.