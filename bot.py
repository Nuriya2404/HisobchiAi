import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import load_config
from handlers import accountant, advisor, export, menu, start
from middlewares.access_control import AccessControlMiddleware
from services.ai_service import AIService
from services.sheets_service import SheetsService
from services.speech_service import SpeechService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


async def main():
    config = load_config()

    ai_service = AIService(config.openai_api_key, config.openai_model)
    speech_service = SpeechService(config.openai_api_key)
    sheets_service = SheetsService(config.google_credentials_path, config.google_spreadsheet_id)

    bot = Bot(token=config.telegram_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp["ai_service"] = ai_service
    dp["speech_service"] = speech_service
    dp["sheets_service"] = sheets_service

    dp.message.outer_middleware(AccessControlMiddleware(config.allowed_user_id))

    dp.include_router(start.router)
    dp.include_router(export.router)
    dp.include_router(menu.router)
    dp.include_router(advisor.router)
    dp.include_router(accountant.router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="excel", description="Ma'lumotlarni Excel'da olish"),
        ]
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
