"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import CrewGraph from "./components/CrewGraph";
import {
  AGENTS,
  EXAMPLES,
  activeAgent,
  agentOfStep,
  cleanAnswer,
  parseSource,
  stepLabel,
  visitedAgents,
} from "./lib/agents";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const REPO_URL = "https://github.com/shodiyorkarimov/multi-agent-ai-analyst";
const WAKING_AFTER_MS = 6000;

function greeting(hour) {
  if (hour < 5) return "Xayrli tun";
  if (hour < 12) return "Xayrli tong";
  if (hour < 18) return "Xayrli kun";
  return "Xayrli kech";
}

// Javobni so'zma-so'z ochadi (foydalanuvchi savoli bergan lahzaga javob sifatida)
function Typewriter({ text, onTick }) {
  const words = useMemo(() => text.split(/(\s+)/), [text]);
  const [count, setCount] = useState(0);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setCount(words.length);
      return;
    }
    setCount(0);
    const id = setInterval(() => {
      setCount((c) => {
        if (c >= words.length) {
          clearInterval(id);
          return c;
        }
        return c + 1;
      });
    }, 22);
    return () => clearInterval(id);
  }, [words]);

  useEffect(() => {
    onTick?.();
  }, [count, onTick]);

  return <>{words.slice(0, count).join("")}</>;
}

