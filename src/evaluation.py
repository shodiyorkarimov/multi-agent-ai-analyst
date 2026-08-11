"""
F11 -- Evaluation harness: RAGAS metrikalari + LLM-judge orqali tizimni baholash.
"""

from ragas.run_config import RunConfig
import json
import time
from pathlib import Path

from ragas import evaluate as ragas_evaluate
from ragas import EvaluationDataset
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import context_precision, faithfulness
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import BaseModel, Field

from src.graph import build_graph
from src.llm import llm
from src.state import new_state

QUESTIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "questions.json"


class JudgeScore(BaseModel):
    score: int = Field(description="1 dan 5 gacha ball: 1=butunlay noto'g'ri, 5=mukammal to'g'ri")
    reason: str = Field(description="Qisqacha sabab")


def llm_judge(question: str, answer: str, ground_truth: str) -> JudgeScore:
    """LLM'dan javobni 1-5 ball bilan baholashni so'raydi (ground_truth bilan solishtirib)."""
    judge = llm.with_structured_output(JudgeScore)
    return judge.invoke(
        f"Savol: {question}\n"
        f"To'g'ri (namunaviy) javob: {ground_truth}\n"
        f"Tizim bergan javob: {answer}\n\n"
        "Tizim javobini 1 dan 5 gacha baholang: "
        "5 = to'g'ri javob va namunaviy javob bilan mos, "
        "3 = qisman to'g'ri yoki to'liq emas, "
        "1 = noto'g'ri yoki mutlaqo aloqasiz."
    )


def run_pipeline_for_question(app, question: str) -> dict:
    """Bitta savolni to'liq grafdan o'tkazadi va RAGAS uchun kerakli maydonlarni yig'adi."""
    state = app.invoke(new_state(question), config={"recursion_limit": 15})

    contexts = list(state["documents"])
    if state["sql_result"]:
        contexts.append(str(state["sql_result"]))
    if state["code_result"]:
        contexts.append(str(state["code_result"]))
    if not contexts:
        contexts = ["(dalil topilmadi)"]

    return {"answer": state["answer"], "contexts": contexts}


def main() -> None:
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        test_set = json.load(f)

    app = build_graph()

    rows = []
    judge_scores = []

    print(f"=== {len(test_set)} ta savol ustida baholash boshlandi ===\n")

    for i, item in enumerate(test_set, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]

        print(f"[{i}/{len(test_set)}] {question}")

        result = run_pipeline_for_question(app, question)
        time.sleep(4)  # kvotani tejash uchun pauza

        judge = llm_judge(question, result["answer"], ground_truth)
        time.sleep(4)

        print(f"  Javob: {result['answer']}")
        print(f"  LLM-judge: {judge.score}/5 -- {judge.reason}\n")

        rows.append({
            "user_input": question,
            "response": result["answer"],
            "retrieved_contexts": result["contexts"],
            "reference": ground_truth,
        })
        judge_scores.append(judge.score)

    print("=== RAGAS metrikalari hisoblanmoqda (bir necha daqiqa davom etishi mumkin) ===\n")

    evaluator_llm = LangchainLLMWrapper(llm)
    evaluator_embeddings = LangchainEmbeddingsWrapper(
        GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")
    )

    dataset = EvaluationDataset.from_list(rows)
    ragas_result = ragas_evaluate(
        dataset=dataset,
        metrics=[faithfulness, context_precision],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        run_config=RunConfig(timeout=120, max_workers=2, max_retries=3),
    )

    df = ragas_result.to_pandas()
    df["llm_judge_1_5"] = judge_scores

    print("\n=== YAKUNIY NATIJALAR JADVALI ===\n")
    print(df[["user_input", "faithfulness", "context_precision", "llm_judge_1_5"]].to_string(index=False))

    print("\n=== O'RTACHA KO'RSATKICHLAR ===")
    print(f"Faithfulness (o'rtacha):      {df['faithfulness'].mean():.2f}")
    print(f"Context precision (o'rtacha): {df['context_precision'].mean():.2f}")
    print(f"LLM-judge (o'rtacha, 1-5):    {sum(judge_scores) / len(judge_scores):.2f}")


if __name__ == "__main__":
    main()