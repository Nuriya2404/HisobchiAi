# Hisobchi AI — Telegram bot

Ikki funksiyali, shaxsiy foydalanish uchun bot (faqat `TELEGRAM_ALLOWED_USER_ID`da ko'rsatilgan foydalanuvchi bilan ishlaydi):
1. **Hisobchi** — matn, ovozli xabar yoki **chek/hisob-kitob rasmini** AI tahlil qilib, daromad/xarajat (turi, kategoriya, mahsulot, miqdor, birlik narxi, jami summa) sifatida Google Sheets'ga yozadi; `/excel` buyrug'i bilan Excel faylida eksport qilib beradi. Chekdagi har bir mahsulot alohida qator sifatida qo'shiladi. Summani aniqlab bo'lmasa, bot uni so'rab oladi.
2. **AI Maslahatchi** — yuborilgan hujjatni (PDF, Word, matn) professional tahlilchi sifatida chuqur tahlil qiladi.

Barcha AI vazifalari (matn tahlili, hujjat tahlili, ovozni matnga aylantirish) faqat **OpenAI** orqali bajariladi — Anthropic kaliti shart emas.

## 1. O'rnatish

```bash
pip install -r requirements.txt
```

## 2. Muhit o'zgaruvchilari

`.env.example` faylidan nusxa olib `.env` yarating va quyidagilarni to'ldiring:

```bash
cp .env.example .env
```

- `TELEGRAM_BOT_TOKEN` — Telegram'da [@BotFather](https://t.me/BotFather) orqali `/newbot` bilan olinadi.
- `OPENAI_API_KEY` — matn/hujjat tahlili va ovozli xabarlarni matnga aylantirish (Whisper) uchun. https://platform.openai.com
- `OPENAI_MODEL` — standart `gpt-4o` (matn, rasm va PDF'ni tushunadi).
- `GOOGLE_CREDENTIALS_PATH` — quyidagi 3-bandda olinadigan service account JSON fayl yo'li.
- `GOOGLE_SPREADSHEET_ID` — Google Sheets jadval linkidagi ID (`https://docs.google.com/spreadsheets/d/<ID>/edit`).
- `TELEGRAM_ALLOWED_USER_ID` — botdan foydalanishga ruxsat etilgan yagona Telegram foydalanuvchi ID'si. Boshqa hech kim bot bilan ishlay olmaydi.

## 3. Google Sheets ulash

1. [Google Cloud Console](https://console.cloud.google.com/) da yangi loyiha yarating.
2. **Google Sheets API** va **Google Drive API**'ni yoqing (APIs & Services → Library).
3. **IAM & Admin → Service Accounts** bo'limidan yangi service account yarating, so'ng **Keys → Add Key → JSON** orqali kalitni yuklab oling — shu faylni loyihaga `credentials.json` nomi bilan saqlang.
4. Yangi Google Sheets jadval oching va uni service account'ning email manzili bilan (masalan `xxx@xxx.iam.gserviceaccount.com`, JSON fayl ichida bor) **Editor** huquqi bilan ulashing.
5. Jadval ID'sini `.env` fayliga qo'ying.

Bot ma'lumotlarni `user_<chat_id>` nomli varaqqa yozadi.

## 4. Ishga tushirish

```bash
python bot.py
```

## Eslatma

- Ovozli xabarlar Whisper orqali o'zbek tili hinti bilan tanib olinadi; sifat yetarli bo'lmasa `services/speech_service.py`'dagi `language="uz"` parametrini olib tashlab ko'ring.
- Hujjat tahlilida PDF va rasmlar to'g'ridan-to'g'ri `gpt-4o`'ga yuboriladi, `.docx`/`.txt` fayllardan matn ajratib olinadi.
- Ruxsat etilmagan foydalanuvchidan xabar kelsa, bot faqat qisqa rad javobi beradi va hech qanday AI/Sheets so'rovi yubormaydi.
