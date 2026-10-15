"""
Barcha agentlar ishlatadigan umumiy LLM va embedding -- to'g'ridan-to'g'ri Google AI Studio (Gemini) orqali.
Kalit: GOOGLE_API_KEY (.env faylida)
"""
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.config import settings

# Model nomi eskirsa, faqat shu ikki qatorni almashtirasiz.
CHAT_MODEL = "gemini-3.5-flash-lite"
EMBEDDING_MODEL = "models/gemini-embedding-001"  # o'lchami 3072 (Qdrant'dagi bilan bir xil)

llm = ChatGoogleGenerativeAI(
    model=CHAT_MODEL,
    google_api_key=settings.google_api_key,
    temperature=0,
    max_retries=2,
    timeout=60,
)


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=settings.google_api_key,
    )
