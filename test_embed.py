import json
import urllib.error
import urllib.request
from pathlib import Path

key = None
for line in Path(".env").read_text(encoding="utf-8-sig").splitlines():
    if line.startswith("GOOGLE_API_KEY="):
        key = line.split("=", 1)[1].strip()

if not key:
    print("❌ .env ichida GOOGLE_API_KEY topilmadi")
    raise SystemExit

BASE = "https://generativelanguage.googleapis.com/v1beta"
HEADERS = {"Content-Type": "application/json", "x-goog-api-key": key}
MODEL = "gemini-embedding-001"

body = json.dumps({"content": {"parts": [{"text": "law of supply and demand"}]}}).encode()
req = urllib.request.Request(f"{BASE}/models/{MODEL}:embedContent", data=body, headers=HEADERS)

try:
    with urllib.request.urlopen(req, timeout=60) as r:
        values = json.load(r)["embedding"]["values"]
        print(f"✅ Ishladi! Model: {MODEL}, vektor o'lchami: {len(values)}")
        print("   (Qdrant'dagi eski vektorlar 3072 o'lchamli edi)")
except urllib.error.HTTPError as e:
    print("❌ Xato kodi:", e.code)
    print(e.read().decode()[:500])
    print("\nMavjud embedding modellari:")
    try:
        req2 = urllib.request.Request(f"{BASE}/models?pageSize=200", headers=HEADERS)
        with urllib.request.urlopen(req2, timeout=60) as r2:
            for m in json.load(r2).get("models", []):
                if "embedContent" in m.get("supportedGenerationMethods", []):
                    print(" -", m["name"])
    except Exception as e2:
        print("   ro'yxatni olib bo'lmadi:", e2)
except Exception as e:
    print("❌", type(e).__name__, e)
