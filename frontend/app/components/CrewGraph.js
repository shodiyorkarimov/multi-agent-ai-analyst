"use client";

import { AGENTS } from "../lib/agents";

const CENTER = AGENTS.supervisor;

// Ko'z qorachasi qaysi tomonga qaraydi (birlik vektor * radius)
function look(from, to, reach = 2.6) {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const len = Math.hypot(dx, dy) || 1;
  return { x: (dx / len) * reach, y: (dy / len) * reach };
}

function Face({ mood, pupil }) {
  // Birlik koordinatalar: shar radiusi 30
  return (
    <g className="face">
      <g className="eyes">
        {[-10, 10].map((ex) => (
          <g key={ex} transform={`translate(${ex} -5)`}>
            <circle r="6.6" fill="#fff" />
            <circle className="pupil" r="3.5" cx={pupil.x} cy={pupil.y} fill="#1E1B3A" />
          </g>
        ))}
      </g>
      {mood === "active" ? (
        <ellipse cx="0" cy="12" rx="4.2" ry="5" fill="#1E1B3A" />
      ) : mood === "happy" ? (
        <path d="M -9 9 Q 0 20 9 9" fill="none" stroke="#1E1B3A" strokeWidth="2.6" strokeLinecap="round" />
      ) : (
        <path d="M -6 11 Q 0 14 6 11" fill="none" stroke="#1E1B3A" strokeWidth="2.4" strokeLinecap="round" />
      )}
    </g>
  );
}

function Node({ id, active, visited, finished, index, lookTarget }) {
  const a = AGENTS[id];
  const mood = active ? "active" : finished || visited ? "happy" : "idle";
  const scale = a.r / 30;
  const from = { x: a.x, y: a.y };
  const pupil = lookTarget ? look(from, lookTarget) : { x: 0, y: 1.6 };

  return (
    <g
      className={`node ${active ? "is-active" : ""} ${finished ? "is-finished" : ""}`}
      transform={`translate(${a.x} ${a.y})`}
      style={{ "--nc": `var(--c-${id})`, "--i": index }}
    >
      <title>{`${a.label}: ${a.hint}`}</title>
      <circle className="ring" r={a.r + 4} />
      <g className="bob">
        <g className="pop" style={{ animationDelay: `${index * 90}ms` }}>
          <g transform={`scale(${scale})`}>
            <circle className="blob" r="30" />
            <Face mood={mood} pupil={pupil} />
          </g>
        </g>
      </g>
      <text className="node-label" y={a.r + 18} textAnchor="middle">
        {a.label}
      </text>
    </g>
  );
}

/**
 * Agentlar jamoasi: markazda Supervisor, atrofida 6 agent.
 * active   -- hozir ishlayotgan agent id (yoki null)
 * visited  -- shu savolda ishtirok etganlar (Set)
 * finished -- javob tayyor bo'lganda true (hammasi jilmayadi)
 */
export default function CrewGraph({ active, visited, finished }) {
  const outer = Object.keys(AGENTS).filter((id) => id !== "supervisor");
  const supervisorLook =
    active && active !== "supervisor" ? AGENTS[active] : { x: CENTER.x, y: CENTER.y + 40 };

  return (
    <svg
      className="crew-graph"
      viewBox="0 0 400 350"
      role="img"
      aria-label="Agentlar jamoasi: Supervisor markazda, Hujjatlar, Web, SQL, Kod, Critic va Xotira agentlari atrofida"
    >
      <g className="edges">
        {outer.map((id, i) => {
          const a = AGENTS[id];
          const isActive = active === id;
          return (
            <line
              key={id}
              className={`edge ${isActive ? "is-active" : ""} ${visited.has(id) ? "is-visited" : ""}`}
              x1={CENTER.x}
              y1={CENTER.y}
              x2={a.x}
              y2={a.y}
              style={{ "--nc": `var(--c-${id})`, "--i": i }}
            />
          );
        })}
      </g>

      {outer.map((id, i) => (
        <Node
          key={id}
          id={id}
          index={i + 1}
          active={active === id}
          visited={visited.has(id)}
          finished={finished}
          lookTarget={CENTER}
        />
      ))}

      <Node
        id="supervisor"
        index={0}
        active={active === "supervisor"}
        visited={false}
        finished={finished}
        lookTarget={supervisorLook}
      />
    </svg>
  );
}
