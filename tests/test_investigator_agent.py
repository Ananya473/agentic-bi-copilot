
import pandas as pd
from unittest.mock import patch

from src.agents.investigator_agent import investigator_agent


def test_investigator_agent_success():

    mock_investigation = {
        "summary": "Revenue declined by 10%.",
        "revenue_change": -10000,
    }

    mock_anomalies = pd.DataFrame([
        {
            "date": "2011-01-15",
            "total_revenue": 5000,
            "is_anomaly": True,
            "anomaly_type": "Low revenue",
        },
        {
            "date": "2011-01-16",
            "total_revenue": 10000,
            "is_anomaly": False,
            "anomaly_type": "Normal",
        },
    ])

    with patch(
        "src.agents.investigator_agent.investigate_revenue_change",
        return_value=mock_investigation,
    ), patch(
        "src.agents.investigator_agent.detect_revenue_anomalies",
        return_value=mock_anomalies,
    ):

        result = investigator_agent()

    assert result["status"] == "completed"
    assert result["results"]["revenue_investigation"] == mock_investigation
    assert len(result["results"]["anomalies"]) == 1


def test_investigator_agent_handles_partial_failure():

    with patch(
        "src.agents.investigator_agent.investigate_revenue_change",
        return_value={"summary": "Revenue increased."},
    ), patch(
        "src.agents.investigator_agent.detect_revenue_anomalies",
        side_effect=RuntimeError("Detection failed"),
    ):

        result = investigator_agent()

    assert result["status"] == "partial"
    assert "revenue_investigation" in result["results"]
    assert "anomaly_detection" in result["errors"]


def test_investigator_agent_handles_complete_failure():

    with patch(
        "src.agents.investigator_agent.investigate_revenue_change",
        side_effect=RuntimeError("Investigation failed"),
    ), patch(
        "src.agents.investigator_agent.detect_revenue_anomalies",
        side_effect=RuntimeError("Detection failed"),
    ):

        result = investigator_agent()

    assert result["status"] == "failed"
    assert len(result["errors"]) == 2
