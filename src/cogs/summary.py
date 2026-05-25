"""$summary command — AI-written stock commentary."""

from __future__ import annotations

import discord
from discord.ext import commands

from ..ai import AIClient
from ..indicators import analyze
from ..stocks import StockError, format_money, get_history, get_info


class Summary(commands.Cog):
    def __init__(self, bot: commands.Bot, ai: AIClient):
        self.bot = bot
        self.ai = ai

    @commands.command(name="summary")
    async def summary(self, ctx: commands.Context, ticker: str):
        if not self.ai.available:
            await ctx.send(
                "AI summaries are disabled. Set `GOOGLE_API_KEY` or "
                "`OPENAI_API_KEY` in your `.env` to enable them."
            )
            return

        async with ctx.typing():
            try:
                info = await get_info(ticker)
                df = await get_history(ticker, period="1y")
            except StockError as e:
                await ctx.send(f"Couldn't fetch `{ticker.upper()}`: {e}")
                return
            a = analyze(df, ticker)
            try:
                text = await self.ai.summarize(info, a)
            except Exception as e:
                await ctx.send(f"AI summary failed: {e}")
                return

        embed = discord.Embed(
            title=f"{a.ticker} — analysis ({self.ai.provider})",
            description=text,
            color=discord.Color.blurple(),
        )
        embed.set_footer(
            text=(
                f"Price {format_money(info.price)} | RSI {a.rsi_14:.0f} | "
                f"MACD hist {a.macd_hist:+.3f}  •  Analysis only, not financial advice."
            )
        )
        await ctx.send(embed=embed)

    @summary.error
    async def _missing_arg(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingRequiredArgument):
            prefix = ctx.prefix or "$"
            await ctx.send(f"Usage: `{prefix}summary <ticker>`")


async def setup(bot: commands.Bot):
    ai: AIClient = bot.ai  # type: ignore[attr-defined]
    await bot.add_cog(Summary(bot, ai))
