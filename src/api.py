"""
F13 -- FastAPI backend: LangGraph oqimini frontendga real vaqtda (SSE) uzatadi.
F12 -- Har bir so'rov Langfuse orqali kuzatiladi (tracing).
"""
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langfuse.langchain import CallbackHandler

from src.graph import build_graph
from src.state import new_state

app = FastAPI(title="Multi-Agent AI Analyst API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://multi-agent-ai-analyst-mauve.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


class AskRequest(BaseModel):
    question: str


def sse_format(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@app.post("/ask")
def ask(request: AskRequest):
    def event_stream():
        state = new_state(request.question)
        seen_steps = 0
        final_snapshot = state

        # F12: har bir so'rov uchun alohida Langfuse callback handler --
        # shunda har bir savol o'zining trace'iga ega bo'ladi (aralashib ketmaydi).
        langfuse_handler = CallbackHandler()

        try:
            for snapshot in graph.stream(
                state,
                config={
                    "recursion_limit": 15,
                    "callbacks": [langfuse_handler],
                },
                stream_mode="values",
            ):
                final_snapshot = snapshot
                steps = snapshot.get("steps", [])
                if len(steps) > seen_steps:
                    seen_steps = len(steps)
                    yield sse_format(
                        {
                            "type": "step",
                            "latest_step": steps[-1],
                            "steps": steps,
                        }
                    )

            yield sse_format(
                {
                    "type": "answer",
                    "answer": final_snapshot.get("answer", ""),
                    "documents": final_snapshot.get("documents", []),
                }
            )
            yield sse_format({"type": "done"})
        finally:
            # Trace darhol Langfuse serveriga yuborilishini ta'minlaydi
            # (aks holda process tugaguncha navbatda kutib qolishi mumkin).
            langfuse_handler.client.flush()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}