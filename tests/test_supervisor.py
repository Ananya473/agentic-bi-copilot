
from unittest.mock import patch

from src.agents.supervisor import (
    plan_agents,
    rule_based_routing,
)


def test_routes_revenue_question_to_data_analyst():

    result = rule_based_routing("What is total revenue?")

    names = [item["agent"] for item in result]

    assert "data_analyst" in names


def test_routes_investigation_question():

    result = rule_based_routing("Why did revenue decline?")

    names = [item["agent"] for item in result]

    assert "investigator" in names
    assert "data_analyst" in names


def test_routes_policy_question_to_knowledge_researcher():

    result = rule_based_routing("Explain our return policy.")

    names = [item["agent"] for item in result]

    assert "knowledge_researcher" in names


def test_routes_combined_question_to_multiple_agents():

    result = rule_based_routing(
        "Why did revenue decline and could promotions explain it?"
    )

    names = [item["agent"] for item in result]

    assert "investigator" in names
    assert "knowledge_researcher" in names
    assert "data_analyst" in names


def test_supervisor_uses_fallback_when_gemini_unavailable():

    with patch(
        "src.agents.supervisor.genai.Client",
        side_effect=RuntimeError("Gemini unavailable"),
    ):
        result = plan_agents("What is total revenue?")

    assert result["source"] == "Rule-based fallback"
    assert result["agents"][0]["agent"] == "data_analyst"


def test_supervisor_rejects_empty_question():

    import pytest

    with pytest.raises(ValueError):
        plan_agents("")
