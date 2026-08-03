"""
F6 -- Code agent: hisob-kitob savollariga LLM Python kod yozadi, biz uni xavfsiz
(alohida subprocessda, vaqt chegarasi bilan) ishga tushiramiz.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from src.llm import llm
from src.state import AgentState

RUNTIME_CAP_SECONDS = 10  # kod shu vaqtdan ortiq ishlasa, majburan to'xtatiladi


def _run_python_sandboxed(code: str) -> str:
    """Kodni vaqtinchalik faylga yozib, ALOHIDA subprocessda, vaqt chegarasi bilan ishga tushiradi."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        script_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=RUNTIME_CAP_SECONDS,
        )
        if proc.returncode != 0:
            return f"XATO:\n{proc.stderr.strip()}"
        return proc.stdout.strip()
    except subprocess.TimeoutExpired:
        return f"XATO: kod {RUNTIME_CAP_SECONDS} soniyadan ortiq ishladi, majburan to'xtatildi."
    finally:
        Path(script_path).unlink(missing_ok=True)


def code_agent(state: AgentState) -> dict:
    """Savolga javob beruvchi Python kodini LLM yozadi, biz uni sandboxda ishga tushiramiz."""
    prompt = (
        f"Savol: {state['question']}\n\n"
        "Shu savolga javob beradigan Python kod yoz. Yakuniy javobni print() bilan chiqar. "
        "Faqat kodning o'zini qaytar, izoh yoki ``` belgilarisiz."
    )
    code = llm.invoke(prompt).text.strip()
    code = code.removeprefix("```python").removeprefix("```").removesuffix("```").strip()

    result = _run_python_sandboxed(code)
    return {
        "code_result": result,
        "steps": state["steps"] + ["code"],
    }


if __name__ == "__main__":
    from src.state import new_state

    test_state = new_state("What is the sum of squares of numbers from 1 to 10?")
    result = code_agent(test_state)

    print(f"Bajarilgan qadamlar: {result['steps']}")
    print(f"Kod natijasi: {result['code_result']}")