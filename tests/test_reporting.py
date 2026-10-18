
import pandas as pd

from src.reporting import build_evidence_report


def test_report_includes_revenue_investigation_evidence():
    result = {
        "question": "Why did revenue change?",
        "planner_source": "Rule-based fallback",
        "results": [
            {
                "tool": "investigate_revenue_change",
                "status": "completed",
                "output": {
                    "summary": "Revenue increased in February.",
                    "previous_month": "2024-01",
                    "current_month": "2024-02",
                    "previous_revenue": 1000.0,
                    "current_revenue": 1200.0,
                    "revenue_change": 200.0,
                    "change_pct": 20.0,
                    "previous_orders": 10,
                    "current_orders": 12,
                    "previous_units": 100,
                    "current_units": 125,
                    "country_drivers": pd.DataFrame([
                        {
                            "country": "Country A",
                            "previous_revenue": 700.0,
                            "current_revenue": 500.0,
                            "change": -200.0,
                        }
                    ]),
                    "product_drivers": pd.DataFrame(),
                    "recommendations": ["Investigate order volumes."],
                },
            }
        ],
    }

    report = build_evidence_report(result)

    assert "Revenue increased in February." in report
    assert "1,000.00" in report
    assert "1,200.00" in report
    assert "Country A" in report
    assert "Investigate order volumes." in report
    assert "not proof of causation" in report


def test_report_includes_anomaly_evidence():
    result = {
        "question": "Detect anomalies",
        "planner_source": "Rule-based fallback",
        "results": [
            {
                "tool": "detect_anomalies",
                "status": "completed",
                "output": {
                    "rows_analyzed": 100,
                    "anomaly_count": 1,
                    "anomalies": pd.DataFrame([
                        {
                            "date": "2024-02-15",
                            "total_revenue": 3000.0,
                            "expected_revenue": 1000.0,
                            "deviation_pct": 200.0,
                            "anomaly_type": "High revenue",
                        }
                    ]),
                },
            }
        ],
    }

    report = build_evidence_report(result)

    assert "Dates analyzed: 100" in report
    assert "Potential anomalies: 1" in report
    assert "2024-02-15" in report
    assert "High revenue" in report
    assert "2,000.00" not in report or "3000.00" in report


def test_report_discloses_failed_tools():
    result = {
        "question": "Investigate sales",
        "planner_source": "Rule-based fallback",
        "results": [
            {
                "tool": "detect_anomalies",
                "status": "failed",
                "error": "Database unavailable",
                "output": None,
            }
        ],
    }

    report = build_evidence_report(result)

    assert "Tools failed: 1" in report
    assert "Database unavailable" in report


def test_report_handles_empty_results():
    report = build_evidence_report({
        "question": "General question",
        "planner_source": "Rule-based fallback",
        "results": [],
    })

    assert "Tools completed: 0" in report
    assert "Tools failed: 0" in report
