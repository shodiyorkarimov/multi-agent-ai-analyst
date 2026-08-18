"""To'liq debug -- barcha pastki qatlam loglarini (tarmoq xatolarini ham) ko'rsatadi."""
import logging
logging.basicConfig(level=logging.DEBUG)  # HAMMA logger uchun, faqat langfuse emas

from src.config import settings, ENV_PATH
from langfuse import Langfuse

print("=" * 60)
print("Public key boshi:", settings.langfuse_public_key[:20] if settings.langfuse_public_key else None)
print("=" * 60)

client = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
    debug=True,
)

with client.start_as_current_span(name="test-span-full-debug") as span:
    span.update(input="salom", output="dunyo")

print("=" * 60)
print("Flush boshlanmoqda...")
client.flush()
print("Flush tugadi.")