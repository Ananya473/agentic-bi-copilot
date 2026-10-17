
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


def _is_supported_question(question: str) -> bool:
    """Check whether a question concerns supported retail analytics."""

    q = question.lower()

    supported_topics = (
        "revenue", "sales", "order", "month", "monthly", "trend",
        "product", "products", "country", "countries", "customer",
        "customers", "client", "clients", "categor", "return",
        "cancellation", "cancelled", "canceled", "unit", "quantity",
        "stock code", "top", "best-selling", "bestselling",
    )

    return any(topic in q for topic in supported_topics)


def generate_sql(question: str) -> str:
    """Generate SQL for a business question."""
    sql, _source = generate_sql_with_source(question)
    return sql


def generate_sql_with_source(question: str) -> tuple[str, str]:
    """Return generated SQL and the method used."""

    if not question or not question.strip():
        raise ValueError("Please enter a business question.")

    # Reject unsupported questions BEFORE contacting Gemini.
    if not _is_supported_question(question):
        raise ValueError(
            "Unsupported question. Ask about retail revenue, sales, "
            "orders, products, customers, countries, monthly trends, "
            "categories, or returns."
        )

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    if api_key:
        try:
            client = genai.Client(api_key=api_key)

            prompt = """
You are a SQL assistant for a retail business intelligence dashboard.

Convert the user's question into exactly one SQLite SELECT query.
Return only SQL, without Markdown or explanations.

Table sales columns:
order_id, order_date, product, category, quantity, unit_price,
revenue, customer_id, country, stock_code.

Table transactions columns:
invoice_no, stock_code, description, quantity, invoice_date,
unit_price, customer_id, country, revenue.

Rules:
- Use sales for normal sales, revenue, product, customer, country,
  and monthly sales analysis.
- Use transactions for returns, cancellations, and transaction records.
- For monthly analysis, group by substr(order_date, 1, 7).
- Exclude missing customer IDs for individual customer analysis.
- Never invent tables or columns.
- Generate one read-only SELECT query only.
- Do not include Markdown code fences.
"""

            response = client.models.generate_content(
                model=model,
                contents=(
                    prompt
                    + "\nBusiness question: "
                    + question.strip()
                ),
            )

            sql = (response.text or "").strip()
            sql = sql.removeprefix("```sql").removeprefix("```")
            sql = sql.removesuffix("```").strip()

            normalized = sql.lower().lstrip()

            # Basic validation. The query engine must independently
            # enforce read-only execution and table access.
            if (
                normalized.startswith("select ")
                and ";" not in sql.rstrip(";")
                and not any(
                    token in normalized.split()
                    for token in (
                        "insert", "update", "delete", "drop",
                        "alter", "create", "pragma", "attach",
                    )
                )
            ):
                return sql, "Gemini AI"

        except Exception:
            # Keep the application usable when the API fails.
            pass

    return _fallback_sql(question), "Rule-based fallback"


def _fallback_sql(question: str) -> str:
    """Generate SQL for common retail questions without Gemini."""

    q = question.lower().strip()

    # Returns and cancellations
    if any(word in q for word in (
        "return", "returns", "cancellation", "cancelled", "canceled"
    )):
        return """
            SELECT
                SUM(CASE WHEN quantity < 0 THEN 1 ELSE 0 END)
                    AS negative_quantity_lines,
                SUM(CASE WHEN invoice_no LIKE 'C%' THEN 1 ELSE 0 END)
                    AS cancelled_invoice_lines,
                ROUND(SUM(
                    CASE WHEN quantity < 0
                    THEN ABS(quantity * unit_price) ELSE 0 END
                ), 2) AS negative_quantity_value
            FROM transactions
        """

    # Monthly revenue trends
    if any(word in q for word in (
        "monthly", "month", "trend", "over time"
    )):
        return """
            SELECT substr(order_date, 1, 7) AS month,
                   ROUND(SUM(revenue), 2) AS total_revenue
            FROM sales
            GROUP BY substr(order_date, 1, 7)
            ORDER BY month
        """

    # Country-wise revenue
    if any(word in q for word in (
        "country", "countries", "geographic", "international"
    )):
        return """
            SELECT country,
                   ROUND(SUM(revenue), 2) AS total_revenue,
                   COUNT(DISTINCT order_id) AS total_orders
            FROM sales
            GROUP BY country
            ORDER BY total_revenue DESC
        """

    # Revenue for a specific country
    country_names = (
        "united kingdom", "netherlands", "germany", "france",
        "eire", "spain", "portugal", "belgium", "switzerland",
        "norway", "italy", "australia", "japan", "sweden",
        "finland", "denmark", "ireland", "usa",
    )

    for country in country_names:
        if country in q:
            return f"""
                SELECT country,
                       ROUND(SUM(revenue), 2) AS total_revenue,
                       COUNT(DISTINCT order_id) AS total_orders
                FROM sales
                WHERE lower(country) = '{country.replace("'", "''")}'
                GROUP BY country
            """

    # Customer analysis
    if any(word in q for word in (
        "customer", "customers", "client", "clients"
    )):
        return """
            SELECT customer_id,
                   COUNT(DISTINCT order_id) AS total_orders,
                   SUM(quantity) AS units_purchased,
                   ROUND(SUM(revenue), 2) AS total_revenue
            FROM sales
            WHERE customer_id IS NOT NULL
            GROUP BY customer_id
            ORDER BY total_revenue DESC
            LIMIT 10
        """

    # Category analysis (dataset currently has only Uncategorized)
    if "categor" in q:
        return """
            SELECT category,
                   ROUND(SUM(revenue), 2) AS total_revenue
            FROM sales
            GROUP BY category
            ORDER BY total_revenue DESC
        """

    # Product analysis
    if any(word in q for word in (
        "product", "products", "best-selling", "bestselling", "stock code"
    )):
        return """
            SELECT stock_code, product,
                   SUM(quantity) AS units_sold,
                   ROUND(SUM(revenue), 2) AS total_revenue
            FROM sales
            GROUP BY stock_code, product
            ORDER BY total_revenue DESC
            LIMIT 10
        """

    # Units sold
    if any(word in q for word in ("units", "quantity")):
        return """
            SELECT SUM(quantity) AS units_sold
            FROM sales
        """

    # Overall sales metrics
    if any(word in q for word in (
        "revenue", "sales", "orders", "total"
    )):
        return """
            SELECT ROUND(SUM(revenue), 2) AS total_revenue,
                   COUNT(DISTINCT order_id) AS total_orders,
                   SUM(quantity) AS units_sold,
                   COUNT(DISTINCT customer_id) AS unique_customers
            FROM sales
        """

    raise ValueError(
        "I couldn't interpret that question. Ask about revenue, monthly "
        "trends, countries, customers, products, categories, or returns."
    )
