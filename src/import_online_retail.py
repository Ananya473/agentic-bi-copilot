
from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = PROJECT_ROOT / "data" / "extracted" / "Online Retail.xlsx"
DATABASE_PATH = PROJECT_ROOT / "data" / "retail_sales.db"


def import_dataset():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {EXCEL_PATH}\n"
            "Place Online Retail.xlsx inside the data folder."
        )

    print("Reading Excel dataset...")
    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")

    # Standardize column names for reliable processing.
    df.columns = df.columns.str.strip()

    required = [
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    original_rows = len(df)

    # Remove rows without essential transaction information.
    df = df.dropna(
        subset=["InvoiceNo", "StockCode", "Quantity",
                "InvoiceDate", "UnitPrice", "Country"]
    ).copy()

    # Keep all remaining transactions in the source table.
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    df["Description"] = df["Description"].fillna("Unknown product").astype(str)
    df["Country"] = df["Country"].astype(str).str.strip()
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")

    df = df.dropna(subset=["Quantity", "UnitPrice", "InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]

    # Cancelled invoices and negative quantities must not be counted
    # as ordinary sales. Preserve them in transactions for later analysis.
    sales = df[
        ~df["InvoiceNo"].str.upper().str.startswith("C")
        & (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
    ].copy()

    # Keep the familiar columns used by the existing analytics modules.
    sales = sales.rename(
        columns={
            "InvoiceNo": "order_id",
            "StockCode": "stock_code",
            "Description": "product",
            "InvoiceDate": "order_date",
            "Quantity": "quantity",
            "UnitPrice": "unit_price",
            "CustomerID": "customer_id",
            "Country": "country",
            "Revenue": "revenue",
        }
    )

    sales["order_date"] = sales["order_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    sales["customer_id"] = sales["customer_id"].astype("Int64")

    # This dataset does not contain product categories.
    # Do not invent categories; use product and country analyses instead.
    sales["category"] = "Uncategorized"

    sales = sales[
        [
            "order_id", "order_date", "product", "category",
            "quantity", "unit_price", "revenue", "customer_id",
            "country", "stock_code",
        ]
    ]

    # Store cleaned transactions separately so cancellations and returns
    # remain available for future analysis.
    transactions = df.rename(
        columns={
            "InvoiceNo": "invoice_no",
            "StockCode": "stock_code",
            "Description": "description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "UnitPrice": "unit_price",
            "CustomerID": "customer_id",
            "Country": "country",
            "Revenue": "revenue",
        }
    )

    transactions = transactions[
        [
            "invoice_no", "stock_code", "description", "quantity",
            "invoice_date", "unit_price", "customer_id", "country",
            "revenue",
        ]
    ].copy()

    transactions["invoice_date"] = transactions["invoice_date"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    transactions["customer_id"] = transactions["customer_id"].astype("Int64")

    print(f"Original rows: {original_rows:,}")
    print(f"Usable transaction rows: {len(transactions):,}")
    print(f"Positive sales rows: {len(sales):,}")
    print(f"Unique countries: {sales['country'].nunique():,}")
    print(f"Unique products: {sales['stock_code'].nunique():,}")

    # Replace the database only after the Excel data has been processed.
    with sqlite3.connect(DATABASE_PATH) as connection:
        transactions.to_sql("transactions", connection, if_exists="replace", index=False)
        sales.to_sql("sales", connection, if_exists="replace", index=False)

    print(f"\nDatabase updated: {DATABASE_PATH}")
    print(f"Positive sales revenue: {sales['revenue'].sum():,.2f}")
    print("Import completed successfully.")


if __name__ == "__main__":
    import_dataset()
