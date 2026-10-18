
import pandas as pd

from src.analytics import run_query


def _month_label(month: str) -> str:
    return pd.Period(month, freq="M").strftime("%B %Y")


def _get_revenue_by_dimension(
    previous_month: str,
    current_month: str,
    dimension: str,
) -> pd.DataFrame:
    """Compare revenue by country or product across two months."""

    # Only fixed, explicitly supported SQL dimensions are accepted.
    if dimension == "country":
        group_column = "country"
        select_expression = "country"
    elif dimension == "product":
        group_column = "product"
        select_expression = "COALESCE(product, 'Unknown')"
    else:
        raise ValueError("Unsupported investigation dimension.")

    query = f"""
        SELECT
            {select_expression} AS {dimension},
            ROUND(
                SUM(
                    CASE WHEN substr(order_date, 1, 7) = '{previous_month}'
                    THEN revenue ELSE 0 END
                ), 2
            ) AS previous_revenue,
            ROUND(
                SUM(
                    CASE WHEN substr(order_date, 1, 7) = '{current_month}'
                    THEN revenue ELSE 0 END
                ), 2
            ) AS current_revenue
        FROM sales
        WHERE substr(order_date, 1, 7)
              IN ('{previous_month}', '{current_month}')
        GROUP BY {group_column}
    """

    result = run_query(query)

    if result is None or result.empty:
        return pd.DataFrame(
            columns=[
                dimension,
                "previous_revenue",
                "current_revenue",
                "change",
            ]
        )

    result["previous_revenue"] = pd.to_numeric(
        result["previous_revenue"], errors="coerce"
    ).fillna(0)

    result["current_revenue"] = pd.to_numeric(
        result["current_revenue"], errors="coerce"
    ).fillna(0)

    result["change"] = (
        result["current_revenue"] - result["previous_revenue"]
    )

    return result.sort_values("change").reset_index(drop=True)


