
from src.question_service import answer_with_sql


def data_analyst_agent(question: str) -> dict:
    """
    Data Analyst Agent:
    Answers business questions using the existing SQL service.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    try:
        result = answer_with_sql(question.strip())

        return {
            "agent": "data_analyst",
            "status": "completed",
            "question": question,
            "result": result,
        }

    except Exception as error:
        return {
            "agent": "data_analyst",
            "status": "failed",
            "question": question,
            "error": str(error),
        }
