
from src.agents.report_agent import report_agent


def test_report_agent_combines_data_analyst_results():
    results = [
        {
            "agent": "data_analyst",
            "status": "completed",
            "result": {
                "source": "Rule-based",
                "sql": "SELECT SUM(Quantity) FROM sales",
                "data": None,
            },
        }
    ]

    report = report_agent(
        "What is total revenue?",
        "Gemini AI",
        results,
    )

    assert report["status"] == "completed"
    assert "Business Intelligence Investigation Report" in report["report"]
    assert "Business Query Results" in report["report"]


def test_report_agent_includes_knowledge_findings():
    results = [
        {
            "agent": "knowledge_researcher",
            "status": "completed",
            "answer": "The return policy allows eligible returns.",
            "sources": ["return_policy.txt"],
        }
    ]

    report = report_agent(
        "Explain the return policy.",
        "Gemini AI",
        results,
    )

    assert report["status"] == "completed"
    assert "Business Knowledge Research" in report["report"]
    assert "return_policy.txt" in report["report"]


def test_report_agent_handles_failed_agent():
    results = [
        {
            "agent": "data_analyst",
            "status": "failed",
            "error": "SQL execution failed.",
        }
    ]

    report = report_agent(
        "What is total revenue?",
        "Rule-based fallback",
        results,
    )

    assert report["status"] == "completed"
    assert "SQL execution failed" in report["report"]


def test_report_agent_rejects_empty_question():
    import pytest

    with pytest.raises(ValueError):
        report_agent("", "Gemini AI", [])


def test_report_agent_handles_empty_agent_results():
    report = report_agent(
        "Give me a business overview.",
        "Rule-based fallback",
        [],
    )

    assert report["status"] == "completed"
    assert "Execution Summary" in report["report"]
