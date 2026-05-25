"""$analyze and $signal commands."""

from __future__ import annotations

import discord
from discord.ext import commands

from ..indicators import analyze
from ..stocks import StockError, format_money, get_history


class AnalysisCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="analyze")
    async def analyze_cmd(self, ctx: commands.Context, ticker: str):
        async with ctx.typing():
            try:
                df = await get_history(ticker, period="1y")
            except StockError as e:
                await ctx.send(f"Couldn't fetch `{ticker.upper()}`: {e}")
                return
            a = analyze(df, ticker)

        color = discord.Color.green() if a.macd_hist >= 0 else discord.Color.red()
        embed = discord.Embed(title=f"{a.ticker} — technical analysis", color=color)
        embed.add_field(
            name="Last close",
            value=format_money(a.last_close),
            inline=True,
        )
        embed.add_field(
            name="52w range",
            value=f"{format_money(a.low_52w)} – {format_money(a.high_52w)}",
            inline=True,
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="SMA 20", value=format_money(a.sma_20), inline=True)
        embed.add_field(name="SMA 50", value=format_money(a.sma_50), inline=True)
        embed.add_field(name="SMA 200", value=format_money(a.sma_200), inline=True)
        embed.add_field(name="RSI(14)", value=f"{a.rsi_14:.1f}", inline=True)
        embed.add_field(
            name="MACD",
            value=f"{a.macd:+.3f} / signal {a.macd_signal:+.3f}",
            inline=True,
        )
        embed.add_field(name="MACD hist", value=f"{a.macd_hist:+.3f}", inline=True)
        embed.add_field(name="Trend", value=a.trend(), inline=False)
        embed.set_footer(text="Analysis only. Not financial advice.")
        await ctx.send(embed=embed)

    @commands.command(name="signal")
    async def signal_cmd(self, ctx: commands.Context, ticker: str):
        async with ctx.typing():
            try:
                df = await get_history(ticker, period="1y")
            except StockError as e:
                await ctx.send(f"Couldn't fetch `{ticker.upper()}`: {e}")
                return
            a = analyze(df, ticker)

        await ctx.send(
            f"**{a.ticker}**: {a.signal()}  (RSI {a.rsi_14:.0f}, "
            f"MACD hist {a.macd_hist:+.3f})  — analysis only, not advice."
        )

    @analyze_cmd.error
    @signal_cmd.error
    async def _missing_arg(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingRequiredArgument):
            prefix = ctx.prefix or "$"
            await ctx.send(
                f"Usage: `{prefix}{ctx.command.name} <ticker>`"
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AnalysisCog(bot))
