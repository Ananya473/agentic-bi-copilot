
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "retail_sales.db"


def run_query(query: str) -> pd.DataFrame:
    """Run trusted, application-defined analytical SQL."""
    with sqlite3.connect(
        f"{DATABASE_PATH.resolve().as_uri()}?mode=ro",
        uri=True,
    ) as connection:
        return pd.read_sql_query(query, connection)


def get_total_revenue() -> pd.DataFrame:
    return run_query("""
        SELECT
            ROUND(SUM(revenue), 2) AS total_revenue,
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(quantity) AS units_sold,
            COUNT(DISTINCT customer_id) AS unique_customers
        FROM sales
    """)


def get_monthly_revenue() -> pd.DataFrame:
    return run_query("""
        SELECT
            substr(order_date, 1, 7) AS month,
            ROUND(SUM(revenue), 2) AS total_revenue
        FROM sales
        GROUP BY substr(order_date, 1, 7)
        ORDER BY month
    """)

def get_daily_revenue() -> pd.DataFrame:
    """Return daily revenue, distinct orders, and units sold."""

    return run_query("""
        SELECT
            substr(order_date, 1, 10) AS date,
            ROUND(SUM(revenue), 2) AS total_revenue,
            COUNT(DISTINCT order_id) AS orders,
            SUM(quantity) AS units_sold
        FROM sales
        GROUP BY substr(order_date, 1, 10)
        ORDER BY date
    """)



def get_revenue_by_category() -> pd.DataFrame:
    """Compatibility function: this dataset has no real categories."""
    return run_query("""
        SELECT
            'Uncategorized' AS category,
            ROUND(SUM(revenue), 2) AS total_revenue
        FROM sales
    """)


def get_top_products(limit: int = 10) -> pd.DataFrame:
    limit = max(1, min(int(limit), 100))
    return run_query(f"""
        SELECT
            stock_code,
            product,
            SUM(quantity) AS units_sold,
            ROUND(SUM(revenue), 2) AS total_revenue
        FROM sales
        GROUP BY stock_code, product
        ORDER BY total_revenue DESC
        LIMIT {limit}
    """)


def get_revenue_by_country(limit: int = 15) -> pd.DataFrame:
    limit = max(1, min(int(limit), 100))
    return run_query(f"""
        SELECT
            country,
            ROUND(SUM(revenue), 2) AS total_revenue,
            COUNT(DISTINCT order_id) AS orders,
            COUNT(DISTINCT customer_id) AS customers
        FROM sales
        GROUP BY country
        ORDER BY total_revenue DESC
        LIMIT {limit}
    """)


def get_top_customers(limit: int = 10) -> pd.DataFrame:
    limit = max(1, min(int(limit), 100))
    return run_query(f"""
        SELECT
            customer_id,
            COUNT(DISTINCT order_id) AS orders,
            SUM(quantity) AS units_purchased,
            ROUND(SUM(revenue), 2) AS total_revenue
        FROM sales
        WHERE customer_id IS NOT NULL
        GROUP BY customer_id
        ORDER BY total_revenue DESC
        LIMIT {limit}
    """)



def get_returns_summary() -> pd.DataFrame:
    return run_query("""
        SELECT
            SUM(CASE WHEN quantity < 0 THEN 1 ELSE 0 END)
                AS negative_quantity_lines,
            SUM(CASE WHEN invoice_no LIKE 'C%' THEN 1 ELSE 0 END)
                AS cancelled_invoice_lines,
            ROUND(
                SUM(
                    CASE
                        WHEN quantity < 0
                        THEN ABS(quantity * unit_price)
                        ELSE 0
                    END
                ), 2
            ) AS negative_quantity_value
        FROM transactions
    """)

