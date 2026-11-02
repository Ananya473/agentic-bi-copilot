
from unittest.mock import patch, MagicMock

from src.agents.knowledge_researcher import (
    knowledge_researcher_agent,
)


def test_knowledge_researcher_returns_answer():

    mock_documents = [
        {
            "document": "Stock shortages can reduce revenue.",
            "source": "inventory_management.txt",
            "category": "inventory_management",
            "distance": 0.2,
        }
    ]

    mock_response = MagicMock()
    mock_response.text = "Stock shortages can reduce revenue."

    with patch(
        "src.agents.knowledge_researcher.retrieve_documents",
        return_value=mock_documents,
    ), patch(
        "src.agents.knowledge_researcher.client.models.generate_content",
        return_value=mock_response,
    ):

        result = knowledge_researcher_agent(
            "What happens when products are out of stock?"
        )

    assert result["status"] == "completed"
    assert result["agent"] == "knowledge_researcher"
    assert "inventory_management.txt" in result["sources"]


def test_knowledge_researcher_handles_failure():

    with patch(
        "src.agents.knowledge_researcher.retrieve_documents",
        side_effect=RuntimeError("Retrieval failed"),
    ):

        result = knowledge_researcher_agent("Test question")

    assert result["status"] == "failed"
    assert "Retrieval failed" in result["error"]


def test_knowledge_researcher_rejects_empty_question():

    import pytest

    with pytest.raises(ValueError):
        knowledge_researcher_agent("")
