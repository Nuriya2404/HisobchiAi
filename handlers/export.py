import logging
import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

from services.excel_service import build_excel
from services.sheets_service import SheetsService

logger = logging.getLogger(__name__)
router = Router()


async def send_excel_report(message: Message, sheets_service: SheetsService):
    await message.answer("⏳ Ma'lumotlar tayyorlanmoqda...")

    try:
        records = sheets_service.get_records(message.chat.id)
    except Exception:
        logger.exception("Google Sheets'dan o'qishda xatolik")
        await message.answer("⚠️ Google Sheets'dan ma'lumot olishda xatolik yuz berdi.")
        return

    if not records:
        await message.answer(
            "📭 Hozircha saqlangan ma'lumot yo'q. Avval menga xarajat yoki daromad haqida yozing yoki "
            "ovozli xabar yuboring."
        )
        return

    file_path = build_excel(records, message.chat.id)
    try:
        await message.answer_document(
            FSInputFile(file_path, filename="hisobot.xlsx"),
            caption="📊 Sizning moliyaviy hisobotingiz",
        )
    finally:
        os.remove(file_path)


@router.message(Command("excel", "export"))
async def cmd_export(message: Message, sheets_service: SheetsService):
    await send_excel_report(message, sheets_service)
