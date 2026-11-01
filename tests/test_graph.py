
from unittest.mock import patch

from src.graph.workflow import run_graph


def test_graph_executes_planned_tools():

    mock_plan = {
        "source": "Test planner",
        "steps": [
            {
                "tool": "answer_question",
                "reason": "Test SQL question",
            },
            {
                "tool": "detect_anomalies",
                "reason": "Test anomaly detection",
            },
        ],
    }

    with patch(
        "src.graph.nodes.plan_question",
        return_value=mock_plan,
    ), patch(
        "src.graph.nodes._execute_tool",
        side_effect=[
            {"answer": "Test result"},
            {"anomaly_count": 2},
        ],
    ):

        result = run_graph("Analyze retail performance")

    assert len(result["results"]) == 2
    assert result["success"] is True
    assert result["results"][0]["status"] == "completed"
    assert result["results"][1]["status"] == "completed"


def test_graph_handles_tool_failure():

    mock_plan = {
        "source": "Test planner",
        "steps": [
            {
                "tool": "answer_question",
                "reason": "Test SQL question",
            },
        ],
    }

    with patch(
        "src.graph.nodes.plan_question",
        return_value=mock_plan,
    ), patch(
        "src.graph.nodes._execute_tool",
        side_effect=RuntimeError("Test error"),
    ):

        result = run_graph("Test question")

    assert result["success"] is False
    assert result["results"][0]["status"] == "failed"


def test_graph_rejects_empty_question():

    import pytest

    with pytest.raises(ValueError):
        run_graph("")
