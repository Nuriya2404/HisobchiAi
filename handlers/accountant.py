import logging
import os
import tempfile

from aiogram import F, Router
from aiogram.types import Message

from services.ai_service import AIService
from services.sheets_service import SheetsService
from services.speech_service import SpeechService

logger = logging.getLogger(__name__)
router = Router()

CONFIRMATION_TEMPLATE = (
    "✅ Yozildi!\n\n"
    "🗂 Turi: {type}\n"
    "📁 Kategoriya: {category}\n"
    "💵 Summa: {amount} {currency}\n"
    "📝 Izoh: {description}\n"
    "📅 Sana: {date}"
)

NOT_FINANCIAL_TEXT = (
    "🤔 Bu xabarda moliyaviy ma'lumot topa olmadim.\n"
    "Masalan: \"Taksiga 20 000 so'm sarfladim\" yoki \"Ish haqim 3 000 000 so'm tushdi\" deb yozib ko'ring."
)


@router.message(F.voice)
async def handle_voice(
    message: Message,
    bot,
    ai_service: AIService,
    speech_service: SpeechService,
    sheets_service: SheetsService,
):
    await bot.send_chat_action(message.chat.id, "typing")
    file = await bot.get_file(message.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await bot.download_file(file.file_path, tmp_path)
        try:
            text = speech_service.transcribe(tmp_path)
        except Exception:
            logger.exception("Ovozni matnga aylantirishda xatolik")
            await message.answer("⚠️ Ovozli xabarni tanib bo'lmadi. Iltimos, qaytadan urinib ko'ring.")
            return
    finally:
        os.remove(tmp_path)

    await message.answer(f"🎙 Eshitdim: <i>{text}</i>")
    await process_finance_text(message, text, ai_service, sheets_service)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, ai_service: AIService, sheets_service: SheetsService):
    await process_finance_text(message, message.text, ai_service, sheets_service)


async def process_finance_text(
    message: Message, text: str, ai_service: AIService, sheets_service: SheetsService
):
    try:
        record = ai_service.analyze_finance_text(text)
    except Exception:
        logger.exception("Moliyaviy matnni tahlil qilishda xatolik")
        await message.answer("⚠️ Tahlil qilishda xatolik yuz berdi. Birozdan so'ng qaytadan urinib ko'ring.")
        return

    if not record:
        await message.answer(NOT_FINANCIAL_TEXT)
        return

    try:
        sheets_service.append_record(message.chat.id, record)
    except Exception:
        logger.exception("Google Sheets'ga saqlashda xatolik")
        await message.answer("⚠️ Google Sheets'ga saqlashda xatolik yuz berdi.")
        return

    await message.answer(
        CONFIRMATION_TEMPLATE.format(
            type=record.get("type", "-"),
            category=record.get("category", "-"),
            amount=record.get("amount", "-"),
            currency=record.get("currency", "so'm"),
            description=record.get("description", "-"),
            date=record.get("date", "-"),
        )
    )
