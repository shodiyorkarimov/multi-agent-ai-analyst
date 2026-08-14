"""
F2 -- Ingestion & Vector Store: load documents -> chunk -> embed -> Qdrant.
"""
import time
from pathlib import Path
from typing import List

import docx2txt
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from qdrant_client import QdrantClient

from src.config import settings  # noqa: F401  (import triggers load_dotenv)

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"
QDRANT_PATH = str(Path(__file__).resolve().parent.parent / "data" / "qdrant_storage")
COLLECTION_NAME = "company_docs"

_qdrant_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Butun loyiha bo'ylab bitta umumiy Qdrant clientini qaytaradi (lokal rejim faqat bitta clientga ruxsat beradi)."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(path=QDRANT_PATH)
    return _qdrant_client

# Katta PDF fayllarda tezkor sinov qilish uchun: masalan 20 ga o'zgartiring
# (faqat birinchi 20 sahifa o'qiladi). To'liq kitobni ishlatish uchun None qoldiring.
MAX_PAGES_PER_PDF: int | None = 250


def _load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = reader.pages[:MAX_PAGES_PER_PDF] if MAX_PAGES_PER_PDF else reader.pages
    return "\n".join(page.extract_text() or "" for page in pages)


def _load_docx(path: Path) -> str:
    return docx2txt.process(str(path))


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


LOADERS = {
    ".pdf": _load_pdf,
    ".docx": _load_docx,
    ".txt": _load_text,
    ".md": _load_text,
}


def load_documents(docs_dir: Path = DOCS_DIR) -> List[Document]:
    """data/docs papkasidagi barcha qo'llab-quvvatlanadigan fayllarni o'qiydi."""
    documents: List[Document] = []
    for file_path in sorted(docs_dir.glob("*")):
        loader = LOADERS.get(file_path.suffix.lower())
        if loader is None:
            print(f"O'tkazib yuborildi (qo'llab-quvvatlanmaydi): {file_path.name}")
            continue
        text = loader(file_path)
        if not text.strip():
            print(f"Ogohlantirish: {file_path.name} dan matn chiqmadi (bo'sh)")
            continue
        documents.append(Document(page_content=text, metadata={"source": file_path.name}))
        print(f"Yuklandi: {file_path.name} ({len(text)} belgi)")
    return documents


def chunk_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_documents(documents)


def build_vectorstore(chunks: List[Document]) -> QdrantVectorStore:
    embeddings = OpenAIEmbeddings(
        base_url="https://saidazam-litellm-proxy.hf.space/v1",
        api_key=settings.gemini_api_key,
        model="gemini-embedding",
    )

    # Birinchi bo'lak orqali bo'sh kolleksiya yaratamiz (vektor o'lchami shundan aniqlanadi)
    vectorstore = QdrantVectorStore.from_documents(
        documents=chunks[:1],
        embedding=embeddings,
        path=QDRANT_PATH,
        collection_name=COLLECTION_NAME,
        force_recreate=True,
    )

    remaining = chunks[1:]
    batch_size = 20  # bepul tarif (100 so'rov/daqiqa) limitiga tegib ketmaslik uchun kichik ushlab turamiz

    for i in range(0, len(remaining), batch_size):
        batch = remaining[i : i + batch_size]
        _add_with_retry(vectorstore, batch)
        done = min(i + batch_size, len(remaining)) + 1
        print(f"  {done}/{len(chunks)} bo'lak Qdrant'ga qo'shildi")
        time.sleep(3)  # navbatdagi so'rovlar oqimidan oldin kichik pauza

    return vectorstore


def _add_with_retry(vectorstore: QdrantVectorStore, batch: List[Document], max_retries: int = 6) -> None:
    """RESOURCE_EXHAUSTED (429) xatosida kutib, qayta urinadi."""
    for attempt in range(1, max_retries + 1):
        try:
            vectorstore.add_documents(batch)
            return
        except Exception as e:  # noqa: BLE001
            rate_limited = "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)
            if not rate_limited or attempt == max_retries:
                raise
            wait = 15 * attempt
            print(f"  Bepul tarif limitiga tegdik, {wait}s kutamiz (urinish {attempt}/{max_retries})...")
            time.sleep(wait)


def main() -> None:
    documents = load_documents()
    if not documents:
        print("data/docs papkasida hujjat topilmadi. Fayl joylashtirib qayta urining.")
        return

    chunks = chunk_documents(documents)
    print(f"\n{len(documents)} ta hujjat -> {len(chunks)} ta bo'lakka (chunk) bo'lindi.")

    vectorstore = build_vectorstore(chunks)
    print(f"Qdrant'ga saqlandi: '{COLLECTION_NAME}' kolleksiyasi, {QDRANT_PATH}")

    query = "law of supply and demand"
    results = vectorstore.similarity_search(query, k=2)
    print(f"\nSinov qidiruvi: '{query}'")
    for i, doc in enumerate(results, 1):
        print(f"\n[{i}] manba: {doc.metadata.get('source')}")
        print(doc.page_content[:200])


if __name__ == "__main__":
    main()