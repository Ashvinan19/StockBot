"""Configuration settings for the application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    discord_token: str
    command_prefix: str
    database_path: Path
    alert_check_interval_seconds: int
    google_api_key: str | None

    @classmethod
    def from_env(cls) -> Config:
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in."
            )

        db_path = Path(os.getenv("DATABASE_PATH", "data/bot.db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        return cls(
            discord_token=token,
            command_prefix=os.getenv("COMMAND_PREFIX", "$"),
            database_path=db_path,
            alert_check_interval_seconds=int(
                os.getenv("ALERT_CHECK_INTERVAL_SECONDS", "300")
            ),
            google_api_key=os.getenv("GOOGLE_API_KEY") or None,
        )
