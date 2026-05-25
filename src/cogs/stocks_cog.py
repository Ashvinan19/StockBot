"""$price and $info commands."""

from __future__ import annotations

import discord
from discord.ext import commands

from ..stocks import StockError, format_money, get_info, get_quote


def _color_for_change(pct: float) -> discord.Color:
    if pct > 0:
        return discord.Color.green()
    if pct < 0:
        return discord.Color.red()
    return discord.Color.light_grey()


class Stocks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="price")
    async def price(self, ctx: commands.Context, ticker: str):
        async with ctx.typing():
            try:
                q = await get_quote(ticker)
            except StockError as e:
                await ctx.send(f"Couldn't fetch `{ticker.upper()}`: {e}")
                return

        arrow = "▲" if q.change >= 0 else "▼"
        embed = discord.Embed(
            title=f"{q.ticker}",
            color=_color_for_change(q.change_pct),
            description=(
                f"**{format_money(q.price, q.currency)}**  "
                f"{arrow} {format_money(q.change, q.currency)} "
                f"({q.change_pct:+.2f}%)"
            ),
        )
        embed.set_footer(text=f"Previous close: {format_money(q.previous_close, q.currency)}")
        await ctx.send(embed=embed)

    @commands.command(name="info")
    async def info(self, ctx: commands.Context, ticker: str):
        async with ctx.typing():
            try:
                i = await get_info(ticker)
            except StockError as e:
                await ctx.send(f"Couldn't fetch `{ticker.upper()}`: {e}")
                return

        title = f"{i.ticker}"
        if i.name:
            title += f" — {i.name}"

        embed = discord.Embed(title=title, color=_color_for_change(i.change_pct))
        embed.add_field(
            name="Price",
            value=f"{format_money(i.price, i.currency)} ({i.change_pct:+.2f}%)",
            inline=True,
        )
        embed.add_field(
            name="Prev close",
            value=format_money(i.previous_close, i.currency),
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        if i.day_high is not None and i.day_low is not None:
            embed.add_field(
                name="Day range",
                value=(
                    f"{format_money(i.day_low, i.currency)} - "
                    f"{format_money(i.day_high, i.currency)}"
                ),
                inline=True,
            )
        embed.add_field(
            name="Volume",
            value=f"{i.volume:,}" if i.volume else "n/a",
            inline=True,
        )
        embed.add_field(
            name="Market cap",
            value=format_money(i.market_cap, i.currency) if i.market_cap else "n/a",
            inline=True,
        )
        await ctx.send(embed=embed)

    @price.error
    @info.error
    async def _missing_arg(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingRequiredArgument):
            prefix = ctx.prefix or "$"
            await ctx.send(
                f"Usage: `{prefix}{ctx.command.name} <ticker>` (e.g. `{prefix}{ctx.command.name} AAPL`)"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))
