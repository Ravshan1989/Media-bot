# Media-bot

Telegram bot (Python):

- 🔗 Instagram / TikTok / YouTube va boshqa havoladan video yoki audio yuklaydi (yt-dlp)
- 🖼 Kino posteri/kadri rasmidan kinoni topadi (Claude + veb-qidiruv)
- 📝 Qo'shiq so'zidan parcha yoki nomi bo'yicha qo'shiqni topadi (Claude + veb-qidiruv)
- 🎤 Audio / ovozli xabar / video orqali qo'shiqni aniqlaydi (Shazam)

## Ishga tushirish

Kerak: Python 3.10+, `ffmpeg` (Shazam uchun).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN va ANTHROPIC_API_KEY ni to'ldiring
python bot.py
```

Eslatma: Telegram bot orqali 50 MB dan katta fayl yuborib bo'lmaydi. Ba'zi saytlar (masalan Instagram) yopiq/shaxsiy videolarni yuklashga ruxsat bermaydi.
