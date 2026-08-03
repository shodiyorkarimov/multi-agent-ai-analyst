"""
F5 -- Data agent (Text-to-SQL): savolni SQL so'roviga aylantirib, bazadan aniq javob oladi.
"""
from pathlib import Path

from langchain_community.utilities import SQLDatabase

from src.llm import llm
from src.state import AgentState

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "company.db"
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")


def data_agent(state: AgentState) -> dict:
    """Savolni SQLga aylantirib, faqat SELECT so'rovlarga ruxsat berib, bazadan javob oladi."""
    prompt = (
        f"Schema:\n{db.get_table_info()}\n\n"
        f"Savol: {state['question']}\n\n"
        "Shu savolga javob beradigan bitta SQLite SELECT so'rovini yoz. "
        "Faqat SQL kodni qaytar, boshqa hech narsa yozma, ``` belgilarisiz."
    )
    sql = llm.invoke(prompt).text.strip()

    # xavfsizlik: faqat SELECT so'roviga ruxsat (DROP/DELETE/UPDATE taqiqlanadi)
    if not sql.lower().startswith("select"):
        raise ValueError(f"Xavfsizlik: faqat SELECT so'roviga ruxsat bor, olindi: {sql!r}")

    result = db.run(sql)
    return {
        "sql_result": f"{sql}\n-> {result}",
        "steps": state["steps"] + ["data(sql)"],
    }


if __name__ == "__main__":
    from src.state import new_state

    test_state = new_state("How many employees work in the Engineering department?")
    result = data_agent(test_state)

    print(f"Bajarilgan qadamlar: {result['steps']}")
    print(f"SQL natijasi:\n{result['sql_result']}")