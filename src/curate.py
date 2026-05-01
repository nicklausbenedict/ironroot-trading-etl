from __future__ import annotations

import pandas as pd


DIM_STORE_COLUMNS = ("StoreId", "StoreName", "Region", "Zone", "FactionAlignment")
DIM_PRODUCT_COLUMNS = ("ProductId", "ProductName", "Category", "Rarity", "BasePriceGold", "IsPerishable")
DIM_CUSTOMER_COLUMNS = ("CustomerId", "CustomerName", "CharacterClass", "Level", "Faction", "HomeRegion")
DIM_SUPPLIER_COLUMNS = ("SupplierId", "SupplierName", "Region", "Specialty", "ReliabilityScore")

FACT_SALES_COLUMNS = (
    "SaleId",
    "StoreId",
    "ProductId",
    "CustomerId",
    "SaleDate",
    "Quantity",
    "UnitPriceGold",
    "RevenueGold",
    "PriceVarianceGold",
    "PriceVariancePercent",
)
FACT_INVENTORY_SNAPSHOT_COLUMNS = (
    "InventoryId",
    "StoreId",
    "ProductId",
    "SnapshotDate",
    "QuantityOnHand",
    "ReorderThreshold",
    "IsBelowReorderThreshold",
)
FACT_PURCHASE_ORDER_COLUMNS = (
    "PurchaseOrderId",
    "SupplierId",
    "StoreId",
    "ProductId",
    "OrderDate",
    "ExpectedDeliveryDate",
    "ActualDeliveryDate",
    "QuantityOrdered",
    "UnitCostGold",
    "DaysLate",
    "WasLate",
)

CURATED_COLUMNS = {
    "dim_store": DIM_STORE_COLUMNS,
    "dim_product": DIM_PRODUCT_COLUMNS,
    "dim_customer": DIM_CUSTOMER_COLUMNS,
    "dim_supplier": DIM_SUPPLIER_COLUMNS,
    "fact_sales": FACT_SALES_COLUMNS,
    "fact_inventory_snapshot": FACT_INVENTORY_SNAPSHOT_COLUMNS,
    "fact_purchase_order": FACT_PURCHASE_ORDER_COLUMNS,
}


def build_curated_tables(processed_tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        "dim_store": _project(processed_tables["stores"], DIM_STORE_COLUMNS),
        "dim_product": _project(processed_tables["products"], DIM_PRODUCT_COLUMNS),
        "dim_customer": _project(processed_tables["customers"], DIM_CUSTOMER_COLUMNS),
        "dim_supplier": _project(processed_tables["suppliers"], DIM_SUPPLIER_COLUMNS),
        "fact_sales": _build_fact_sales(processed_tables["sales"], processed_tables["products"]),
        "fact_inventory_snapshot": _build_fact_inventory_snapshot(processed_tables["inventory"]),
        "fact_purchase_order": _build_fact_purchase_order(processed_tables["purchase_orders"]),
    }


def _project(df: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    return df.loc[:, list(columns)].copy()


def _build_fact_sales(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    fact = sales.loc[:, ["SaleId", "StoreId", "ProductId", "CustomerId", "SaleDate", "Quantity", "UnitPriceGold"]].copy()
    product_prices = products.loc[:, ["ProductId", "BasePriceGold"]].copy()
    fact = fact.merge(product_prices, on="ProductId", how="left", validate="many_to_one")
    fact["RevenueGold"] = fact["Quantity"] * fact["UnitPriceGold"]
    fact["PriceVarianceGold"] = fact["UnitPriceGold"] - fact["BasePriceGold"]
    fact["PriceVariancePercent"] = fact["PriceVarianceGold"] / fact["BasePriceGold"]
    return fact.loc[:, list(FACT_SALES_COLUMNS)]


def _build_fact_inventory_snapshot(inventory: pd.DataFrame) -> pd.DataFrame:
    fact = _project(
        inventory,
        ("InventoryId", "StoreId", "ProductId", "SnapshotDate", "QuantityOnHand", "ReorderThreshold"),
    )
    fact["IsBelowReorderThreshold"] = fact["QuantityOnHand"] < fact["ReorderThreshold"]
    return fact.loc[:, list(FACT_INVENTORY_SNAPSHOT_COLUMNS)]


def _build_fact_purchase_order(purchase_orders: pd.DataFrame) -> pd.DataFrame:
    fact = _project(
        purchase_orders,
        (
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
    )
    expected_delivery = pd.to_datetime(fact["ExpectedDeliveryDate"], errors="coerce")
    actual_delivery = pd.to_datetime(fact["ActualDeliveryDate"], errors="coerce")
    fact["DaysLate"] = (actual_delivery - expected_delivery).dt.days.astype("Int64")
    fact["WasLate"] = fact["DaysLate"].gt(0).fillna(False).astype("boolean")
    return fact.loc[:, list(FACT_PURCHASE_ORDER_COLUMNS)]
