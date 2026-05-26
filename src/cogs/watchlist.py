"""$watch add / remove / list commands."""

from __future__ import annotations

import discord
from discord.ext import commands

from ..bot import StockBot
from ..stocks import StockError, get_quote


class Watchlist(commands.Cog):
    def __init__(self, bot: StockBot):
        self.bot = bot
        self.db = bot.db

    @commands.group(name="watch", invoke_without_command=True)
    async def watch(self, ctx: commands.Context):
        prefix = ctx.prefix or "$"
        await ctx.send(
            f"Subcommands: `{prefix}watch add <ticker>`, "
            f"`{prefix}watch remove <ticker>`, `{prefix}watch list`"
        )

    @watch.command(name="add")
    async def watch_add(self, ctx: commands.Context, ticker: str):
        symbol = ticker.upper()
        added = await self.db.add_watch(ctx.author.id, symbol)
        if added:
            await ctx.send(f"Added **{symbol}** to your watchlist.")
        else:
            await ctx.send(f"**{symbol}** is already on your watchlist.")

    @watch.command(name="remove", aliases=["rm", "del"])
    async def watch_remove(self, ctx: commands.Context, ticker: str):
        symbol = ticker.upper()
        removed = await self.db.remove_watch(ctx.author.id, symbol)
        if removed:
            await ctx.send(f"Removed **{symbol}** from your watchlist.")
        else:
            await ctx.send(f"**{symbol}** is not on your watchlist.")

    @watch.command(name="list", aliases=["ls"])
    async def watch_list(self, ctx: commands.Context):
        tickers = await self.db.list_watch(ctx.author.id)
        if not tickers:
            prefix = ctx.prefix or "$"
            await ctx.send(
                f"Your watchlist is empty. Add one with `{prefix}watch add AAPL`."
            )
            return

        async with ctx.typing():
            lines: list[str] = []
            for sym in tickers:
                try:
                    q = await get_quote(sym)
                    arrow = "▲" if q.change >= 0 else "▼"
                    lines.append(
                        f"`{sym:<6}` {q.price:>10,.2f}  {arrow} {q.change_pct:+.2f}%"
                    )
                except StockError:
                    lines.append(f"`{sym:<6}` (data unavailable)")

        embed = discord.Embed(
            title=f"Watchlist — {ctx.author.display_name}",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed)


async def setup(bot: StockBot):
    await bot.add_cog(Watchlist(bot))
