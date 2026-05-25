"""Entry point. Loads config, opens the DB, registers cogs, runs the bot."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from src.ai import AIClient
from src.config import Config
from src.db import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("stockbot")


COGS = [
    "src.cogs.general",
    "src.cogs.stocks_cog",
    "src.cogs.watchlist",
    "src.cogs.alerts",
    "src.cogs.analysis",
    "src.cogs.summary",
]


async def main() -> None:
    config = Config.from_env()

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix=config.command_prefix,
        intents=intents,
        help_command=None,
    )
    bot.config = config  # type: ignore[attr-defined]
    bot.db = Database(config.database_path)  # type: ignore[attr-defined]
    bot.ai = AIClient(config)  # type: ignore[attr-defined]

    await bot.db.init()  # type: ignore[attr-defined]

    @bot.event
    async def on_ready():
        log.info("Logged on as %s (id=%s)", bot.user, bot.user.id if bot.user else "?")
        log.info("Prefix: %r  |  AI provider: %s", config.command_prefix, bot.ai.provider or "disabled")  # type: ignore[attr-defined]

    for ext in COGS:
        await bot.load_extension(ext)
        log.info("Loaded cog: %s", ext)

    await bot.start(config.discord_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutting down (Ctrl+C).")
