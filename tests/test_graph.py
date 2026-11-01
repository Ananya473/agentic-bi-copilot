
from unittest.mock import patch

from src.graph.workflow import run_graph


def test_multi_agent_workflow_executes_selected_agents():
    plan = {
        "source": "Test Supervisor",
        "agents": [
            {"agent": "data_analyst", "reason": "SQL analysis"},
            {"agent": "knowledge_researcher", "reason": "Policy research"},
            {"agent": "investigator", "reason": "Revenue investigation"},
        ],
    }

    with (
        patch("src.graph.nodes.plan_agents", return_value=plan),
        patch(
            "src.graph.nodes.AGENT_FUNCTIONS",
            {
                "data_analyst": lambda q: {
                    "agent": "data_analyst",
                    "status": "completed",
                    "result": {
                        "source": "Test SQL",
                        "sql": "SELECT 100",
                        "data": None,
                    },
                },
                "knowledge_researcher": lambda q: {
                    "agent": "knowledge_researcher",
                    "status": "completed",
                    "answer": "Test knowledge finding.",
                    "sources": ["test.txt"],
                },
                "investigator": lambda: {
                    "agent": "investigator",
                    "status": "completed",
                    "results": {
                        "revenue_investigation": {
                            "summary": "Revenue investigation test."
                        },
                        "anomalies": [],
                    },
                    "errors": {},
                },
            },
        ),
    ):
        result = run_graph("Analyze retail performance.")

    assert result["success"] is True
    assert result["execution_trace"] == [
        "data_analyst",
        "knowledge_researcher",
        "investigator",
    ]
    assert len(result["agent_results"]) == 3
    assert result["report_status"] == "completed"
    assert "Business Intelligence Investigation Report" in result["final_report"]
    assert "Test knowledge finding." in result["final_report"]


def test_workflow_handles_failed_specialist():
    plan = {
        "source": "Test Supervisor",
        "agents": [
            {"agent": "data_analyst", "reason": "SQL analysis"},
        ],
    }

    with (
        patch("src.graph.nodes.plan_agents", return_value=plan),
        patch(
            "src.graph.nodes.AGENT_FUNCTIONS",
            {
                "data_analyst": lambda q: {
                    "agent": "data_analyst",
                    "status": "failed",
                    "error": "Test SQL failure",
                },
            },
        ),
    ):
        result = run_graph("What is total revenue?")

    assert result["success"] is False
    assert result["report_status"] == "completed"
    assert "Test SQL failure" in result["final_report"]


def test_workflow_rejects_empty_question():
    import pytest

    with pytest.raises(ValueError):
        run_graph("")


def test_workflow_rejects_whitespace_question():
    import pytest

    with pytest.raises(ValueError):
        run_graph("   ")
