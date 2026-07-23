from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    chat_id: int | None
    timezone: str
    root: Path

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def outbox_dir(self) -> Path:
        return self.data_dir / "outbox"

    @property
    def runtime_dir(self) -> Path:
        return self.data_dir / "runtime"

    @property
    def db_path(self) -> Path:
        return self.runtime_dir / "bot.sqlite3"

    @property
    def profile_path(self) -> Path:
        return self.root / "profile" / "profile.yaml"


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Copy .env.example to .env and set the token.")

    chat_raw = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    chat_id = int(chat_raw) if chat_raw else None
    tz = os.getenv("TZ", "Europe/Moscow").strip() or "Europe/Moscow"
    return Settings(bot_token=token, chat_id=chat_id, timezone=tz, root=ROOT)
