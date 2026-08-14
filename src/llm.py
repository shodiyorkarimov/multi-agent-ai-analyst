"""
Barcha agentlar ishlatadigan umumiy LLM -- endi class proxy orqali (OpenAI-mos format).
"""
from langchain_openai import ChatOpenAI

from src.config import settings  # noqa: F401  (import triggers load_dotenv)

PROXY_BASE_URL = "https://saidazam-litellm-proxy.hf.space/v1"

llm = ChatOpenAI(
    base_url=PROXY_BASE_URL,
    api_key=settings.gemini_api_key,
    model="gemini-flash-lite",
    temperature=0,
)