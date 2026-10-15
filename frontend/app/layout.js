import { Bricolage_Grotesque, Figtree } from "next/font/google";
import "./globals.css";

const display = Bricolage_Grotesque({
  variable: "--font-display",
  subsets: ["latin", "latin-ext"],
});

const body = Figtree({
  variable: "--font-body",
  subsets: ["latin", "latin-ext"],
});

export const metadata = {
  title: "Multi-Agent AI Analyst",
  description:
    "Yetti AI agent bitta savolga birga javob qidiradi: hujjatlar, SQL, web, kod, tekshiruvchi va xotira. LangGraph, Gemini va Qdrant asosida.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="uz" className={`${display.variable} ${body.variable}`}>
      <body>{children}</body>
    </html>
  );
}
