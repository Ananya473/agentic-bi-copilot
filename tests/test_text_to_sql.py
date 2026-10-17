
import pytest

from src.text_to_sql import generate_sql
from src.question_service import answer_with_sql


def test_category_question_generates_select():
    query = generate_sql("Show revenue by category")
    assert query.strip().upper().startswith("SELECT")
    assert "GROUP BY" in query.upper()
    assert "category" in query.lower()


def test_monthly_question_generates_sql():
    query = generate_sql("Show monthly revenue")
    assert "substr(order_date, 1, 7)" in query
    assert "GROUP BY" in query
    assert "SUM(revenue)" in query


def test_unsupported_question_is_rejected():
    with pytest.raises(ValueError):
        generate_sql("What is the weather today?")


def test_empty_question_is_rejected():
    with pytest.raises(ValueError):
        generate_sql("")


def test_question_service_returns_results():
    result = answer_with_sql("Show revenue by category")
    assert not result["data"].empty
    assert "category" in result["data"].columns
    assert "total_revenue" in result["data"].columns
