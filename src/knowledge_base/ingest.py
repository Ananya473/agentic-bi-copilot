
from src.knowledge_base.vector_store import ingest_documents


if __name__ == "__main__":
    count = ingest_documents()

    print(f"Successfully indexed {count} documents.")
