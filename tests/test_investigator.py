
import pandas as pd
import pytest

import src.investigator as investigator


def fake_query_results(query):
    """Return predictable results for each SQL query in the investigation."""
    sql = " ".join(query.lower().split())

    # Step 1: Inspect the dataset's date range.
    if "min(date(order_date))" in sql and "max(date(order_date))" in sql:
        return pd.DataFrame([{
            "min_date": "2024-01-01",
            "max_date": "2024-03-03",
        }])

    # Step 2: Monthly performance.
    if "as month" in sql and "group by substr(order_date, 1, 7)" in sql:
        return pd.DataFrame([
            {
                "month": "2024-01",
                "total_revenue": 1000.00,
                "total_orders": 10,
                "units_sold": 100,
            },
            {
                "month": "2024-02",
                "total_revenue": 1200.00,
                "total_orders": 12,
                "units_sold": 125,
            },
        ])

    # Step 3: Country-level comparisons.
    if "group by country" in sql:
        return pd.DataFrame([
            {
                "country": "Country A",
                "previous_revenue": 700.00,
                "current_revenue": 500.00,
            },
            {
                "country": "Country B",
                "previous_revenue": 300.00,
                "current_revenue": 700.00,
            },
        ])

    # Step 4: Product-level comparisons.
    if "group by product" in sql:
        return pd.DataFrame([
            {
                "product": "Product A",
                "previous_revenue": 600.00,
                "current_revenue": 400.00,
            },
            {
                "product": "Product B",
                "previous_revenue": 400.00,
                "current_revenue": 800.00,
            },
        ])

    raise AssertionError(f"Unexpected SQL query: {query}")


def test_investigation_compares_latest_completed_months(monkeypatch):
    monkeypatch.setattr(
        investigator,
        "run_query",
        fake_query_results,
    )

    result = investigator.investigate_revenue_change()

    # March is incomplete in the simulated dataset, so February
    # should be compared with January.
    assert result["previous_month"] == "2024-01"
    assert result["current_month"] == "2024-02"

    assert result["previous_revenue"] == 1000.00
    assert result["current_revenue"] == 1200.00
    assert result["revenue_change"] == 200.00
    assert result["change_pct"] == pytest.approx(20.0)


def test_investigation_reports_supporting_metrics(monkeypatch):
    monkeypatch.setattr(
        investigator,
        "run_query",
        fake_query_results,
    )

    result = investigator.investigate_revenue_change()

    assert result["previous_orders"] == 10
    assert result["current_orders"] == 12
    assert result["previous_units"] == 100
    assert result["current_units"] == 125


def test_investigation_returns_country_and_product_comparisons(monkeypatch):
    monkeypatch.setattr(
        investigator,
        "run_query",
        fake_query_results,
    )

    result = investigator.investigate_revenue_change()

    country_changes = result["country_drivers"].set_index("country")
    product_changes = result["product_drivers"].set_index("product")

    assert country_changes.loc["Country A", "change"] == -200.00
    assert country_changes.loc["Country B", "change"] == 400.00

    assert product_changes.loc["Product A", "change"] == -200.00
    assert product_changes.loc["Product B", "change"] == 400.00


def test_investigation_includes_steps_and_recommendations(monkeypatch):
    monkeypatch.setattr(
        investigator,
        "run_query",
        fake_query_results,
    )

    result = investigator.investigate_revenue_change()

    assert len(result["steps"]) == 4
    assert result["findings"]
    assert result["recommendations"]
    assert any(
        "Country A" in finding
        for finding in result["findings"]
    )


def test_investigation_rejects_missing_month_data(monkeypatch):
    def query_without_monthly_data(query):
        sql = " ".join(query.lower().split())

        if "min(date(order_date))" in sql:
            return pd.DataFrame([{
                "min_date": "2024-01-01",
                "max_date": "2024-03-03",
            }])

        if "as month" in sql:
            return pd.DataFrame([
                {
                    "month": "2024-01",
                    "total_revenue": 1000.00,
                    "total_orders": 10,
                    "units_sold": 100,
                }
            ])

        raise AssertionError(f"Unexpected SQL query: {query}")

    monkeypatch.setattr(
        investigator,
        "run_query",
        query_without_monthly_data,
    )

    with pytest.raises(ValueError, match="Revenue data is missing"):
        investigator.investigate_revenue_change()
