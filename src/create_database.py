
import sqlite3
from pathlib import Path

import pandas as pd

# Locate the project folder and data directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "retail_sales.db"

# Create the data directory if it does not exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Sample retail sales data
sales_data = [
    {
        "order_id": 1001,
        "order_date": "2026-01-05",
        "product": "Laptop",
        "category": "Electronics",
        "quantity": 2,
        "unit_price": 55000,
        "customer": "Aarav",
        "region": "West",
    },
    {
        "order_id": 1002,
        "order_date": "2026-01-12",
        "product": "Chair",
        "category": "Furniture",
        "quantity": 4,
        "unit_price": 3500,
        "customer": "Diya",
        "region": "North",
    },
    {
        "order_id": 1003,
        "order_date": "2026-02-03",
        "product": "Phone",
        "category": "Electronics",
        "quantity": 3,
        "unit_price": 22000,
        "customer": "Ishaan",
        "region": "South",
    },
    {
        "order_id": 1004,
        "order_date": "2026-02-18",
        "product": "Desk",
        "category": "Furniture",
        "quantity": 2,
        "unit_price": 8000,
        "customer": "Diya",
        "region": "West",
    },
    {
        "order_id": 1005,
        "order_date": "2026-03-07",
        "product": "Headphones",
        "category": "Electronics",
        "quantity": 5,
        "unit_price": 2500,
        "customer": "Meera",
        "region": "East",
    },
    {
        "order_id": 1006,
        "order_date": "2026-03-21",
        "product": "Chair",
        "category": "Furniture",
        "quantity": 3,
        "unit_price": 3500,
        "customer": "Aarav",
        "region": "North",
    },
    {
        "order_id": 1007,
        "order_date": "2026-04-02",
        "product": "Laptop",
        "category": "Electronics",
        "quantity": 1,
        "unit_price": 55000,
        "customer": "Meera",
        "region": "West",
    },
    {
        "order_id": 1008,
        "order_date": "2026-04-15",
        "product": "Desk",
        "category": "Furniture",
        "quantity": 3,
        "unit_price": 8000,
        "customer": "Ishaan",
        "region": "South",
    },
]

# Convert the records into a DataFrame
df = pd.DataFrame(sales_data)

# Calculate revenue for each order
df["revenue"] = df["quantity"] * df["unit_price"]

# Save the data to a SQLite database
with sqlite3.connect(DATABASE_PATH) as connection:
    df.to_sql("sales", connection, if_exists="replace", index=False)

    # Verify that the table was created
    result = pd.read_sql_query(
        "SELECT * FROM sales LIMIT 5;",
        connection,
    )

print(f"Database created at: {DATABASE_PATH}")
print("\nFirst five rows of the sales table:")
print(result.to_string(index=False))
print(f"\nTotal records loaded: {len(df)}")
