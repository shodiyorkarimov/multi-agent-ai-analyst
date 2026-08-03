"""
Barcha agentlar ishlatadigan umumiy LLM (Gemini chat modeli).
"""
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import settings  # noqa: F401  (import triggers load_dotenv)

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)