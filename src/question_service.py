
from src.text_to_sql import generate_sql_with_source
from src.query_engine import execute_read_only_query


def answer_with_sql(question: str) -> dict:
    query, source = generate_sql_with_source(question)
    data = execute_read_only_query(query)

    return {
        "question": question,
        "sql": query.strip(),
        "data": data,
        "source": source,
    }
