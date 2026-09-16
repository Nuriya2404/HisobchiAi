import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    telegram_token: str
    openai_api_key: str
    openai_model: str
    google_credentials_path: Optional[str]
    google_credentials_json: Optional[str]
    google_spreadsheet_id: str
    allowed_user_id: int


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} muhit o'zgaruvchisi topilmadi. .env faylini tekshiring "
            f"(.env.example namunasiga qarang)."
        )
    return value


def load_config() -> Config:
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not credentials_path and not credentials_json:
        raise RuntimeError(
            "GOOGLE_CREDENTIALS_PATH yoki GOOGLE_CREDENTIALS_JSON'dan birini belgilang. "
            "Lokal ishga tushirishda fayl yo'li, bulutli deploy'da (Railway va h.k.) "
            "esa JSON matnini muhit o'zgaruvchisiga qo'ying."
        )

    return Config(
        telegram_token=_require("TELEGRAM_BOT_TOKEN"),
        openai_api_key=_require("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        google_credentials_path=credentials_path,
        google_credentials_json=credentials_json,
        google_spreadsheet_id=_require("GOOGLE_SPREADSHEET_ID"),
        allowed_user_id=int(_require("TELEGRAM_ALLOWED_USER_ID")),
    )
