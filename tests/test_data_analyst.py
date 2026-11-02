
from unittest.mock import patch

from src.agents.data_analyst import data_analyst_agent


def test_data_analyst_returns_sql_results():

    mock_result = {
        "question": "What is total revenue?",
        "sql": "SELECT SUM(Revenue) FROM sales",
        "data": [{"total_revenue": 100000}],
        "source": "rule_based",
    }

    with patch(
        "src.agents.data_analyst.answer_with_sql",
        return_value=mock_result,
    ):
        result = data_analyst_agent("What is total revenue?")

    assert result["agent"] == "data_analyst"
    assert result["status"] == "completed"
    assert result["result"]["data"][0]["total_revenue"] == 100000


def test_data_analyst_handles_failure():

    with patch(
        "src.agents.data_analyst.answer_with_sql",
        side_effect=RuntimeError("SQL error"),
    ):
        result = data_analyst_agent("What is total revenue?")

    assert result["status"] == "failed"
    assert "SQL error" in result["error"]


def test_data_analyst_rejects_empty_question():

    import pytest

    with pytest.raises(ValueError):
        data_analyst_agent("")
