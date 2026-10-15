import json
import urllib.error
import urllib.request
from pathlib import Path

key = None
for line in Path(".env").read_text(encoding="utf-8-sig").splitlines():
    if line.startswith("GOOGLE_API_KEY="):
        key = line.split("=", 1)[1].strip()

if not key:
    print("❌ .env ichida GOOGLE_API_KEY topilmadi (fayl loyiha papkasida ekanini tekshiring)")
    raise SystemExit

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
body = json.dumps({"contents": [{"parts": [{"text": "Bitta so'z bilan javob ber: salom"}]}]}).encode()
req = urllib.request.Request(
    url,
    data=body,
    headers={"Content-Type": "application/json", "x-goog-api-key": key},
)

try:
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
        print("✅ Ishladi! Gemini javobi:", data["candidates"][0]["content"]["parts"][0]["text"])
except urllib.error.HTTPError as e:
    print("❌ Xato kodi:", e.code)
    print(e.read().decode()[:600])
except Exception as e:
    print("❌", type(e).__name__, e)
