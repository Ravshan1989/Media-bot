import logging
import os
import re
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()  # identify.py import qilinishidan oldin (ANTHROPIC_MODEL uchun)

import downloader  # noqa: E402
import identify  # noqa: E402
import shazam  # noqa: E402

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger("media-bot")

URL_RE = re.compile(r"https?://\S+")

HELP = (
    "Salom! Men nima qila olaman:\n"
    "🔗 Instagram/TikTok/YouTube va boshqa havola yuboring — video yoki audioni yuklab beraman\n"
    "🖼 Kino posteri yoki kadrini yuboring — qaysi kino ekanini topaman\n"
    "📝 Qo'shiq so'zidan parcha yoki nomini yozing — qo'shiqni topaman\n"
    "🎤 Audio, ovozli xabar yoki video yuboring — qaysi qo'shiq ekanini aniqlayman"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    m = URL_RE.search(text)
    if m:
        context.user_data["url"] = m.group(0)
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🎬 Video", callback_data="video"), InlineKeyboardButton("🎧 Audio", callback_data="audio")]]
        )
        await update.message.reply_text("Qaysi formatda yuklay?", reply_markup=kb)
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        await update.message.reply_text(await identify.identify_text(text))
    except Exception:
        log.exception("identify_text")
        await update.message.reply_text("Qidirishda xatolik bo'ldi. ANTHROPIC_API_KEY to'g'ri qo'yilganini tekshiring.")


async def on_download_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    url = context.user_data.get("url")
    if not url:
        await q.edit_message_text("Havola topilmadi, qaytadan yuboring.")
        return
    kind = q.data
    await q.edit_message_text("⏳ Yuklanmoqda...")
    path = None
    try:
        path, title = await downloader.download(url, kind)
        chat = q.message.chat
        await chat.send_action(ChatAction.UPLOAD_VIDEO if kind == "video" else ChatAction.UPLOAD_VOICE)
        with path.open("rb") as f:
            if kind == "video":
                await chat.send_video(f, caption=title[:1000], supports_streaming=True)
            else:
                await chat.send_audio(f, title=title[:100])
        await q.message.delete()
    except Exception as e:
        log.exception("download")
        await q.edit_message_text(f"❌ Yuklab bo'lmadi: {str(e)[:300]}")
    finally:
        if path:
            path.unlink(missing_ok=True)
            path.parent.rmdir()


async def _download_tg_file(tg_file, suffix: str) -> Path:
    fd, name = tempfile.mkstemp(prefix="mediabot_", suffix=suffix)
    os.close(fd)
    path = Path(name)
    await tg_file.download_to_drive(path)
    return path


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.chat.send_action(ChatAction.TYPING)
    path = await _download_tg_file(await update.message.photo[-1].get_file(), ".jpg")
    try:
        await update.message.reply_text(await identify.identify_movie(path.read_bytes(), update.message.caption or ""))
    except Exception:
        log.exception("identify_movie")
        await update.message.reply_text("Kinoni aniqlashda xatolik bo'ldi. ANTHROPIC_API_KEY to'g'ri qo'yilganini tekshiring.")
    finally:
        path.unlink(missing_ok=True)


async def on_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    media = msg.voice or msg.audio or msg.video or msg.video_note
    if media.file_size and media.file_size > 20 * 1024 * 1024:
        await msg.reply_text("Fayl 20 MB dan katta. Qisqaroq parcha yuboring.")
        return
    await msg.chat.send_action(ChatAction.TYPING)
    path = await _download_tg_file(await media.get_file(), ".ogg" if msg.voice else ".mp4")
    try:
        result = await shazam.recognize(path)
        await msg.reply_text(result or "Qo'shiqni aniqlay olmadim. Aniqroq/uzunroq parcha yuboring.")
    except Exception:
        log.exception("shazam")
        await msg.reply_text("Aniqlashda xatolik bo'ldi (ffmpeg o'rnatilganini tekshiring).")
    finally:
        path.unlink(missing_ok=True)


def main() -> None:
    app = Application.builder().token(os.environ["BOT_TOKEN"]).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CallbackQueryHandler(on_download_choice, pattern="^(video|audio)$"))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO | filters.VIDEO_NOTE, on_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling()


if __name__ == "__main__":
    main()
