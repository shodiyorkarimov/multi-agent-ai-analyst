"""
F10 -- Long-term memory: o'tgan savol-javoblarni saqlaydi va tegishlilarini qidirib topadi.
"""
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import Distance, VectorParams

from src.config import settings  # noqa: F401  (load_dotenv triggeri)
from src.ingestion import get_qdrant_client

MEMORY_COLLECTION = "conversation_memory"

_memory_store: QdrantVectorStore | None = None


def get_memory_store() -> QdrantVectorStore:
    """Xotira uchun alohida Qdrant kolleksiyasi (hujjatlar kolleksiyasidan mustaqil, lekin bitta umumiy client orqali)."""
    global _memory_store
    if _memory_store is None:
        embeddings = OpenAIEmbeddings(
        base_url="https://saidazam-litellm-proxy.hf.space/v1",
        api_key=settings.gemini_api_key,
        model="gemini-embedding",
    )
        client = get_qdrant_client()

        if not client.collection_exists(MEMORY_COLLECTION):
            vector_size = len(embeddings.embed_query("o'lcham aniqlash uchun sinov matni"))
            client.create_collection(
                collection_name=MEMORY_COLLECTION,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

        _memory_store = QdrantVectorStore(
            client=client,
            collection_name=MEMORY_COLLECTION,
            embedding=embeddings,
        )
    return _memory_store


def add_turn(question: str, answer: str) -> None:
    """Bir savol-javob juftligini xotiraga qo'shadi."""
    store = get_memory_store()
    store.add_documents([Document(page_content=f"Savol: {question}\nJavob: {answer}")])


def recall(question: str, k: int = 3) -> list[str]:
    """Yangi savolga eng tegishli o'tgan suhbatlarni qidirib topadi."""
    store = get_memory_store()
    docs = store.similarity_search(question, k=k)
    return [d.page_content for d in docs]


if __name__ == "__main__":
    add_turn(
        "How many employees work in Engineering?",
        "Engineering bo'limida 2 nafar xodim ishlaydi.",
    )
    add_turn(
        "What is the law of demand?",
        "Talab qonuni: narx oshsa, talab qilingan miqdor kamayadi (boshqa sharoitlar teng bo'lganda).",
    )

    print("--- Xotiradan qidiruv: 'Engineering haqida yana savol' ---")
    for item in recall("Tell me more about the Engineering department", k=2):
        print(f"- {item}\n")