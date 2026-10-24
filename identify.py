"""Rasm bo'yicha kino va matn (qo'shiq so'zlari/nomi) bo'yicha musiqa topish — Claude (+ veb-qidiruv)."""
import base64
import os

from anthropic import AsyncAnthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
WEB_SEARCH = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}]

_client: AsyncAnthropic | None = None


def client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()  # ANTHROPIC_API_KEY ni muhitdan oladi
    return _client


async def _ask(content: list[dict], system: str) -> str:
    resp = await client().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        tools=WEB_SEARCH,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


async def identify_movie(image: bytes, caption: str = "") -> str:
    system = (
        "Sen kino topuvchi yordamchisan. Foydalanuvchi poster, kadr yoki skrinshot yuboradi. "
        "Qaysi kino/serial ekanini aniqla (kerak bo'lsa veb-qidiruvdan foydalan). "
        "O'zbek tilida qisqa javob ber: nomi (original va yili), janri, qisqa mazmuni, "
        "bosh rollar. Aniq bilmasang, eng ehtimoliy variantlarni ayt va shuni belgila."
    )
    content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(image).decode()},
        },
        {"type": "text", "text": caption or "Bu qaysi kino?"},
    ]
    return await _ask(content, system)


async def identify_text(query: str) -> str:
    system = (
        "Sen musiqa va kino topuvchi yordamchisan. Foydalanuvchi qo'shiq so'zlaridan parcha, "
        "qo'shiq nomi yoki kino tavsifini yozadi. Veb-qidiruv orqali topib, o'zbek tilida "
        "qisqa javob ber: ijrochi — qo'shiq nomi (yoki kino nomi, yili), va qayerdan "
        "eshitish/ko'rish mumkin. Topa olmasang, ochiq ayt."
    )
    return await _ask([{"type": "text", "text": query}], system)
