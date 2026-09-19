import logging
import os
import tempfile

from aiogram import F, Router
from aiogram.types import Message

from services.ai_service import AIService
from services.document_service import prepare_content_blocks

logger = logging.getLogger(__name__)
router = Router()

MAX_MESSAGE_LEN = 4000


@router.message(F.document)
async def handle_document(message: Message, bot, ai_service: AIService):
    filename = message.document.file_name or "hujjat"
    await message.answer(f'📄 "{filename}" tahlil qilinmoqda, biroz kuting...')

    file = await bot.get_file(message.document.file_id)
    suffix = os.path.splitext(filename)[1] or ""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await bot.download_file(file.file_path, tmp_path)
        try:
            blocks = prepare_content_blocks(tmp_path, filename)
        except ValueError as exc:
            await message.answer(f"⚠️ {exc}")
            return
    finally:
        os.remove(tmp_path)

    await _run_analysis(message, ai_service, blocks, filename)


async def _run_analysis(message: Message, ai_service: AIService, blocks: list, filename: str):
    try:
        analysis = ai_service.analyze_document(blocks, filename)
    except Exception:
        logger.exception("Hujjatni tahlil qilishda xatolik")
        await message.answer("⚠️ Hujjatni tahlil qilishda xatolik yuz berdi.")
        return

    for i in range(0, len(analysis), MAX_MESSAGE_LEN):
        await message.answer(analysis[i : i + MAX_MESSAGE_LEN])
