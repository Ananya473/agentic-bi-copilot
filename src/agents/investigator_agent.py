
import pandas as pd

from src.investigator import investigate_revenue_change
from src.anomaly_detection import detect_revenue_anomalies


def investigator_agent() -> dict:
    """
    Investigator Agent:
    Investigates revenue changes and detects unusual
    daily revenue patterns using existing modules.
    """

    results = {}
    errors = {}

    # Investigation of monthly revenue changes
    try:
        results["revenue_investigation"] = investigate_revenue_change()

    except Exception as error:
        errors["revenue_investigation"] = str(error)

    # Detection of daily revenue anomalies
    try:
        anomalies_df = detect_revenue_anomalies()

        if anomalies_df is None or anomalies_df.empty:
            results["anomalies"] = []
        else:
            unusual_days = anomalies_df[
                anomalies_df["is_anomaly"] == True
            ]

            results["anomalies"] = unusual_days.to_dict(
                orient="records"
            )

    except Exception as error:
        errors["anomaly_detection"] = str(error)

    # Determine overall execution status
    if not errors:
        status = "completed"
    elif results:
        status = "partial"
    else:
        status = "failed"

    return {
        "agent": "investigator",
        "status": status,
        "results": results,
        "errors": errors,
    }
