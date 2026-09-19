from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import MAIN_KEYBOARD

router = Router()

WELCOME_TEXT = (
    "👋 Assalomu alaykum! Men <b>Hisobchi AI</b> botiman.\n\n"
    "📊 <b>1. Hisobchi</b>\n"
    "Menga xarajat yoki daromadingiz haqida oddiy tilda yozing yoki ovozli xabar yuboring, masalan:\n"
    "<i>\"Bugun 3 ta daftar oldim, har biri 15 ming so'mdan\"</i>\n"
    "Men buni tahlil qilib, avtomatik ravishda Google Sheets jadvaliga saqlayman.\n"
    "📸 <b>Chek yoki hisob-kitob rasmini</b> yuborsangiz, undagi mahsulotlarni avtomatik o'qib, "
    "har birini alohida qator qilib jadvalga qo'shaman.\n"
    "Pastdagi <b>📊 Hisobot</b> tugmasi (yoki /excel) — barcha yozuvlaringizni Excel faylida beradi.\n"
    "<b>💼 Balans</b> tugmasi — joriy kirim/chiqim/sof qoldiqni ko'rsatadi.\n\n"
    "🧠 <b>2. AI Maslahatchi</b>\n"
    "Menga PDF, Word yoki matn fayl yuboring — professional tahlilchi sifatida uni chuqur tahlil qilib "
    "beraman.\n\n"
    "Boshladik! 🚀"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=MAIN_KEYBOARD)
