"""
F7-F9 -- Supervisor, Critic, va ularni bog'laydigan LangGraph grafi.
Hozircha faqat F7 (supervisor) qismi.
"""
from pydantic import BaseModel, Field

from src.llm import llm
from src.state import AgentState


class Route(BaseModel):
    next: str = Field(description="retriever|web|data|code|finish")


def supervisor(state: AgentState) -> dict:
    """Savolga qarab, keyingi qaysi agent ishga tushishi kerakligini hal qiladi."""
    router = llm.with_structured_output(Route)
    decision = router.invoke(
        f"Savol: {state['question']}\n"
        f"Hozirgacha bajarilgan qadamlar: {state['steps']}\n\n"
        "Quyidagi agentlardan eng mosini tanla:\n"
        "- retriever: lokal hujjatlar bazasidan qidiradi. Bazada IQTISODIYOT DARSLIKLARI bor "
        "(talab-taklif qonuni, elastiklik, narx, bozor tuzilishi, iste'molchi tanlovi kabi "
        "klassik iqtisodiyot tushunchalari). Shu mavzudagi savollar uchun buni tanla.\n"
        "- web: internetdan joriy/yangi ma'lumot qidiradi (masalan bugungi narxlar, so'nggi "
        "yangiliklar, hujjatlarda yo'q joriy voqealar).\n"
        "- data: kompaniya SQL bazasidan (xodimlar, sotuvlar) sonli javob oladi.\n"
        "- code: matematik hisob-kitob yoki agregatsiya talab qiladigan savollar uchun.\n"
        "- finish: agar javob uchun yetarli ma'lumot allaqachon yig'ilgan bo'lsa.\n\n"
        "Eng mos variantni tanla."
    )
    return {
        "plan": decision.next,
        "steps": state["steps"] + [f"supervisor->{decision.next}"],
    }


if __name__ == "__main__":
    from src.state import new_state

    for question in [
        "How many employees work in Engineering?",
        "What is the law of demand?",
    ]:
        state = new_state(question)
        result = supervisor(state)
        print(f"Savol: {question}")
        print(f"  -> Tanlangan agent: {result['plan']}")
        print(f"  -> steps: {result['steps']}\n")