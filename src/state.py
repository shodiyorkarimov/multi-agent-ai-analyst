"""
F1 -- Shared State: barcha agentlar shu bitta holat (state) orqali ma'lumot almashadi.
"""
from typing import List, Optional, TypedDict


class AgentState(TypedDict):
    question: str                  # foydalanuvchi savoli
    plan: str                      # supervisor tanlagan keyingi agent nomi
    documents: List[str]           # retriever/web to'plagan matn parchalari
    sql_result: Optional[str]      # data(SQL) agent natijasi
    code_result: Optional[str]     # code agent natijasi
    memory_context: List[str]      # F10: xotiradan topilgan tegishli oldingi suhbatlar
    answer: str                    # yakuniy javob
    steps: List[str]               # qaysi agentlar ishga tushgani (trace uchun)
    revisions: int                 # critic necha marta qaytarganini sanaydi


def new_state(question: str) -> AgentState:
    """Yangi savol uchun bo'sh boshlang'ich state yaratadi."""
    return AgentState(
        question=question,
        plan="",
        documents=[],
        sql_result=None,
        code_result=None,
        memory_context=[],
        answer="",
        steps=[],
        revisions=0,
    )