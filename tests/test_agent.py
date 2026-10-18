
import pandas as pd
import pytest

import src.agent as agent


def test_country_question_selects_business_query_tool():
    plan = agent._rule_based_plan(
        "Which countries generate the most revenue?"
    )

    assert len(plan) == 1
    assert plan[0]["tool"] == "answer_question"


def test_investigation_and_anomaly_question_selects_both_tools():
    plan = agent._rule_based_plan(
        "Why did revenue decline and were there anomalies?"
    )

    selected_tools = [step["tool"] for step in plan]

    assert "investigate_revenue_change" in selected_tools
    assert "detect_anomalies" in selected_tools


def test_planner_uses_fallback_when_gemini_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        agent,
        "_plan_with_gemini",
        lambda question: None,
    )

    result = agent.plan_question("Detect revenue anomalies")

    assert result["source"] == "Rule-based fallback"
    assert result["steps"][0]["tool"] == "detect_anomalies"


def test_planner_accepts_a_gemini_plan(monkeypatch):
    gemini_steps = [
        {
            "tool": "investigate_revenue_change",
            "reason": "Compare monthly revenue and identify contributors.",
        }
    ]

    monkeypatch.setattr(
        agent,
        "_plan_with_gemini",
        lambda question: gemini_steps,
    )

    result = agent.plan_question("Why did revenue change?")

    assert result["source"] == "Gemini AI"
    assert result["steps"] == gemini_steps


def test_planner_rejects_empty_questions():
    with pytest.raises(ValueError, match="business question"):
        agent.plan_question("   ")


def test_run_agent_executes_selected_tool(monkeypatch):
    monkeypatch.setattr(
        agent,
        "_plan_with_gemini",
        lambda question: [
            {
                "tool": "answer_question",
                "reason": "Retrieve country-level revenue.",
            }
        ],
    )

    monkeypatch.setattr(
        agent,
        "answer_with_sql",
        lambda question: {
            "sql": "SELECT country, SUM(revenue) FROM sales GROUP BY country",
            "data": pd.DataFrame({
                "country": ["United Kingdom"],
                "total_revenue": [1000.0],
            }),
            "source": "Test",
        },
    )

    result = agent.run_agent(
        "Which countries generate the most revenue?"
    )

    assert result["success"] is True
    assert result["planner_source"] == "Gemini AI"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "completed"
    assert result["results"][0]["tool"] == "answer_question"


def test_run_agent_reports_tool_failure(monkeypatch):
    monkeypatch.setattr(
        agent,
        "_plan_with_gemini",
        lambda question: [
            {
                "tool": "detect_anomalies",
                "reason": "Inspect unusual revenue values.",
            }
        ],
    )

    def failing_detector():
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(
        agent,
        "detect_revenue_anomalies",
        failing_detector,
    )

    result = agent.run_agent("Detect revenue anomalies")

    assert result["success"] is False
    assert result["results"][0]["status"] == "failed"
    assert "Simulated database failure" in result["results"][0]["error"]


def test_agent_continues_after_a_tool_failure(monkeypatch):
    monkeypatch.setattr(
        agent,
        "_plan_with_gemini",
        lambda question: [
            {
                "tool": "investigate_revenue_change",
                "reason": "Compare revenue periods.",
            },
            {
                "tool": "detect_anomalies",
                "reason": "Detect unusual revenue.",
            },
        ],
    )

    def failing_investigation():
        raise RuntimeError("Investigation unavailable")

    monkeypatch.setattr(
        agent,
        "investigate_revenue_change",
        failing_investigation,
    )

    monkeypatch.setattr(
        agent,
        "detect_revenue_anomalies",
        lambda: pd.DataFrame({
            "date": ["2024-01-01"],
            "is_anomaly": [True],
            "anomaly_type": ["High revenue"],
        }),
    )

    result = agent.run_agent(
        "Investigate revenue changes and anomalies"
    )

    assert result["success"] is True
    assert result["results"][0]["status"] == "failed"
    assert result["results"][1]["status"] == "completed"
    assert result["results"][1]["output"]["anomaly_count"] == 1


def test_agent_rejects_unknown_tools():
    with pytest.raises(ValueError, match="not allowed"):
        agent._execute_tool("arbitrary_tool", "test question")
