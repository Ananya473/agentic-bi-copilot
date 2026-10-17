
from src.insights import answer_business_question


def test_total_revenue():
    result = answer_business_question("What is our total revenue?")
    assert "₹10,666,685" in result["answer"]
    assert "19960 orders" in result["answer"]


def test_highest_revenue_category():
    result = answer_business_question(
        "Which category has the highest revenue?"
    )
    assert "Uncategorized" in result["answer"]


def test_monthly_revenue():
    result = answer_business_question(
        "Which month has the highest revenue?"
    )
    assert "2011-11" in result["answer"]
