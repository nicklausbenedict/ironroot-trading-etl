from __future__ import annotations

from pathlib import Path

try:
    from .models import ForeignKeySpec, TableSpec
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from models import ForeignKeySpec, TableSpec


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REJECTED_DIR = DATA_DIR / "rejected"
REPORTS_DIR = DATA_DIR / "reports"
CURATED_DIR = DATA_DIR / "curated"

AUDIT_COLUMNS = ("_source_file", "_source_row_number", "_ingested_at")
VALIDATION_STATUS_COLUMN = "_validation_status"
REJECTION_REASONS_COLUMN = "_rejection_reasons"

TABLE_SPECS: dict[str, TableSpec] = {
    "stores": TableSpec(
        name="stores",
        filename="stores.csv",
        primary_key="StoreId",
        columns=("StoreId", "StoreName", "Region", "Zone", "FactionAlignment"),
        required_columns=("StoreId", "StoreName", "Region", "Zone", "FactionAlignment"),
        string_columns=("StoreId", "StoreName", "Region", "Zone", "FactionAlignment"),
    ),
    "products": TableSpec(
        name="products",
        filename="products.csv",
        primary_key="ProductId",
        columns=("ProductId", "ProductName", "Category", "Rarity", "BasePriceGold", "IsPerishable"),
        required_columns=("ProductId", "ProductName", "Category", "Rarity", "BasePriceGold", "IsPerishable"),
        string_columns=("ProductId", "ProductName", "Category", "Rarity"),
        float_columns=("BasePriceGold",),
        boolean_columns=("IsPerishable",),
    ),
    "customers": TableSpec(
        name="customers",
        filename="customers.csv",
        primary_key="CustomerId",
        columns=("CustomerId", "CustomerName", "CharacterClass", "Level", "Faction", "HomeRegion"),
        required_columns=("CustomerId", "CustomerName", "CharacterClass", "Level", "Faction", "HomeRegion"),
        string_columns=("CustomerId", "CustomerName", "CharacterClass", "Faction", "HomeRegion"),
        integer_columns=("Level",),
    ),
    "sales": TableSpec(
        name="sales",
        filename="sales.csv",
        primary_key="SaleId",
        columns=("SaleId", "StoreId", "ProductId", "CustomerId", "SaleDate", "Quantity", "UnitPriceGold"),
        required_columns=("SaleId", "StoreId", "ProductId", "CustomerId", "SaleDate", "Quantity", "UnitPriceGold"),
        string_columns=("SaleId", "StoreId", "ProductId", "CustomerId"),
        date_columns=("SaleDate",),
        integer_columns=("Quantity",),
        float_columns=("UnitPriceGold",),
    ),
    "inventory": TableSpec(
        name="inventory",
        filename="inventory.csv",
        primary_key="InventoryId",
        columns=("InventoryId", "StoreId", "ProductId", "SnapshotDate", "QuantityOnHand", "ReorderThreshold"),
        required_columns=("InventoryId", "StoreId", "ProductId", "SnapshotDate", "QuantityOnHand", "ReorderThreshold"),
        string_columns=("InventoryId", "StoreId", "ProductId"),
        date_columns=("SnapshotDate",),
        integer_columns=("QuantityOnHand", "ReorderThreshold"),
    ),
    "suppliers": TableSpec(
        name="suppliers",
        filename="suppliers.csv",
        primary_key="SupplierId",
        columns=("SupplierId", "SupplierName", "Region", "Specialty", "ReliabilityScore"),
        required_columns=("SupplierId", "SupplierName", "Region", "Specialty", "ReliabilityScore"),
        string_columns=("SupplierId", "SupplierName", "Region", "Specialty"),
        float_columns=("ReliabilityScore",),
    ),
    "purchase_orders": TableSpec(
        name="purchase_orders",
        filename="purchase_orders.csv",
        primary_key="PurchaseOrderId",
        columns=(
            "PurchaseOrderId",
            "SupplierId",
            "StoreId",
            "ProductId",
            "OrderDate",
            "ExpectedDeliveryDate",
            "ActualDeliveryDate",
            "QuantityOrdered",
            "UnitCostGold",
        ),
        required_columns=(
            "PurchaseOrderId",
            "SupplierId",
            "StoreId",
            "ProductId",
            "OrderDate",
            "ExpectedDeliveryDate",
            "QuantityOrdered",
            "UnitCostGold",
        ),
        string_columns=("PurchaseOrderId", "SupplierId", "StoreId", "ProductId"),
        date_columns=("OrderDate", "ExpectedDeliveryDate", "ActualDeliveryDate"),
        integer_columns=("QuantityOrdered",),
        float_columns=("UnitCostGold",),
    ),
}

FOREIGN_KEYS: tuple[ForeignKeySpec, ...] = (
    ForeignKeySpec("sales", "StoreId", "stores", "StoreId"),
    ForeignKeySpec("sales", "ProductId", "products", "ProductId"),
    ForeignKeySpec("sales", "CustomerId", "customers", "CustomerId"),
    ForeignKeySpec("inventory", "StoreId", "stores", "StoreId"),
    ForeignKeySpec("inventory", "ProductId", "products", "ProductId"),
    ForeignKeySpec("purchase_orders", "SupplierId", "suppliers", "SupplierId"),
    ForeignKeySpec("purchase_orders", "StoreId", "stores", "StoreId"),
    ForeignKeySpec("purchase_orders", "ProductId", "products", "ProductId"),
)

NONNEGATIVE_COLUMNS: dict[str, tuple[str, ...]] = {
    "sales": ("Quantity",),
    "inventory": ("QuantityOnHand", "ReorderThreshold"),
    "purchase_orders": ("QuantityOrdered",),
}

POSITIVE_COLUMNS: dict[str, tuple[str, ...]] = {
    "products": ("BasePriceGold",),
    "sales": ("UnitPriceGold",),
    "purchase_orders": ("UnitCostGold",),
}
