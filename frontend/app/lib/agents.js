// Agentlar haqidagi yagona manba: nomi, rangi, joylashuvi va step -> agent xaritasi.

export const AGENTS = {
  supervisor: { label: "Supervisor", hint: "Savolni tahlil qilib, kerakli agentni tanlaydi", x: 200, y: 175, r: 36 },
  retriever: { label: "Hujjatlar", hint: "Iqtisodiyot darsligidan qidiradi (RAG)", x: 200, y: 50, r: 25 },
  web: { label: "Web", hint: "Internetdan yangi ma'lumot qidiradi", x: 308, y: 112, r: 25 },
  data: { label: "SQL", hint: "Kompaniya bazasidan aniq son oladi", x: 308, y: 238, r: 25 },
  code: { label: "Kod", hint: "Python yozib, hisob-kitob qiladi", x: 200, y: 300, r: 25 },
  critic: { label: "Critic", hint: "Javobni dalillar bilan solishtirib tekshiradi", x: 92, y: 238, r: 25 },
  memory: { label: "Xotira", hint: "Oldingi suhbatlarni eslab qoladi", x: 92, y: 112, r: 25 },
};

export const WORKERS = ["retriever", "web", "data", "code"];

const STEP_LABELS = {
  "supervisor->retriever": "Supervisor: hujjatlardan qidirish kerak",
  "supervisor->web": "Supervisor: internetdan qidirish kerak",
  "supervisor->data": "Supervisor: SQL bazasidan so'rov kerak",
  "supervisor->code": "Supervisor: kod bilan hisoblash kerak",
  "supervisor->finish": "Supervisor: ma'lumot yetarli, javob yozamiz",
  "supervisor->finish(forced)": "Supervisor: qadamlar chegarasiga yetdik, javob yozamiz",
  retriever: "Hujjatlar bazasidan qidirildi",
  web: "Internetdan qidirildi",
  "web (skipped)": "Web qidiruv o'tkazib yuborildi (kalit yo'q)",
  "data(sql)": "SQL bazasidan ma'lumot olindi",
  code: "Kod ishga tushirildi",
  generate: "Javob yozildi",
  save_memory: "Xotiraga saqlandi",
};

export function stepLabel(step) {
  if (step.startsWith("critic (ok=True)")) return "Critic: javob tasdiqlandi";
  if (step.startsWith("critic (ok=False)")) return "Critic: javob rad etildi, qayta yoziladi";
  return STEP_LABELS[step] || step;
}

// Step qaysi agentga tegishli (trace'dagi nuqta rangi uchun)
export function agentOfStep(step) {
  if (step.startsWith("supervisor")) return "supervisor";
  if (step.startsWith("critic")) return "critic";
  if (step === "save_memory") return "memory";
  if (step === "generate") return "supervisor";
  if (step === "data(sql)") return "data";
  if (step.startsWith("web")) return "web";
  if (step === "retriever" || step === "code") return step;
  return "supervisor";
}

// Hozir qaysi agent "ishlayapti" -- oxirgi qadamdan keyingi navbat.
export function activeAgent(steps) {
  const last = steps[steps.length - 1];
  if (!last) return "supervisor";
  if (last.startsWith("supervisor->")) {
    const target = last.slice("supervisor->".length);
    return WORKERS.includes(target) ? target : "supervisor";
  }
  if (last === "generate") return "critic";
  if (last.startsWith("critic (ok=True)")) return "memory";
  if (last.startsWith("critic (ok=False)")) return "supervisor";
  if (last === "save_memory") return null;
  return "supervisor";
}

// Ishtirok etgan agentlar (graf chiziqlarini bo'yash uchun)
export function visitedAgents(steps) {
  const set = new Set();
  for (const s of steps) {
    const a = agentOfStep(s);
    if (a !== "supervisor") set.add(a);
  }
  return set;
}

// "[manba: Principles of Economics.pdf] matn..." -> { source, text }
export function parseSource(doc) {
  const match = doc.match(/^\[manba:\s*(.+?)\]\s*([\s\S]*)$/);
  return match ? { source: match[1], text: match[2] } : { source: null, text: doc };
}

// Xotiradan nusxalangan "Savol: ...\nJavob: ..." prefiksini olib tashlaydi.
export function cleanAnswer(answer) {
  return (answer || "").replace(/^\s*Savol:[\s\S]*?\n\s*Javob:\s*/i, "").trim();
}

export const EXAMPLES = [
  { text: "How many employees work in Engineering?", agent: "data" },
  { text: "What is the law of demand?", agent: "retriever" },
  { text: "What is the sum of squares of numbers from 1 to 10?", agent: "code" },
];
