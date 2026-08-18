"""
F4 -- Web agent: Tavily orqali hujjatlardan tashqarida (jonli) internet qidiruvi.
"""
from tavily import TavilyClient

from src.config import settings
from src.state import AgentState


def web_agent(state: AgentState) -> dict:
    """Tavily orqali joriy/tashqi ma'lumot qidiradi. Kalit bo'lmasa, xatosiz o'tkazib yuboradi."""
    if not settings.tavily_api_key:
        print("TAVILY_API_KEY topilmadi -- web qidiruv o'tkazib yuborildi.")
        return {"steps": state["steps"] + ["web (skipped)"]}

    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(state["question"], max_results=4)
    hits = response.get("results", [])

    tagged_hits = [
        f"[manba: {h.get('url', 'internet')}] {h['content']}" for h in hits
    ]

    return {
        "documents": state["documents"] + tagged_hits,
        "steps": state["steps"] + ["web"],
    }


if __name__ == "__main__":
    from src.state import new_state

    test_state = new_state("2026-yilda Gemini API narxlari qanday?")
    result = web_agent(test_state)

    print(f"Bajarilgan qadamlar: {result['steps']}")
    print(f"Topilgan natijalar soni: {len(result.get('documents', []))}")
    for i, doc in enumerate(result.get("documents", []), 1):
        print(f"\n[{i}] {doc[:200]}")