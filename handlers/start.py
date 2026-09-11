from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import MAIN_KEYBOARD

router = Router()

WELCOME_TEXT = (
    "👋 Assalomu alaykum! Men <b>Hisobchi AI</b> botiman.\n\n"
    "📊 <b>1. Hisobchi</b>\n"
    "Menga xarajat yoki daromadingiz haqida oddiy tilda yozing yoki ovozli xabar yuboring, masalan:\n"
    "<i>\"Bozordan 50 000 so'mlik oziq-ovqat oldim\"</i>\n"
    "Men buni tahlil qilib, avtomatik ravishda Google Sheets jadvaliga saqlayman.\n"
    "Pastdagi <b>📊 Hisobot</b> tugmasi (yoki /excel) — barcha yozuvlaringizni Excel faylida beradi.\n"
    "<b>💼 Balans</b> tugmasi — joriy kirim/chiqim/sof qoldiqni ko'rsatadi.\n\n"
    "🧠 <b>2. AI Maslahatchi</b>\n"
    "Menga istalgan hujjat (PDF, rasm, Word yoki matn fayl) yuboring — professional tahlilchi sifatida "
    "uni chuqur tahlil qilib beraman.\n\n"
    "Boshladik! 🚀"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=MAIN_KEYBOARD)
