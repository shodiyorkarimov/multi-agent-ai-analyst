"""
F3 -- Retriever agent: savolga eng mos hujjat bo'laklarini Qdrant'dan topib beradi.
"""
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from src.config import settings  # noqa: F401  (import triggers load_dotenv)
from src.ingestion import COLLECTION_NAME, QDRANT_PATH
from src.state import AgentState

_vectorstore: QdrantVectorStore | None = None


def get_vectorstore() -> QdrantVectorStore:
    """F2'da yaratilgan Qdrant kolleksiyasiga ulanadi (qayta ingestion qilmasdan)."""
    global _vectorstore
    if _vectorstore is None:
        embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")
        client = QdrantClient(path=QDRANT_PATH)
        _vectorstore = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
        )
    return _vectorstore


def retriever_agent(state: AgentState) -> dict:
    """RAG agent: state['question']ga eng mos 4 ta bo'lakni topib, state'ga qo'shadi."""
    vectorstore = get_vectorstore()
    docs = vectorstore.as_retriever(search_kwargs={"k": 4}).invoke(state["question"])
    return {
        "documents": [d.page_content for d in docs],
        "steps": state["steps"] + ["retriever"],
    }


if __name__ == "__main__":
    from src.state import new_state

    test_state = new_state("What is the law of demand?")
    result = retriever_agent(test_state)

    print(f"Bajarilgan qadamlar: {result['steps']}")
    print(f"Topilgan bo'laklar soni: {len(result['documents'])}")
    for i, chunk in enumerate(result["documents"], 1):
        print(f"\n[{i}] {chunk[:200]}")