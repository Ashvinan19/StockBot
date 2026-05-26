"""Technical indicators calculated from stock price data.

Each function expects a pandas DataFrame with a 'Close' column and returns
indicator values using only pandas and numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window=window, min_periods=window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Classic Wilder RSI.

    Edge cases:
    - all gains, no losses → 100
    - all losses, no gains → 0
    - no movement at all   → 50
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    out = pd.Series(np.nan, index=close.index)
    both_zero = (avg_gain == 0) & (avg_loss == 0)
    only_gains = (avg_loss == 0) & (avg_gain > 0)
    only_losses = (avg_gain == 0) & (avg_loss > 0)
    normal = ~(both_zero | only_gains | only_losses) & avg_gain.notna() & avg_loss.notna()

    rs = avg_gain[normal] / avg_loss[normal]
    out[normal] = 100 - (100 / (1 + rs))
    out[only_gains] = 100.0
    out[only_losses] = 0.0
    out[both_zero] = 50.0
    return out.fillna(50.0)


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "hist": hist}
    )


@dataclass
class Analysis:
    """Summary of the most recent indicator values for a ticker."""

    ticker: str
    last_close: float
    sma_20: float | None
    sma_50: float | None
    sma_200: float | None
    rsi_14: float
    macd: float
    macd_signal: float
    macd_hist: float
    high_52w: float
    low_52w: float

    def trend(self) -> str:
        """ summary of the indicators"""
        parts: list[str] = []
        if self.sma_50 is not None:
            if self.last_close > self.sma_50:
                parts.append("price above 50-day SMA")
            else:
                parts.append("price below 50-day SMA")
        if self.sma_200 is not None:
            if self.last_close > self.sma_200:
                parts.append("above 200-day SMA")
            else:
                parts.append("below 200-day SMA")

        if self.rsi_14 >= 70:
            parts.append(f"RSI {self.rsi_14:.0f} (overbought)")
        elif self.rsi_14 <= 30:
            parts.append(f"RSI {self.rsi_14:.0f} (oversold)")
        else:
            parts.append(f"RSI {self.rsi_14:.0f} (neutral)")

        if self.macd_hist > 0:
            parts.append("MACD bullish")
        elif self.macd_hist < 0:
            parts.append("MACD bearish")

        return "; ".join(parts)

    def signal(self) -> str:
        """Bucket the indicators into a coarse momentum label."""
        score = 0
        if self.sma_50 is not None and self.last_close > self.sma_50:
            score += 1
        if self.sma_200 is not None and self.last_close > self.sma_200:
            score += 1
        if self.rsi_14 > 55:
            score += 1
        elif self.rsi_14 < 45:
            score -= 1
        if self.macd_hist > 0:
            score += 1
        else:
            score -= 1

        if score >= 3:
            return "Strong bullish momentum"
        if score >= 1:
            return "Mildly bullish"
        if score <= -3:
            return "Strong bearish momentum"
        if score <= -1:
            return "Mildly bearish"
        return "Neutral / mixed"


def analyze(df: pd.DataFrame, ticker: str) -> Analysis:
    """Compute all indicators and return the latest snapshot."""
    if "Close" not in df.columns:
        raise ValueError("DataFrame must have a 'Close' column")
    close = df["Close"].dropna()
    if close.empty:
        raise ValueError("No close prices available")

    sma20 = sma(close, 20).iloc[-1]
    sma50 = sma(close, 50).iloc[-1]
    sma200 = sma(close, 200).iloc[-1]
    rsi_series = rsi(close, 14)
    macd_df = macd(close)

    last_close = float(close.iloc[-1])
    window_52w = close.iloc[-252:] if len(close) >= 252 else close

    def f(v):
        return None if pd.isna(v) else float(v)

    return Analysis(
        ticker=ticker.upper(),
        last_close=last_close,
        sma_20=f(sma20),
        sma_50=f(sma50),
        sma_200=f(sma200),
        rsi_14=float(rsi_series.iloc[-1]),
        macd=float(macd_df["macd"].iloc[-1]),
        macd_signal=float(macd_df["signal"].iloc[-1]),
        macd_hist=float(macd_df["hist"].iloc[-1]),
        high_52w=float(window_52w.max()),
        low_52w=float(window_52w.min()),
    )
