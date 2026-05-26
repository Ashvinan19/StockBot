"""Entry point. Loads config and runs the bot."""

from __future__ import annotations

import asyncio
import logging

from src.bot import StockBot
from src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("stockbot")


async def main() -> None:
    config = Config.from_env()
    bot = StockBot(config)
    await bot.start(config.discord_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down (Ctrl+C).")
