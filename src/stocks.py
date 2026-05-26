"""Stock data wrapper around yfinance.

yfinance is synchronous and can be slow, so every public function offloads to a
thread so it never blocks the event loop.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


class StockError(Exception):
    """Raised when stock data cannot be retrieved or parsed."""


@dataclass
class Quote:
    ticker: str
    price: float
    previous_close: float
    currency: str | None = None

    @property
    def change(self) -> float:
        return self.price - self.previous_close

    @property
    def change_pct(self) -> float:
        if not self.previous_close:
            return 0.0
        return (self.change / self.previous_close) * 100


@dataclass
class StockInfo:
    ticker: str
    name: str | None
    price: float
    previous_close: float
    day_high: float | None
    day_low: float | None
    volume: int | None
    market_cap: int | None
    currency: str | None

    @property
    def change_pct(self) -> float:
        if not self.previous_close:
            return 0.0
        return ((self.price - self.previous_close) / self.previous_close) * 100


def _ticker(symbol: str) -> yf.Ticker:
    symbol = symbol.strip().upper()
    if not symbol or any(c.isspace() for c in symbol):
        raise StockError(f"Invalid ticker: {symbol!r}")
    return yf.Ticker(symbol)


def _quote_sync(symbol: str) -> Quote:
    t = _ticker(symbol)
    fast = t.fast_info
    try:
        price = float(fast["last_price"])
        prev = float(fast["previous_close"])
    except (KeyError, TypeError, ValueError) as e:
        raise StockError(f"No data for {symbol.upper()}") from e
    currency = fast.get("currency") if hasattr(fast, "get") else None
    return Quote(
        ticker=symbol.upper(),
        price=price,
        previous_close=prev,
        currency=currency,
    )


def _info_sync(symbol: str) -> StockInfo:
    t = _ticker(symbol)
    fast = t.fast_info

    def _safe_float(key: str) -> float | None:
        try:
            v = fast[key]
            return float(v) if v is not None else None
        except (KeyError, TypeError, ValueError):
            return None

    price = _safe_float("last_price")
    prev = _safe_float("previous_close")
    if price is None or prev is None:
        raise StockError(f"No data for {symbol.upper()}")

    # yfinance's .info hits a slow Reddit-style endpoint that frequently times
    # out or returns 4xx for less-popular tickers. We treat it as best-effort:
    # log and continue with the fast_info we already have.
    name: str | None = None
    market_cap: int | None = None
    try:
        info = t.info or {}
        name = info.get("shortName") or info.get("longName")
        mc = info.get("marketCap")
        if mc:
            market_cap = int(mc)
    except Exception as e:
        log.debug("Extended .info fetch failed for %s: %s", symbol, e)

    volume = _safe_float("last_volume") or _safe_float("ten_day_average_volume")
    return StockInfo(
        ticker=symbol.upper(),
        name=name,
        price=price,
        previous_close=prev,
        day_high=_safe_float("day_high"),
        day_low=_safe_float("day_low"),
        volume=int(volume) if volume else None,
        market_cap=market_cap,
        currency=getattr(fast, "currency", None),
    )


def _history_sync(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    t = _ticker(symbol)
    df = t.history(period=period, interval=interval, auto_adjust=False)
    if df.empty:
        raise StockError(f"No history for {symbol.upper()}")
    return df


# Public async API ---------------------------------------------------------


async def get_quote(symbol: str) -> Quote:
    return await asyncio.to_thread(_quote_sync, symbol)


async def get_info(symbol: str) -> StockInfo:
    return await asyncio.to_thread(_info_sync, symbol)


async def get_history(
    symbol: str, period: str = "1y", interval: str = "1d"
) -> pd.DataFrame:
    return await asyncio.to_thread(_history_sync, symbol, period, interval)


def format_money(value: float | int | None, currency: str | None = None) -> str:
    if value is None:
        return "n/a"
    suffix = ""
    abs_v = abs(float(value))
    if abs_v >= 1_000_000_000_000:
        formatted = f"{value / 1_000_000_000_000:.2f}T"
    elif abs_v >= 1_000_000_000:
        formatted = f"{value / 1_000_000_000:.2f}B"
    elif abs_v >= 1_000_000:
        formatted = f"{value / 1_000_000:.2f}M"
    else:
        formatted = f"{value:,.2f}"
    prefix = "$" if (currency in (None, "USD")) else f"{currency} "
    return f"{prefix}{formatted}{suffix}"
