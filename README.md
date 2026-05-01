# Ironroot Trading ETL

Ironroot Trading ETL is a Python practice project for building a custom CSV-based ETL pipeline.

The project reads raw CSV files from `data/raw`, cleans and validates the records, separates accepted and rejected rows, writes validation reports, and generates curated dimension/fact CSVs for downstream analytics.

## Project Layout

```text
src/                 Pipeline source code
tests/               Unit tests
data/raw/            Committed sample source CSVs
data/processed/      Generated accepted cleaned CSVs
data/rejected/       Generated rejected CSVs with validation reasons
data/reports/        Generated validation reports
data/curated/        Generated dimension/fact CSVs
```

The generated data folders are committed with `.gitkeep` placeholders, but their generated CSV/report contents are ignored by Git.

## Quick Start

Create a virtual environment:

```powershell
python -m venv .venv
```

Install dependencies:

```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Run the ETL pipeline:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline
```

Run the unit tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Available Commands

Run the pipeline with default directories:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline
```

Run the pipeline with explicit output directories:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --processed-dir data\processed --rejected-dir data\rejected --curated-dir data\curated --reports-dir data\reports
```

Show pipeline command options:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --help
```

Run all tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Run one test module:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_curate
```

## Outputs

Running the pipeline writes:

```text
data/processed/*.csv
data/rejected/*_rejected.csv
data/reports/validation_summary.json
data/curated/*.csv
```

Curated outputs include:

```text
dim_store.csv
dim_product.csv
dim_customer.csv
dim_supplier.csv
fact_sales.csv
fact_inventory_snapshot.csv
fact_purchase_order.csv
```

## Notes

`data/raw/` is committed because the tests and examples depend on the sample source data. Additional dataset details live in `data/README.md`.
