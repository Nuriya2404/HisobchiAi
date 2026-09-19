import logging
import os
import re
import tempfile
from typing import Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from services.ai_service import AIService
from services.document_service import prepare_content_blocks
from services.sheets_service import SheetsService
from services.speech_service import SpeechService

logger = logging.getLogger(__name__)
router = Router()


class RecordStates(StatesGroup):
    waiting_for_amount = State()


NOT_FINANCIAL_TEXT = (
    "🤔 Bu xabarda moliyaviy ma'lumot topa olmadim.\n"
    "Masalan: \"Taksiga 20 000 so'm sarfladim\" yoki \"Ish haqim 3 000 000 so'm tushdi\" deb yozib ko'ring."
)

ASK_AMOUNT_TEXT = "💰 Summani aniqlay olmadim. Iltimos, summani raqam bilan yuboring (masalan: 45000)."


@router.message(RecordStates.waiting_for_amount, F.text)
async def handle_amount_reply(
    message: Message,
    state: FSMContext,
    ai_service: AIService,
    sheets_service: SheetsService,
):
    amount = _extract_number(message.text or "")
    if amount is None:
        await state.clear()
        await process_finance_text(message, message.text or "", ai_service, sheets_service, state)
        return

    data = await state.get_data()
    record: Optional[dict] = data.get("pending_record")
    await state.clear()

    if not record:
        await message.answer("⚠️ Nimadir xato ketdi, iltimos qaytadan yozib ko'ring.")
        return

    record["amount"] = amount
    if not record.get("unit_price"):
        record["unit_price"] = amount
    if not record.get("quantity"):
        record["quantity"] = 1

    await _save_and_confirm(message, record, sheets_service)


@router.message(F.photo)
async def handle_photo(
    message: Message,
    bot,
    ai_service: AIService,
    sheets_service: SheetsService,
):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer("🧾 Rasmni tahlil qilyapman...")

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await bot.download_file(file.file_path, tmp_path)
        blocks = prepare_content_blocks(tmp_path, "chek.jpg")
    finally:
        os.remove(tmp_path)

    try:
        records = ai_service.analyze_finance_receipt(blocks, "chek.jpg")
    except Exception:
        logger.exception("Chekni tahlil qilishda xatolik")
        await message.answer("⚠️ Rasmni tahlil qilishda xatolik yuz berdi.")
        return

    if not records:
        await message.answer(
            "🤔 Rasmda moliyaviy ma'lumot topa olmadim. Aniqroq chek yoki hisob-kitob rasmini yuborib ko'ring."
        )
        return

    saved = []
    skipped = 0
    for record in records:
        amount = record.get("amount")
        if amount in (None, "", 0):
            skipped += 1
            continue
        try:
            sheets_service.append_record(message.chat.id, record)
            saved.append(record)
        except Exception:
            logger.exception("Google Sheets'ga saqlashda xatolik")
            await message.answer("⚠️ Google Sheets'ga saqlashda xatolik yuz berdi.")
            return

    if not saved:
        await message.answer("🤔 Rasmda aniq summalarni aniqlay olmadim. Ma'lumotni qo'lda yozib ko'ring.")
        return

    lines = [f"✅ {len(saved)} ta yozuv qo'shildi:\n"]
    total = 0.0
    currency = saved[0].get("currency", "so'm")
    for record in saved:
        product = record.get("product") or record.get("category", "-")
        amount = record.get("amount", 0)
        lines.append(f"• {product} — {amount} {record.get('currency', currency)}")
        try:
            total += float(amount)
        except (TypeError, ValueError):
            pass
    lines.append(f"\n💵 Jami: {total:,.0f} {currency}")
    if skipped:
        lines.append(f"\n⚠️ {skipped} ta qatorning summasini aniqlay olmadim, ular qo'shilmadi.")

    await message.answer("\n".join(lines))


@router.message(F.voice)
async def handle_voice(
    message: Message,
    bot,
    ai_service: AIService,
    speech_service: SpeechService,
    sheets_service: SheetsService,
    state: FSMContext,
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
    await process_finance_text(message, text, ai_service, sheets_service, state)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(
    message: Message,
    ai_service: AIService,
    sheets_service: SheetsService,
    state: FSMContext,
):
    await process_finance_text(message, message.text, ai_service, sheets_service, state)


async def process_finance_text(
    message: Message,
    text: str,
    ai_service: AIService,
    sheets_service: SheetsService,
    state: FSMContext,
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

    amount = record.get("amount")
    if amount in (None, "", 0):
        await state.update_data(pending_record=record)
        await state.set_state(RecordStates.waiting_for_amount)
        await message.answer(ASK_AMOUNT_TEXT)
        return

    await _save_and_confirm(message, record, sheets_service)


async def _save_and_confirm(message: Message, record: dict, sheets_service: SheetsService) -> None:
    try:
        sheets_service.append_record(message.chat.id, record)
    except Exception:
        logger.exception("Google Sheets'ga saqlashda xatolik")
        await message.answer("⚠️ Google Sheets'ga saqlashda xatolik yuz berdi.")
        return

    await message.answer(_format_confirmation(record))


def _format_confirmation(record: dict) -> str:
    lines = [
        "✅ Yozildi!\n",
        f"🗂 Turi: {record.get('type', '-')}",
        f"📁 Kategoriya: {record.get('category', '-')}",
    ]
    if record.get("product"):
        lines.append(f"📦 Mahsulot: {record['product']}")
    if record.get("quantity"):
        lines.append(f"🔢 Miqdor: {record['quantity']}")
    if record.get("unit_price"):
        lines.append(f"🏷 Birlik narxi: {record['unit_price']}")
    currency = record.get("currency") or "so'm"
    lines.append(f"💵 Summa: {record.get('amount', '-')} {currency}")
    lines.append(f"📝 Izoh: {record.get('description', '-')}")
    lines.append(f"📅 Sana: {record.get('date', '-')}")
    return "\n".join(lines)


def _extract_number(text: str) -> Optional[float]:
    match = re.search(r"\d[\d\s.,]*", text)
    if not match:
        return None
    cleaned = match.group(0).replace(" ", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None