function Check() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="9" fill="currentColor" opacity="0.2" />
      <path d="M6 10.5l2.7 2.7L14 7.8" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Trace({ msg }) {
  const items = msg.steps.map((step, i) => (
    <li key={i} style={{ "--nc": `var(--c-${agentOfStep(step)})` }}>
      <i />
      {stepLabel(step)}
    </li>
  ));

  if (!msg.done) return <ol className="trace">{items}</ol>;

  const seconds = msg.finishedAt && msg.startedAt ? ((msg.finishedAt - msg.startedAt) / 1000).toFixed(1) : null;
  return (
    <details className="trace">
      <summary>
        Agentlar qanday ishladi ({msg.steps.length} qadam{seconds ? `, ${seconds} soniya` : ""})
      </summary>
      <ol>{items}</ol>
    </details>
  );
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [waking, setWaking] = useState(false);
  const [server, setServer] = useState("waking");
  const [hello, setHello] = useState("Salom");
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const last = messages[messages.length - 1];
  const steps = last?.steps ?? [];

  // Server uyxlab yotgan bo'lishi mumkin (bepul tarif) -- sahifa ochilishi bilanoq uyg'otamiz.
  useEffect(() => {
    setHello(greeting(new Date().getHours()));
    let cancelled = false;
    (async () => {
      for (let attempt = 0; attempt < 14 && !cancelled; attempt++) {
        try {
          const res = await fetch(`${API}/health`);
          if (res.ok) {
            if (!cancelled) setServer("ready");
            return;
          }
        } catch {
          /* server hali uyg'onmagan */
        }
        await new Promise((r) => setTimeout(r, 5000));
      }
      if (!cancelled) setServer("down");
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // So'rov yuborilgach 6 soniya hech qanday qadam kelmasa -- server uyg'onayotgan bo'lishi mumkin.
  useEffect(() => {
    setWaking(false);
    if (!loading || steps.length > 0) return;
    const id = setTimeout(() => setWaking(true), WAKING_AFTER_MS);
    return () => clearTimeout(id);
  }, [loading, steps.length]);

  const scrollDown = useMemo(
    () => () => {
      const el = scrollRef.current;
      if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    },
    []
  );

  useEffect(scrollDown, [messages.length, steps.length, scrollDown]);

  function patchLast(patch) {
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const next = prev.slice();
      next[next.length - 1] = { ...next[next.length - 1], ...patch };
      return next;
    });
  }

  async function ask(text) {
    const q = text.trim();
    if (!q || loading) return;

    setQuestion("");
    setLoading(true);
    setMessages((prev) => [
      ...prev,
      { question: q, steps: [], answer: null, documents: [], done: false, error: false, startedAt: Date.now() },
    ]);

    try {
      const response = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!response.ok) throw new Error(`Server ${response.status} xato qaytardi`);

      setServer("ready");
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
          if (event.type === "step") {
            patchLast({ steps: event.steps });
          } else if (event.type === "answer") {
            patchLast({ answer: cleanAnswer(event.answer), documents: event.documents || [] });
          } else if (event.type === "done") {
            patchLast({ done: true, finishedAt: Date.now() });
          }
        }
      }
      patchLast({ done: true, finishedAt: Date.now() });
    } catch (err) {
      patchLast({
        answer: `Javob olib bo'lmadi: ${err.message}. Server uyg'onayotgan bo'lishi mumkin, bir daqiqadan keyin qayta urinib ko'ring.`,
        error: true,
        done: true,
        finishedAt: Date.now(),
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    ask(question);
  }

  // Grafning holati
  const finished = Boolean(last?.done && last?.answer && !last?.error);
  const active = loading ? activeAgent(steps) : null;
  const visited = useMemo(() => visitedAgents(steps), [steps]);

  let statusText = "Agentlar tayyor. Savol bering.";
  let statusColor = "var(--c-supervisor)";
  if (loading) {
    if (steps.length === 0) {
      statusText = waking ? "Server uyg'onmoqda, bu 30-60 soniya olishi mumkin..." : "Supervisor savolni o'qimoqda...";
    } else {
      const next = active ? AGENTS[active] : null;
      statusText = next ? `${next.label}: ${next.hint}` : "Tayyor!";
      statusColor = `var(--c-${active || "supervisor"})`;
    }
  } else if (finished) {
    statusText = "Tayyor! Yana savol berishingiz mumkin.";
    statusColor = "var(--c-critic)";
  } else if (last?.error) {
    statusText = "Xatolik chiqdi. Qayta urinib ko'ring.";
    statusColor = "var(--c-web)";
  }

  const serverText = {
    ready: "Server tayyor",
    waking: "Server uyg'onmoqda...",
    down: "Server javob bermayapti",
  }[server];

  return (
    <div className="app">
      <aside className="crew">
        <div>
          <h1 className="brand">Multi-Agent AI Analyst</h1>
          <p className="tagline">Yetti agent bitta savolga birga javob qidiradi: o&apos;qiydi, hisoblaydi, tekshiradi.</p>
        </div>

        <div className="stage">
          <CrewGraph active={active} visited={visited} finished={finished && !loading} />
        </div>

        <p className={`status ${loading ? "is-live" : ""}`} aria-live="polite" style={{ "--nc": statusColor }}>
          <span className="status-dot" />
          <span>{statusText}</span>
        </p>

        <div className="crew-extra">
          <span className="server" data-state={server}>
            <i />
            {serverText}
          </span>
          <p>LangGraph · Gemini · Qdrant · FastAPI · Next.js</p>
          <a href={REPO_URL} target="_blank" rel="noreferrer">
            Kodni GitHub&apos;da ko&apos;rish
          </a>
        </div>
      </aside>

      <section className="talk">
        <div className="talk-scroll" ref={scrollRef}>
          <div className="talk-inner">
            {messages.length === 0 && (
              <div className="hello">
                <h2>{hello}! Nimani bilmoqchisiz?</h2>
                <p>Tanlangan misol har agent o&apos;z rangida ishga tushadi. Yoki o&apos;z savolingizni yozing.</p>
                <div className="chips">
                  {EXAMPLES.map((ex) => (
                    <button
                      key={ex.text}
                      className="chip"
                      style={{ "--nc": `var(--c-${ex.agent})` }}
                      onClick={() => ask(ex.text)}
                      disabled={loading}
                    >
                      <span className="chip-tag">{AGENTS[ex.agent].label}</span>
                      {ex.text}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <article className="turn" key={i}>
                <div className="q">{msg.question}</div>

                {msg.steps.length > 0 && <Trace msg={msg} />}

                {!msg.answer && !msg.done && i === messages.length - 1 && waking && msg.steps.length === 0 && (
                  <p className="waking-note">
                    Server bepul tarifda uxlab qolgan edi, hozir uyg&apos;onmoqda. Birinchi javob 30-60 soniya olishi
                    mumkin, keyingilari tez bo&apos;ladi.
                  </p>
                )}

                {msg.answer && (
                  <p className={`answer ${msg.error ? "is-error" : ""}`}>
                    {msg.error ? (
                      msg.answer
                    ) : i === messages.length - 1 ? (
                      <Typewriter text={msg.answer} onTick={scrollDown} />
                    ) : (
                      msg.answer
                    )}
                  </p>
                )}

                {msg.done && msg.answer && !msg.error && msg.steps.some((s) => s.startsWith("critic (ok=True)")) && (
                  <span className="badge">
                    <Check />
                    Critic dalillar bilan solishtirib tasdiqladi
                  </span>
                )}

                {msg.documents.length > 0 && (
                  <details className="sources">
                    <summary>Manbalar ({msg.documents.length})</summary>
                    <ul>
                      {msg.documents.map((doc, k) => {
                        const { source, text } = parseSource(doc);
                        return (
                          <li key={k}>
                            {source && <b>{source}</b>}
                            <span>{text}</span>
                          </li>
                        );
                      })}
                    </ul>
                  </details>
                )}
              </article>
            ))}
          </div>
        </div>

        <div className="composer">
          <form onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Savolingizni yozing..."
              aria-label="Savol"
              disabled={loading}
              autoComplete="off"
            />
            <button type="submit" className="send" disabled={loading || !question.trim()}>
              {loading ? "Ishlayapti" : "Yuborish"}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M3 11.5l17-8-7 17-2.6-7L3 11.5z" fill="currentColor" />
              </svg>
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
