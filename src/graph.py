"""
F7-F10 -- Supervisor, Critic, LangGraph grafi va uzoq muddatli xotira.
"""
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from src.agents.code_agent import code_agent
from src.agents.data_sql import data_agent
from src.llm import llm
from src.agents.retriever import retriever_agent
from src.memory import add_turn, recall
from src.state import AgentState
from src.agents.web import web_agent
from langfuse.langchain import CallbackHandler


class Route(BaseModel):
    next: str = Field(description="retriever|web|data|code|finish")


def supervisor(state: AgentState) -> dict:
    """Savolga qarab, keyingi qaysi agent ishga tushishi kerakligini hal qiladi."""
    if len(state["steps"]) >= 6:
        print("  [supervisor] xavfsizlik chegarasi (6 qadam) -- majburan finish")
        return {"plan": "finish", "steps": state["steps"] + ["supervisor->finish(forced)"]}

    past_context = recall(state["question"], k=2)
    memory_block = (
        "Oldingi tegishli suhbatlar:\n" + "\n---\n".join(past_context)
        if past_context else "Oldingi tegishli suhbat topilmadi."
    )

    router = llm.with_structured_output(Route)
    decision = router.invoke(
        f"{memory_block}\n\n"
        f"Savol: {state['question']}\n"
        f"Hozirgacha bajarilgan qadamlar: {state['steps']}\n\n"
        f"Hozirgacha yig'ilgan dalillar:\n"
        f"- Hujjatlar: {state['documents'] or 'hali yoq'}\n"
        f"- SQL natijasi: {state['sql_result'] or 'hali yoq'}\n"
        f"- Kod natijasi: {state['code_result'] or 'hali yoq'}\n\n"
        "MUHIM: agar yuqoridagi dalillar (yoki oldingi suhbatlar) savolga allaqachon aniq javob "
        "berish uchun yetarli bo'lsa, albatta 'finish' ni tanla -- bir xil agentni qayta-qayta "
        "chaqirma.\n\n"
        "Quyidagi agentlardan eng mosini tanla:\n"
        "- retriever: lokal hujjatlar bazasidan qidiradi. Bazada IQTISODIYOT DARSLIKLARI bor "
        "(talab-taklif qonuni, elastiklik, narx, bozor tuzilishi, iste'molchi tanlovi kabi "
        "klassik iqtisodiyot tushunchalari). Shu mavzudagi savollar uchun buni tanla.\n"
        "- web: internetdan joriy/yangi ma'lumot qidiradi (masalan bugungi narxlar, so'nggi "
        "yangiliklar, hujjatlarda yo'q joriy voqealar).\n"
        "- data: kompaniya SQL bazasidan (xodimlar, sotuvlar) sonli javob oladi.\n"
        "- code: matematik hisob-kitob yoki agregatsiya talab qiladigan savollar uchun.\n"
        "- finish: agar javob uchun yetarli ma'lumot allaqachon yig'ilgan bo'lsa (yoki oldingi "
        "suhbatda savolga allaqachon javob berilgan bo'lsa).\n\n"
        "Eng mos variantni tanla."
    )
    print(f"  [supervisor] {len(state['steps'])}-qadam -> {decision.next}")
    return {
        "plan": decision.next,
        "memory_context": past_context,
        "steps": state["steps"] + [f"supervisor->{decision.next}"],
    }


def generate(state: AgentState) -> dict:
    """Yig'ilgan barcha dalillar (hujjatlar, SQL, kod natijasi, xotira) asosida yakuniy javobni yozadi."""
    prompt = (
        f"Savol: {state['question']}\n\n"
        f"Hujjatlardan topilgan dalillar: {state['documents']}\n"
        f"SQL natijasi: {state['sql_result']}\n"
        f"Kod natijasi: {state['code_result']}\n"
        f"Oldingi tegishli suhbatlar (xotira): {state['memory_context']}\n\n"
        "Yuqoridagi barcha dalillarga (jumladan oldingi suhbatlarga) asoslanib, savolga aniq va "
        "qisqa javob yoz. Faqat yuqorida berilgan dalillardan foydalan, o'zingdan narsa qo'shma. "
        "Agar hech qaysi manbada yetarli ma'lumot bo'lmasa, shuni aytib o't."
    )
    answer = llm.invoke(prompt).text.strip()
    return {
        "answer": answer,
        "steps": state["steps"] + ["generate"],
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
        f"Dalillar (xotira): {state['memory_context']}\n"
        f"Yozilgan javob: {state['answer']}\n\n"
        "Bu javob to'g'rimi VA to'liq ravishda yuqoridagi dalillarga asoslanganmi? "
        "Agar dalillarda yo'q narsa aytilgan bo'lsa yoki noto'g'ri bo'lsa, ok=False de."
    )
    print(f"  [critic] ok={verdict.ok}, sabab: {verdict.reason}")
    return {
        "revisions": state["revisions"] + (0 if verdict.ok else 1),
    }


MAX_REVISIONS = 2  # necha marta qayta yozishga urinishga ruxsat (grafning cheksiz aylanishini oldini oladi)


def route_after_critic(state: AgentState) -> str:
    """Critic natijasidan keyin: javob tasdiqlandimi (finish) yoki qayta ishlash kerakmi (revise)?"""
    if state["revisions"] == 0:
        return "finish"
    if state["revisions"] >= MAX_REVISIONS:
        print(f"  [route_after_critic] revisions limiti ({MAX_REVISIONS}) tugadi -- majburan finish")
        return "finish"
    return "revise"


def save_memory(state: AgentState) -> dict:
    """Yakunlangan savol-javobni uzoq muddatli xotiraga yozadi."""
    add_turn(state["question"], state["answer"])
    return {"steps": state["steps"] + ["save_memory"]}


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
    g.add_node("save_memory", save_memory)

    g.set_entry_point("supervisor")

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

    for agent_name in ["retriever", "web", "data", "code"]:
        g.add_edge(agent_name, "supervisor")

    g.add_edge("generate", "critic")

    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {"finish": "save_memory", "revise": "supervisor"},
    )
    g.add_edge("save_memory", END)

    return g.compile()


if __name__ == "__main__":
    from src.state import new_state

    app = build_graph()
    langfuse_handler = CallbackHandler()

    try:
        print("--- 1-savol ---")
        state1 = app.invoke(
            new_state("How many employees work in Engineering?"),
            config={"recursion_limit": 15, "callbacks": [langfuse_handler]},
        )
        print(f"Javob: {state1['answer']}")
        print(f"steps: {state1['steps']}\n")

        print("--- 2-savol (davomli, xotiraga tayanishi kerak) ---")
        state2 = app.invoke(
            new_state("And how many work in Marketing?"),
            config={"recursion_limit": 15, "callbacks": [langfuse_handler]},
        )
        print(f"Javob: {state2['answer']}")
        print(f"steps: {state2['steps']}")
    finally:
        langfuse_handler.client.flush()
        print("\n[Langfuse] barcha trace'lar yuborildi (flush qilindi).")