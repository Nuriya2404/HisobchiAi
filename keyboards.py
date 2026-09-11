from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_REPORT = "📊 Hisobot"
BTN_BALANCE = "💼 Balans"
BTN_ADVISOR = "🧠 AI Maslahatchi"
BTN_HELP = "ℹ️ Yordam"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_REPORT), KeyboardButton(text=BTN_BALANCE)],
        [KeyboardButton(text=BTN_ADVISOR), KeyboardButton(text=BTN_HELP)],
    ],
    resize_keyboard=True,
    is_persistent=True,
)
