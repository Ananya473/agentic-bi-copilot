
from src.analytics import (
    get_total_revenue,
    get_revenue_by_category,
    get_top_products,
    get_monthly_revenue,
)


def answer_business_question(question: str) -> dict:
    """Answer supported business questions using SQL analytics."""

    question = question.lower().strip()

    if not question:
        return {
            "answer": "Please enter a business question.",
            "data": None,
        }

    # Category revenue questions
    if any(word in question for word in ["category", "categories"]):
        data = get_revenue_by_category()

        if data.empty:
            return {"answer": "No category data is available.", "data": data}

        top = data.iloc[0]
        return {
            "answer": (
                f"{top['category']} generates the highest revenue "
                f"at ₹{top['total_revenue']:,.0f}."
            ),
            "data": data,
        }

    # Monthly trend questions
    if any(word in question for word in ["month", "monthly", "trend"]):
        data = get_monthly_revenue()

        if data.empty:
            return {"answer": "No monthly data is available.", "data": data}

        top = data.loc[data["total_revenue"].idxmax()]
        return {
            "answer": (
                f"The highest-revenue month is {top['month']}, "
                f"with ₹{top['total_revenue']:,.0f}."
            ),
            "data": data,
        }

    # Product performance questions
    if any(word in question for word in ["product", "products", "units"]):
        data = get_top_products()

        if data.empty:
            return {"answer": "No product data is available.", "data": data}

        top = data.iloc[0]
        return {
            "answer": (
                f"{top['product']} sold the most units: "
                f"{int(top['units_sold'])}."
            ),
            "data": data,
        }

    # Overall KPI questions
    if any(word in question for word in ["revenue", "sales", "orders", "total"]):
        data = get_total_revenue().iloc[0]

        return {
            "answer": (
                f"Total revenue is ₹{data['total_revenue']:,.0f}, "
                f"across {int(data['total_orders'])} orders, "
                f"with {int(data['units_sold'])} units sold."
            ),
            "data": None,
        }

    return {
        "answer": (
            "I can currently answer questions about total revenue, "
            "product categories, product performance, and monthly trends."
        ),
        "data": None,
    }
