"""
F7-F9 -- Supervisor, Critic, va ularni bog'laydigan LangGraph grafi.
"""
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from src.agents.code_agent import code_agent
from src.agents.data_sql import data_agent
from src.llm import llm
from src.agents.retriever import retriever_agent
from src.state import AgentState
from src.agents.web import web_agent


class Route(BaseModel):
    next: str = Field(description="retriever|web|data|code|finish")


def generate(state: AgentState) -> dict:
    """Yig'ilgan barcha dalillar (hujjatlar, SQL, kod natijasi) asosida yakuniy javobni yozadi."""
    prompt = (
        f"Savol: {state['question']}\n\n"
        f"Hujjatlardan topilgan dalillar: {state['documents']}\n"
        f"SQL natijasi: {state['sql_result']}\n"
        f"Kod natijasi: {state['code_result']}\n\n"
        "Yuqoridagi dalillarga asoslanib, savolga aniq va qisqa javob yoz. "
        "Faqat yuqorida berilgan dalillardan foydalan, o'zingdan narsa qo'shma. "
        "Agar dalillar yetarli bo'lmasa, shuni aytib o't."
    )
    answer = llm.invoke(prompt).text.strip()
    return {
        "answer": answer,
        "steps": state["steps"] + ["generate"],
    }


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


class Verdict(BaseModel):
    ok: bool = Field(description="Javob to'g'ri va dalillar bilan to'liq asoslanganmi")
    reason: str = Field(description="Qisqacha sabab")


def critic(state: AgentState) -> dict:
    """Yozilgan javobni yig'ilgan dalillar bilan solishtirib, tasdiqlaydi yoki qaytaradi."""
    verifier = llm.with_structured_output(Verdict)
    verdict = verifier.invoke(
        f"Savol: {state['question']}\n"
        f"Dalillar (hujjatlar): {state['documents']}\n"
        f"Dalillar (SQL): {state['sql_result']}\n"
        f"Dalillar (kod): {state['code_result']}\n"
        f"Yozilgan javob: {state['answer']}\n\n"
        "Bu javob to'g'rimi VA to'liq ravishda yuqoridagi dalillarga asoslanganmi? "
        "Agar dalillarda yo'q narsa aytilgan bo'lsa yoki noto'g'ri bo'lsa, ok=False de."
    )
    print(f"  [critic] ok={verdict.ok}, sabab: {verdict.reason}")
    return {
        "approved": verdict.ok,
        "revisions": state["revisions"] + (0 if verdict.ok else 1),
    }


MAX_REVISIONS = 2  # necha marta qayta yozishga urinishga ruxsat (grafning cheksiz aylanishini oldini oladi)


def route_after_critic(state: AgentState) -> str:
    """Critic natijasidan keyin: javob tasdiqlandimi (finish) yoki qayta ishlash kerakmi (revise)?"""
    if state["approved"]:
        return "finish"
    if state["revisions"] >= MAX_REVISIONS:
        print(f"  [route_after_critic] revisions limiti ({MAX_REVISIONS}) tugadi -- majburan finish")
        return "finish"
    return "revise"


def build_graph():
    """Barcha agentlarni bitta LangGraph grafiga ulaydi va uni compile qiladi."""
    g = StateGraph(AgentState)

    g.add_node("supervisor", supervisor)
    g.add_node("retriever", retriever_agent)
    g.add_node("web", web_agent)
    g.add_node("data", data_agent)
    g.add_node("code", code_agent)
    g.add_node("generate", generate)
    g.add_node("critic", critic)

    g.set_entry_point("supervisor")

    # supervisor qaysi agentni tanlasa, o'sha node'ga o'tadi
    g.add_conditional_edges(
        "supervisor",
        lambda state: state["plan"],
        {
            "retriever": "retriever",
            "web": "web",
            "data": "data",
            "code": "code",
            "finish": "generate",
        },
    )

    # har bir specialist agent ishini tugatgach, qaytadan supervisor'ga qaytadi
    for agent_name in ["retriever", "web", "data", "code"]:
        g.add_edge(agent_name, "supervisor")

    # generate -> critic
    g.add_edge("generate", "critic")

    # critic'dan keyin: finish (END) yoki qaytadan supervisor (revise)
    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {"finish": END, "revise": "supervisor"},
    )

    return g.compile()


if __name__ == "__main__":
    from src.state import new_state

    app = build_graph()
    final_state = app.invoke(new_state("How many employees work in Engineering?"))

    print(f"Bosqichlar: {final_state['steps']}")
    print(f"Revisiyalar: {final_state['revisions']}, tasdiqlandi: {final_state['approved']}")
    print(f"\nYakuniy javob: {final_state['answer']}")