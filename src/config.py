"""
F1 -- Configuration: .env dan API kalitlarni o'qiydi va tekshiradi.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 1. __file__ atrofida ikkita pastki chiziq (_) bo'lishi shart
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# 2. BOM muammosini oldini olish uchun faylni qo'lda to'g'ri o'qish
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# Zaxira sifatida load_dotenv ham ishga tushadi
load_dotenv(dotenv_path=ENV_PATH, override=True)

class Settings(BaseModel):
    google_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    tavily_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY") or None)
    langfuse_public_key: Optional[str] = Field(default_factory=lambda: os.getenv("LANGFUSE_PUBLIC_KEY") or None)
    langfuse_secret_key: Optional[str] = Field(default_factory=lambda: os.getenv("LANGFUSE_SECRET_KEY") or None)
    langfuse_host: str = Field(default_factory=lambda: os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"))

    def validate_required(self) -> None:
        """Shart bo'lgan kalit yo'q bo'lsa, aniq xato bilan to'xtatadi."""
        if not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY topilmadi. .env faylida GOOGLE_API_KEY=... qatorini to'ldiring."
            )

settings = Settings()

def check_status() -> None:
    """Har bir kalit yuklanganini (qiymatini ko'rsatmasdan) tekshiradi."""
    checks = {
        "GOOGLE_API_KEY (shart)": bool(settings.google_api_key),
        "TAVILY_API_KEY (ixtiyoriy)": bool(settings.tavily_api_key),
        "LANGFUSE_PUBLIC_KEY (ixtiyoriy)": bool(settings.langfuse_public_key),
        "LANGFUSE_SECRET_KEY (ixtiyoriy)": bool(settings.langfuse_secret_key),
    }
    print("--- .env holati ---")
    for name, ok in checks.items():
        print(f"{'✅' if ok else '❌'} {name}")

if __name__ == "__main__":
    check_status()
    settings.validate_required()
    print("\n✅ Config muvaffaqiyatli yuklandi.")