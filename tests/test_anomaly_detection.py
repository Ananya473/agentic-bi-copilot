
import numpy as np
import pandas as pd
import pytest

import src.anomaly_detection as anomaly_detection


def make_daily_data(revenues):
    return pd.DataFrame({
        "date": pd.date_range(
            "2011-01-01", periods=len(revenues), freq="D"
        ).strftime("%Y-%m-%d"),
        "total_revenue": revenues,
        "orders": [10] * len(revenues),
        "units_sold": [100] * len(revenues),
    })


def test_detects_unusually_high_revenue(monkeypatch):
    revenues = [1000.0] * 9 + [3000.0]
    monkeypatch.setattr(
        anomaly_detection,
        "get_daily_revenue",
        lambda: make_daily_data(revenues),
    )

    result = anomaly_detection.detect_revenue_anomalies(
        window=7, min_periods=5
    )

    last = result.iloc[-1]
    assert bool(last["is_anomaly"])
    assert last["anomaly_type"] == "High revenue"
    assert last["expected_revenue"] == 1000.0


def test_detects_unusually_low_revenue(monkeypatch):
    revenues = [1000.0] * 9 + [100.0]
    monkeypatch.setattr(
        anomaly_detection,
        "get_daily_revenue",
        lambda: make_daily_data(revenues),
    )

    result = anomaly_detection.detect_revenue_anomalies(
        window=7, min_periods=5
    )

    last = result.iloc[-1]
    assert bool(last["is_anomaly"])
    assert last["anomaly_type"] == "Low revenue"


def test_normal_revenue_is_not_flagged(monkeypatch):
    monkeypatch.setattr(
        anomaly_detection,
        "get_daily_revenue",
        lambda: make_daily_data([1000.0] * 20),
    )

    result = anomaly_detection.detect_revenue_anomalies(
        window=7, min_periods=5
    )

    assert not result["is_anomaly"].any()


def test_empty_data_returns_empty_result(monkeypatch):
    monkeypatch.setattr(
        anomaly_detection,
        "get_daily_revenue",
        lambda: pd.DataFrame(),
    )

    result = anomaly_detection.detect_revenue_anomalies()

    assert result.empty
    assert "is_anomaly" in result.columns


def test_invalid_window_is_rejected():
    with pytest.raises(ValueError):
        anomaly_detection.detect_revenue_anomalies(window=1)


def test_detector_uses_only_prior_revenue(monkeypatch):
    revenues = [1000.0] * 9 + [3000.0]
    monkeypatch.setattr(
        anomaly_detection,
        "get_daily_revenue",
        lambda: make_daily_data(revenues),
    )

    result = anomaly_detection.detect_revenue_anomalies(
        window=7, min_periods=5
    )

    # The unusual current-day value must not inflate its own baseline.
    assert result.iloc[-1]["expected_revenue"] == 1000.0
