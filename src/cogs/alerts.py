"""Price alerts with a background checker.

Schema lives in src/db.py. The background task polls every
ALERT_CHECK_INTERVAL_SECONDS, fetches each active alert's current price, and
fires + marks-triggered any that cross the threshold.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands, tasks

from ..bot import StockBot
from ..stocks import StockError, format_money, get_quote

log = logging.getLogger(__name__)


class Alerts(commands.Cog):
    def __init__(self, bot: StockBot):
        self.bot = bot
        self.db = bot.db
        self.config = bot.config
        self.check_alerts.change_interval(
            seconds=bot.config.alert_check_interval_seconds
        )
        self.check_alerts.start()

    def cog_unload(self):
        self.check_alerts.cancel()

    @commands.group(name="alert", invoke_without_command=True)
    async def alert(
        self,
        ctx: commands.Context,
        ticker: str,
        direction: str,
        price: float,
    ):
        direction = direction.lower()
        if direction not in ("above", "below"):
            await ctx.send("Direction must be `above` or `below`.")
            return
        if price <= 0:
            await ctx.send("Price must be positive.")
            return

        alert_id = await self.db.add_alert(
            ctx.author.id, ctx.channel.id, ticker, direction, price
        )
        await ctx.send(
            f"Alert #{alert_id} set: notify when **{ticker.upper()}** is "
            f"**{direction} {format_money(price)}**."
        )

    @alert.command(name="remove", aliases=["rm", "del"])
    async def alert_remove(self, ctx: commands.Context, alert_id: int):
        removed = await self.db.remove_alert(ctx.author.id, alert_id)
        if removed:
            await ctx.send(f"Removed alert #{alert_id}.")
        else:
            await ctx.send(f"No alert #{alert_id} owned by you.")

    @commands.command(name="alerts")
    async def list_alerts(self, ctx: commands.Context):
        rows = await self.db.list_alerts(ctx.author.id)
        if not rows:
            prefix = ctx.prefix or "$"
            await ctx.send(
                f"You have no alerts. Try `{prefix}alert AAPL above 200`."
            )
            return

        lines = []
        for r in rows:
            status = "fired" if r["triggered"] else "active"
            lines.append(
                f"`#{r['id']:>3}` {r['ticker']:<6} {r['direction']:<5} "
                f"{format_money(r['price'])}  ({status})"
            )
        embed = discord.Embed(
            title=f"Alerts — {ctx.author.display_name}",
            description="\n".join(lines),
            color=discord.Color.orange(),
        )
        await ctx.send(embed=embed)

    @alert.error
    async def _alert_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            prefix = ctx.prefix or "$"
            await ctx.send(
                f"Usage: `{prefix}alert <ticker> <above|below> <price>` "
                f"(e.g. `{prefix}alert AAPL above 200`)"
            )

    # ----- background task -----

    @tasks.loop(seconds=300)
    async def check_alerts(self):
        try:
            rows = await self.db.active_alerts()
        except Exception:
            log.exception("Failed to load active alerts")
            return
        if not rows:
            return

        triggered: list[int] = []
        by_ticker: dict[str, list[dict]] = {}
        for r in rows:
            by_ticker.setdefault(r["ticker"], []).append(r)

        for ticker, alerts in by_ticker.items():
            try:
                q = await get_quote(ticker)
            except StockError:
                continue

            for a in alerts:
                hit = (
                    (a["direction"] == "above" and q.price >= a["price"])
                    or (a["direction"] == "below" and q.price <= a["price"])
                )
                if not hit:
                    continue
                triggered.append(a["id"])
                channel = self.bot.get_channel(a["channel_id"])
                if channel is None:
                    try:
                        channel = await self.bot.fetch_channel(a["channel_id"])
                    except Exception:
                        log.warning("Could not fetch channel %s", a["channel_id"])
                        continue
                user_mention = f"<@{a['user_id']}>"
                try:
                    await channel.send(
                        f"{user_mention} Alert #{a['id']}: **{ticker}** is "
                        f"{a['direction']} {format_money(a['price'])} — now "
                        f"**{format_money(q.price)}**"
                    )
                except discord.DiscordException:
                    log.exception("Failed to send alert message")

        if triggered:
            await self.db.mark_triggered(triggered)

    @check_alerts.before_loop
    async def _before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot: StockBot):
    await bot.add_cog(Alerts(bot))
