"""StockBot.

Holds the typed handles (config, db, ai) that every cog needs. Subclassing here
means cogs can access `self.bot.db` etc. with full type-checking instead of
each call site asserting via `type: ignore`.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from .ai import AIClient
from .config import Config
from .db import Database

log = logging.getLogger(__name__)

COGS: tuple[str, ...] = (
    "src.cogs.general",
    "src.cogs.stocks_cog",
    "src.cogs.watchlist",
    "src.cogs.alerts",
    "src.cogs.analysis",
    "src.cogs.summary",
)


class StockBot(commands.Bot):
    """commands.Bot subclass with typed config, db, and ai attributes."""

    config: Config
    db: Database
    ai: AIClient

    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=config.command_prefix,
            intents=intents,
            help_command=None,
        )

        self.config = config
        self.db = Database(config.database_path)
        self.ai = AIClient(config)

    async def setup_hook(self) -> None:
        await self.db.init()
        for ext in COGS:
            await self.load_extension(ext)
            log.info("Loaded cog: %s", ext)

    async def on_ready(self) -> None:
        user = self.user
        log.info("Logged on as %s (id=%s)", user, getattr(user, "id", "?"))
        ai_status = "gemini" if self.ai.available else "disabled"
        log.info("Prefix: %r  |  AI provider: %s", self.config.command_prefix, ai_status)
