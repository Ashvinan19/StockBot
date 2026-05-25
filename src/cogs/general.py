"""Basic commands: hello, ping, help."""

from __future__ import annotations

import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="hello")
    async def hello(self, ctx: commands.Context):
        await ctx.send(f"Hello {ctx.author.mention}!")

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! {latency_ms} ms")

    @commands.command(name="help")
    async def help_cmd(self, ctx: commands.Context):
        prefix = ctx.prefix or "$"
        embed = discord.Embed(
            title="StockBot commands",
            color=discord.Color.blurple(),
            description="All commands are prefixed with `" + prefix + "`.",
        )
        embed.add_field(
            name="General",
            value=(
                f"`{prefix}hello` — say hi\n"
                f"`{prefix}ping` — latency\n"
                f"`{prefix}help` — this message"
            ),
            inline=False,
        )
        embed.add_field(
            name="Stocks",
            value=(
                f"`{prefix}price AAPL` — current price\n"
                f"`{prefix}info TSLA` — detailed info"
            ),
            inline=False,
        )
        embed.add_field(
            name="Watchlist",
            value=(
                f"`{prefix}watch add AAPL`\n"
                f"`{prefix}watch remove AAPL`\n"
                f"`{prefix}watch list`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Alerts",
            value=(
                f"`{prefix}alert AAPL above 200`\n"
                f"`{prefix}alert TSLA below 150`\n"
                f"`{prefix}alerts` — list your alerts\n"
                f"`{prefix}alert remove <id>`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Analysis",
            value=(
                f"`{prefix}analyze AAPL` — full indicator breakdown\n"
                f"`{prefix}signal NVDA` — quick momentum signal\n"
                f"`{prefix}summary AAPL` — AI summary (analysis only, not advice)"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
