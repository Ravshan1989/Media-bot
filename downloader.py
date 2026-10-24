"""Havola (Instagram, TikTok, YouTube va h.k.) orqali video/audio yuklash — yt-dlp."""
import asyncio
import tempfile
from pathlib import Path

import yt_dlp

TG_LIMIT = 50 * 1024 * 1024  # Telegram bot fayl yuborish limiti

FORMATS = {
    "video": "bv*[height<=480]+ba/b[height<=480]/bv*+ba/b",
    "audio": "bestaudio[ext=m4a]/bestaudio/best",
}


def _download(url: str, kind: str, out_dir: Path) -> tuple[Path, str]:
    opts = {
        "format": FORMATS[kind],
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = Path(ydl.prepare_filename(info))
        if not path.exists():  # birlashtirilgandan keyin kengaytma o'zgargan bo'lishi mumkin
            path = next(out_dir.iterdir())
    return path, info.get("title") or ""


async def download(url: str, kind: str = "video") -> tuple[Path, str]:
    """Faylni vaqtinchalik papkaga yuklaydi. Chaqiruvchi faylni o'chirishi kerak."""
    out_dir = Path(tempfile.mkdtemp(prefix="mediabot_"))
    path, title = await asyncio.to_thread(_download, url, kind, out_dir)
    if path.stat().st_size > TG_LIMIT:
        path.unlink(missing_ok=True)
        raise ValueError("Fayl 50 MB dan katta, Telegram bot orqali yuborib bo'lmaydi.")
    return path, title
