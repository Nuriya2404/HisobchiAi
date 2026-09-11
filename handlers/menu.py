import logging

from aiogram import F, Router
from aiogram.types import Message

from handlers.export import send_excel_report
from handlers.start import WELCOME_TEXT
from keyboards import BTN_ADVISOR, BTN_BALANCE, BTN_HELP, BTN_REPORT
from services.sheets_service import SheetsService

logger = logging.getLogger(__name__)
router = Router()

ADVISOR_HINT_TEXT = (
    "🧠 <b>AI Maslahatchi</b>\n\n"
    "Menga PDF, rasm (jpg/png) yoki Word/matn fayl yuboring — professional tahlilchi sifatida "
    "uni chuqur tahlil qilib beraman."
)


@router.message(F.text == BTN_REPORT)
async def menu_report(message: Message, sheets_service: SheetsService):
    await send_excel_report(message, sheets_service)


@router.message(F.text == BTN_BALANCE)
async def menu_balance(message: Message, sheets_service: SheetsService):
    try:
        records = sheets_service.get_records(message.chat.id)
    except Exception:
        logger.exception("Google Sheets'dan o'qishda xatolik")
        await message.answer("⚠️ Google Sheets'dan ma'lumot olishda xatolik yuz berdi.")
        return

    if not records:
        await message.answer(
            "📭 Hozircha saqlangan ma'lumot yo'q. Avval menga xarajat yoki daromad haqida yozing."
        )
        return

    totals: dict[str, dict[str, float]] = {}
    for record in records:
        currency = str(record.get("Valyuta") or "so'm").strip() or "so'm"
        try:
            amount = float(record.get("Summa", 0) or 0)
        except (TypeError, ValueError):
            amount = 0.0
        entry = totals.setdefault(currency, {"income": 0.0, "expense": 0.0})
        record_type = str(record.get("Turi", "")).strip().lower()
        if record_type == "kirim":
            entry["income"] += amount
        elif record_type == "chiqim":
            entry["expense"] += amount

    lines = ["💼 <b>Balans</b>\n"]
    for currency, values in totals.items():
        net = values["income"] - values["expense"]
        lines.append(
            f"<b>{currency}</b>\n"
            f"  Kirim: {values['income']:,.0f}\n"
            f"  Chiqim: {values['expense']:,.0f}\n"
            f"  Sof qoldiq: {net:,.0f}\n"
        )
    await message.answer("\n".join(lines))


@router.message(F.text == BTN_ADVISOR)
async def menu_advisor(message: Message):
    await message.answer(ADVISOR_HINT_TEXT)


@router.message(F.text == BTN_HELP)
async def menu_help(message: Message):
    await message.answer(WELCOME_TEXT)
