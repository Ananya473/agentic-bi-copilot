
import numpy as np
import pandas as pd

from src.analytics import get_daily_revenue


def _scaled_mad(values: np.ndarray) -> float:
    """Return a robust estimate of standard deviation using MAD."""
    median = np.median(values)
    mad = np.median(np.abs(values - median))
    return float(1.4826 * mad)


def detect_revenue_anomalies(
    window: int = 28,
    min_periods: int = 14,
    threshold_mad: float = 3.5,
    min_change_pct: float = 0.50,
) -> pd.DataFrame:
    """
    Flag unusually high or low daily revenue relative to prior
    transaction-active days.

    The baseline uses past observations only, avoiding leakage
    from the day currently being evaluated.
    """

    if window < 2:
        raise ValueError("window must be at least 2.")

    if min_periods < 2 or min_periods > window:
        raise ValueError("min_periods must be between 2 and window.")

    if threshold_mad <= 0:
        raise ValueError("threshold_mad must be positive.")

    if min_change_pct < 0:
        raise ValueError("min_change_pct cannot be negative.")

    data = get_daily_revenue()

    if data is None or data.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "total_revenue",
                "orders",
                "units_sold",
                "expected_revenue",
                "deviation",
                "deviation_pct",
                "is_anomaly",
                "anomaly_type",
            ]
        )

    data = data.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["total_revenue"] = pd.to_numeric(
        data["total_revenue"], errors="coerce"
    )

    data = (
        data.dropna(subset=["date", "total_revenue"])
        .sort_values("date")
        .drop_duplicates(subset=["date"], keep="last")
        .reset_index(drop=True)
    )

    revenue = data["total_revenue"]

    # Shift first so each date is compared only with earlier observations.
    historical_revenue = revenue.shift(1)

    data["expected_revenue"] = historical_revenue.rolling(
        window=window,
        min_periods=min_periods,
    ).median()

    robust_scale = historical_revenue.rolling(
        window=window,
        min_periods=min_periods,
    ).apply(_scaled_mad, raw=True)

    data["deviation"] = revenue - data["expected_revenue"]

    data["deviation_pct"] = (
        data["deviation"]
        .div(data["expected_revenue"].abs().replace(0, np.nan))
        .mul(100)
    )

    # Require both a robust statistical deviation and a material
    # percentage change from the historical baseline.
    statistical_threshold = threshold_mad * robust_scale
    percentage_threshold = (
        data["expected_revenue"].abs() * min_change_pct
    )
    required_deviation = np.maximum(
        statistical_threshold.to_numpy(),
        percentage_threshold.to_numpy(),
    )

    eligible = data["expected_revenue"].notna()

    data["is_anomaly"] = (
        eligible
        & data["deviation"].abs().gt(required_deviation)
    )

    data["anomaly_type"] = np.select(
        [
            data["is_anomaly"] & data["deviation"].gt(0),
            data["is_anomaly"] & data["deviation"].lt(0),
        ],
        ["High revenue", "Low revenue"],
        default="Normal",
    )

    data["date"] = data["date"].dt.strftime("%Y-%m-%d")

    return data[
        [
            "date",
            "total_revenue",
            "orders",
            "units_sold",
            "expected_revenue",
            "deviation",
            "deviation_pct",
            "is_anomaly",
            "anomaly_type",
        ]
    ]
