from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class AccessControlMiddleware(BaseMiddleware):
    """Botni faqat bitta ruxsat etilgan Telegram foydalanuvchisi bilan ishlashini ta'minlaydi."""

    def __init__(self, allowed_user_id: int):
        self.allowed_user_id = allowed_user_id

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if event.from_user is None or event.from_user.id != self.allowed_user_id:
            await event.answer("⛔ Kechirasiz, bu bot faqat shaxsiy foydalanish uchun mo'ljallangan.")
            return None
        return await handler(event, data)
