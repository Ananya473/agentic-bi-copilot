
import os

from dotenv import load_dotenv
from google import genai

from src.knowledge_base.vector_store import retrieve_documents


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def knowledge_researcher_agent(question: str) -> dict:
    """
    Knowledge Researcher Agent:
    Retrieves relevant business documents and generates
    an answer grounded in the retrieved context.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    try:
        documents = retrieve_documents(question, top_k=3)

        context = "\n\n".join(
            f"Source: {doc['source']}\n"
            f"Content: {doc['document']}"
            for doc in documents
        )

        prompt = f"""
You are a retail business knowledge researcher.

Answer the user's question using ONLY the provided documents.

Rules:
- Do not invent business policies or facts.
- If the documents do not contain enough information,
  clearly state that.
- Distinguish documented information from assumptions.
- Mention the source filenames used in your answer.

Retrieved documents:
{context}

User question:
{question}
"""

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        return {
            "agent": "knowledge_researcher",
            "status": "completed",
            "question": question,
            "answer": response.text,
            "sources": [
                doc["source"] for doc in documents
            ],
            "retrieved_documents": documents,
        }

    except Exception as error:
        return {
            "agent": "knowledge_researcher",
            "status": "failed",
            "question": question,
            "error": str(error),
        }
