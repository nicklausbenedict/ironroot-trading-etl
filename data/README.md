# Ironroot Trading Co. Raw CSV Dataset

Fictional fantasy general goods dataset for practicing Python ETL, cloud object storage, validation, dimensional modeling, and SQL loading. The records are synthetic and are not based on real customers, stores, suppliers, or transactions.

Files:
- stores.csv
- products.csv
- customers.csv
- sales.csv
- inventory.csv
- suppliers.csv
- purchase_orders.csv

Notes:
- The files intentionally include a few raw-data quality issues: duplicate sales, invalid foreign keys, blank IDs, and whitespace around some IDs.
- Suggested curated tables: dim_store, dim_product, dim_customer, fact_sales, fact_inventory_snapshot, fact_purchase_order.
