"""Audio/ovozli xabar/video orqali qo'shiqni aniqlash — Shazam (kalit kerak emas, ffmpeg kerak)."""
from pathlib import Path

from shazamio import Shazam


async def recognize(path: Path) -> str | None:
    result = await Shazam().recognize(str(path))
    track = result.get("track")
    if not track:
        return None
    text = f"🎵 {track.get('subtitle', '?')} — {track.get('title', '?')}"
    if track.get("url"):
        text += f"\n{track['url']}"
    return text
