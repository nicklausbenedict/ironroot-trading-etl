# Ironroot Trading ETL

Ironroot Trading ETL is a Python practice project for building a custom CSV-based ETL pipeline.

The project reads raw CSV files from `data/raw`, cleans and validates the records, separates accepted and rejected rows, writes validation reports, and generates curated dimension/fact CSVs for downstream analytics.

By default, the pipeline reads raw CSVs from the local project directory. It can also stream the same raw CSV files from an existing S3 bucket when run with `--source s3`.

## Project Layout

```text
src/                 Pipeline source code
glue/                AWS Glue entrypoint script
tests/               Unit tests
data/raw/            Committed sample source CSVs
data/processed/      Generated accepted cleaned CSVs
data/rejected/       Generated rejected CSVs with validation reasons
data/reports/        Generated validation reports
data/curated/        Generated dimension/fact CSV and Parquet files
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

To configure S3 sourcing later, copy `.env.example` to `.env` and fill in your bucket settings. `.env` is ignored by Git.

Run the unit tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Available Commands

Run the pipeline with default directories:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline
```

Run the pipeline from S3:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --source s3
```

Run the pipeline and upload curated CSV and Parquet files to S3:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --upload-curated
```

Run the pipeline from S3 and upload curated CSV and Parquet files back to S3:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --source s3 --upload-curated
```

Run the pipeline with explicit output directories:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --processed-dir data\processed --rejected-dir data\rejected --curated-dir data\curated --reports-dir data\reports
```

Run the pipeline from S3 with explicit output directories:

```powershell
.\.venv\Scripts\python.exe -m src.pipeline --source s3 --processed-dir data\processed --rejected-dir data\rejected --curated-dir data\curated --reports-dir data\reports
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

Package the project code for AWS Glue:

```powershell
New-Item -ItemType Directory -Force build
Compress-Archive -Path src -DestinationPath build\ironroot_etl_src.zip -Force
```

## Outputs

Running the pipeline writes:

```text
data/processed/*.csv
data/rejected/*_rejected.csv
data/reports/validation_summary.json
data/curated/csv/*.csv
data/curated/parquet/*.parquet
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

## S3 Source Configuration

S3 mode expects the bucket to contain the same raw CSV filenames used in `data/raw`:

```text
stores.csv
products.csv
customers.csv
sales.csv
inventory.csv
suppliers.csv
purchase_orders.csv
```

Configure local S3 settings in `.env`:

```env
S3_BUCKET=your-bucket-name
S3_RAW_PREFIX=optional/prefix/
S3_CURATED_CSV_PREFIX=curated/csv/
S3_CURATED_PARQUET_PREFIX=curated/parquet/
AWS_PROFILE=optional-profile-name
```

If `S3_RAW_PREFIX=raw/`, the pipeline reads keys like `raw/stores.csv` and `raw/sales.csv`.

When `--upload-curated` is used, curated files are uploaded under timestamped run folders:

```text
curated/csv/YYYYMMDDTHHMMSSZ/*.csv
curated/parquet/YYYYMMDDTHHMMSSZ/*.parquet
```

After all expected curated CSV and Parquet files are uploaded and verified, the pipeline writes:

```text
curated/latest_manifest.json
```

## AWS Glue Deployment

The Glue integration keeps the project code modular. Upload the thin entrypoint script and a zipped copy of `src/` to S3:

```text
s3://your-bucket-name/glue/scripts/ironroot_glue_job.py
s3://your-bucket-name/glue/packages/ironroot_etl_src.zip
```

Create an AWS Glue Spark job with Glue 5.1, Python 3, and this script path:

```text
s3://your-bucket-name/glue/scripts/ironroot_glue_job.py
```

Configure these job parameters:

```text
--extra-py-files=s3://your-bucket-name/glue/packages/ironroot_etl_src.zip
--S3_BUCKET=your-bucket-name
--S3_RAW_PREFIX=raw/
--S3_CURATED_CSV_PREFIX=curated/csv/
--S3_CURATED_PARQUET_PREFIX=curated/parquet/
```

Configure dependencies with a requirements file in S3:

```text
--python-modules-installer-option=-r
--additional-python-modules=s3://your-bucket-name/glue/requirements/requirements.txt
```

The Glue job does not use `.env` or `AWS_PROFILE`. It should use the IAM role attached to the Glue job for S3 and CloudWatch Logs access.

## Notes

`.env` is local-only and used for optional S3 source configuration.

`.venv/`, `.env`, Python caches, and generated pipeline outputs are ignored by Git.

`data/raw/` is committed because the tests and examples depend on the sample source data. The dataset is fictional and intended for ETL practice. Additional dataset details live in `data/README.md`.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