def investigate_revenue_change() -> dict:
    """
    Investigate the change between the two most recent completed
    calendar months represented in the retail dataset.

    Steps:
    1. Inspect the dataset's date range.
    2. Compare total monthly revenue.
    3. Compare country-level revenue.
    4. Compare product-level revenue.
    5. Summarize the largest observed contributors to the change.

    These comparisons identify associations, not proven causes.
    """

    date_range = run_query("""
        SELECT
            MIN(date(order_date)) AS min_date,
            MAX(date(order_date)) AS max_date
        FROM sales
        WHERE order_date IS NOT NULL
    """)

    if date_range is None or date_range.empty:
        raise ValueError("No order dates are available for investigation.")

    min_date = pd.to_datetime(date_range.iloc[0]["min_date"], errors="coerce")
    max_date = pd.to_datetime(date_range.iloc[0]["max_date"], errors="coerce")

    if pd.isna(min_date) or pd.isna(max_date):
        raise ValueError("The dataset contains no valid order date range.")

    # Do not compare an incomplete latest month with a full prior month.
    latest_period = pd.Period(max_date, freq="M")
    if max_date.day < latest_period.days_in_month:
        current_period = latest_period - 1
    else:
        current_period = latest_period

    previous_period = current_period - 1

    current_month = str(current_period)
    previous_month = str(previous_period)

    monthly = run_query("""
        SELECT
            substr(order_date, 1, 7) AS month,
            ROUND(SUM(revenue), 2) AS total_revenue,
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(quantity) AS units_sold
        FROM sales
        GROUP BY substr(order_date, 1, 7)
        ORDER BY month
    """)

    if monthly is None or monthly.empty:
        raise ValueError("Monthly revenue data could not be calculated.")

    monthly["month"] = monthly["month"].astype(str)
    monthly["total_revenue"] = pd.to_numeric(
        monthly["total_revenue"], errors="coerce"
    )

    monthly_lookup = monthly.set_index("month")

    for month in (previous_month, current_month):
        if month not in monthly_lookup.index:
            raise ValueError(
                f"Revenue data is missing for {_month_label(month)}."
            )

    previous_row = monthly_lookup.loc[previous_month]
    current_row = monthly_lookup.loc[current_month]

    previous_revenue = float(previous_row["total_revenue"])
    current_revenue = float(current_row["total_revenue"])
    revenue_change = current_revenue - previous_revenue

    change_pct = (
        (revenue_change / previous_revenue) * 100
        if previous_revenue != 0
        else None
    )

    # Investigation step: compare countries.
    country_drivers = _get_revenue_by_dimension(
        previous_month,
        current_month,
        "country",
    )

    # Investigation step: compare products.
    product_drivers = _get_revenue_by_dimension(
        previous_month,
        current_month,
        "product",
    )

    previous_label = _month_label(previous_month)
    current_label = _month_label(current_month)

    if revenue_change < 0:
        direction = "declined"
    elif revenue_change > 0:
        direction = "increased"
    else:
        direction = "was unchanged"

    summary = (
        f"Revenue {direction} from {previous_revenue:,.2f} in "
        f"{previous_label} to {current_revenue:,.2f} in {current_label}."
    )

    if change_pct is not None:
        summary += (
            f" The change was {revenue_change:+,.2f} "
            f"({change_pct:+.1f}%)."
        )

    # Largest negative contributors and positive offsets.
    largest_country_declines = (
        country_drivers[country_drivers["change"] < 0]
        .sort_values("change")
        .head(3)
    )

    largest_product_declines = (
        product_drivers[product_drivers["change"] < 0]
        .sort_values("change")
        .head(3)
    )

    largest_country_increases = (
        country_drivers[country_drivers["change"] > 0]
        .sort_values("change", ascending=False)
        .head(3)
    )

    largest_product_increases = (
        product_drivers[product_drivers["change"] > 0]
        .sort_values("change", ascending=False)
        .head(3)
    )

    findings = []

    for _, row in largest_country_declines.iterrows():
        findings.append(
            f"Country {row['country']} decreased by "
            f"{abs(float(row['change'])):,.2f} in revenue."
        )

    for _, row in largest_product_declines.iterrows():
        findings.append(
            f"Product {row['product']} decreased by "
            f"{abs(float(row['change'])):,.2f} in revenue."
        )

    if not findings:
        findings.append(
            "No individual country or product had a negative revenue "
            "change in the selected comparison."
        )

    recommendations = [
        "Review the largest country-level revenue declines and check "
        "whether order volumes or the number of active customers changed.",
        "Inspect products with the largest revenue decreases for changes "
        "in units sold, availability, or order frequency.",
        "Check returns, cancellations, promotions, and trading-day "
        "differences before attributing the revenue change to a cause.",
    ]

    steps = [
        {
            "step": "Inspect date coverage",
            "detail": (
                f"Available order dates range from {min_date.date()} "
                f"to {max_date.date()}."
            ),
        },
        {
            "step": "Compare monthly KPIs",
            "detail": (
                f"Compared revenue, distinct orders, and units sold "
                f"for {previous_label} and {current_label}."
            ),
        },
        {
            "step": "Investigate by country",
            "detail": (
                f"Compared revenue by country for both selected months "
                f"across {len(country_drivers)} country groups."
            ),
        },
        {
            "step": "Investigate by product",
            "detail": (
                f"Compared revenue by product for both selected months "
                f"across {len(product_drivers)} product groups."
            ),
        },
    ]

    return {
        "summary": summary,
        "previous_month": previous_month,
        "current_month": current_month,
        "previous_revenue": previous_revenue,
        "current_revenue": current_revenue,
        "revenue_change": revenue_change,
        "change_pct": change_pct,
        "previous_orders": int(previous_row["total_orders"]),
        "current_orders": int(current_row["total_orders"]),
        "previous_units": int(previous_row["units_sold"]),
        "current_units": int(current_row["units_sold"]),
        "steps": steps,
        "findings": findings,
        "country_drivers": country_drivers,
        "product_drivers": product_drivers,
        "largest_country_increases": largest_country_increases,
        "largest_product_increases": largest_product_increases,
        "recommendations": recommendations,
        "data_range": {
            "start": str(min_date.date()),
            "end": str(max_date.date()),
        },
    }
