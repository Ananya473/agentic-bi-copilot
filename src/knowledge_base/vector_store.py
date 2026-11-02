
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

EMBEDDING_MODEL = "gemini-embedding-2"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = PROJECT_ROOT / "src" / "knowledge_base" / "documents"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in .env")

gemini_client = genai.Client(api_key=api_key)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="retail_business_knowledge",
    metadata={"description": "Retail business knowledge documents"}
)


def generate_embedding(text: str, task_type: str) -> list[float]:
    """Generate an embedding using Gemini."""

    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type
        ),
    )

    return response.embeddings[0].values


def ingest_documents() -> int:
    """Read text documents, embed them, and store them in ChromaDB."""

    documents = []
    metadatas = []
    ids = []

    for file_path in sorted(DOCUMENTS_DIR.glob("*.txt")):

        text = file_path.read_text(encoding="utf-8").strip()

        if not text:
            continue

        documents.append(text)

        metadatas.append({
            "source": file_path.name,
            "category": file_path.stem,
        })

        ids.append(file_path.stem)

    if not documents:
        return 0

    embeddings = [
        generate_embedding(
            document,
            "RETRIEVAL_DOCUMENT"
        )
        for document in documents
    ]

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(documents)


def retrieve_documents(
    question: str,
    top_k: int = 3
) -> list[dict]:
    """Retrieve the most relevant documents for a question."""

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if collection.count() == 0:
        raise ValueError(
            "Knowledge base is empty. Ingest documents first."
        )

    query_embedding = generate_embedding(
        question,
        "RETRIEVAL_QUERY"
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )

    retrieved = []

    for i in range(len(results["ids"][0])):

        retrieved.append({
            "document": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "category": results["metadatas"][0][i]["category"],
            "distance": results["distances"][0][i],
        })

    return retrieved
