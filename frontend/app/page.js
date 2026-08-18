"use client";

import { useState, useRef, useEffect } from "react";

const AGENT_LABELS = {
  supervisor: "Supervisor yo'nalish tanlamoqda...",
  "supervisor->retriever": "Supervisor: hujjatlardan qidirish kerak",
  "supervisor->web": "Supervisor: internetdan qidirish kerak",
  "supervisor->data": "Supervisor: SQL bazasidan so'rov kerak",
  "supervisor->code": "Supervisor: kod bilan hisoblash kerak",
  "supervisor->finish": "Supervisor: yetarli ma'lumot bor, javob yozamiz",
  retriever: "Hujjatlar bazasidan qidirildi",
  web: "Internetdan qidirildi",
  "data(sql)": "SQL bazasidan ma'lumot olindi",
  code: "Kod ishga tushirildi",
  generate: "Javob yozilmoqda...",
  save_memory: "Xotiraga saqlanmoqda...",
};

function stepLabel(step) {
  if (step.startsWith("critic (ok=True)")) return "Critic: javob tasdiqlandi ✅";
  if (step.startsWith("critic (ok=False)")) return "Critic: javob rad etildi, qayta yozilmoqda ♻️";
  return AGENT_LABELS[step] || step;
}

// "[manba: Principles of Economics.pdf] matn..." -> { source, text }
function parseSource(doc) {
  const match = doc.match(/^\[manba:\s*(.+?)\]\s*([\s\S]*)$/);
  if (match) {
    return { source: match[1], text: match[2] };
  }
  return { source: null, text: doc };
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userQuestion = question;
    setQuestion("");
    setLoading(true);

    const newMessage = {
      question: userQuestion,
      steps: [],
      answer: null,
      documents: [],
    };
    setMessages((prev) => [...prev, newMessage]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userQuestion }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();

        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          const event = JSON.parse(part.slice(6));

          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];

            if (event.type === "step") {
              last.steps = event.steps;
            } else if (event.type === "answer") {
              last.answer = event.answer;
              last.documents = event.documents || [];
            }
            return updated;
          });
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].answer = `Xato: ${err.message}`;
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-800">
          Multi-Agent AI Analyst
        </h1>
      </header>

      <main className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {messages.length === 0 && (
          <p className="text-gray-400 text-center mt-20">
            Savol bering, masalan: &quot;How many employees work in Engineering?&quot;
          </p>
        )}

        {messages.map((msg, i) => (
          <div key={i} className="max-w-2xl mx-auto space-y-2">
            <div className="bg-blue-600 text-white rounded-2xl px-4 py-2 w-fit ml-auto">
              {msg.question}
            </div>

            {msg.steps.length > 0 && (
              <div className="space-y-1">
                {msg.steps.map((step, j) => (
                  <div
                    key={j}
                    className="text-sm text-gray-500 flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                    {stepLabel(step)}
                  </div>
                ))}
              </div>
            )}

            {msg.answer && (
              <div className="bg-white border rounded-2xl px-4 py-3 w-fit max-w-full shadow-sm">
                {msg.answer}
              </div>
            )}

            {msg.documents && msg.documents.length > 0 && (
              <details className="max-w-full">
                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                  Manbalar ({msg.documents.length})
                </summary>
                <div className="mt-2 space-y-2">
                  {msg.documents.map((doc, k) => {
                    const { source, text } = parseSource(doc);
                    return (
                      <div
                        key={k}
                        className="bg-gray-100 border rounded-lg px-3 py-2 text-xs text-gray-600"
                      >
                        {source && (
                          <div className="font-semibold text-gray-700 mb-1">
                            📄 {source}
                          </div>
                        )}
                        <div className="line-clamp-3">{text}</div>
                      </div>
                    );
                  })}
                </div>
              </details>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </main>

      <form
        onSubmit={handleSubmit}
        className="bg-white border-t px-6 py-4 flex gap-3 max-w-2xl mx-auto w-full"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Savolingizni yozing..."
          disabled={loading}
          className="flex-1 border rounded-full px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white rounded-full px-5 py-2 disabled:opacity-50"
        >
          {loading ? "..." : "Yuborish"}
        </button>
      </form>
    </div>
  );
}