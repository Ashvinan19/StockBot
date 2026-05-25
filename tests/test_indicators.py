"""Unit tests for the technical-indicator math."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.indicators import analyze, ema, macd, rsi, sma


def _series(values):
    return pd.Series(values, dtype=float)


def test_sma_basic():
    s = _series([1, 2, 3, 4, 5])
    result = sma(s, window=3)
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx(3.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_ema_decays_toward_value():
    s = _series([10] * 30 + [20] * 30)
    out = ema(s, span=10)
    assert out.iloc[0] == pytest.approx(10.0)
    assert 10 < out.iloc[35] < 20
    assert out.iloc[-1] == pytest.approx(20.0, abs=0.5)


def test_rsi_on_monotonic_up_is_overbought():
    s = _series(list(range(1, 60)))
    r = rsi(s, period=14)
    assert r.iloc[-1] > 90


def test_rsi_on_monotonic_down_is_oversold():
    s = _series(list(range(60, 1, -1)))
    r = rsi(s, period=14)
    assert r.iloc[-1] < 10


def test_macd_columns():
    s = _series(np.linspace(100, 200, 200))
    df = macd(s)
    assert set(df.columns) == {"macd", "signal", "hist"}
    assert len(df) == len(s)
    assert df["hist"].iloc[-1] == pytest.approx(
        df["macd"].iloc[-1] - df["signal"].iloc[-1]
    )


def test_analyze_returns_full_snapshot():
    rng = np.random.default_rng(seed=42)
    closes = 100 + np.cumsum(rng.normal(0, 1, 300))
    df = pd.DataFrame({"Close": closes})
    a = analyze(df, "TEST")
    assert a.ticker == "TEST"
    assert a.sma_20 is not None
    assert a.sma_50 is not None
    assert a.sma_200 is not None
    assert 0 <= a.rsi_14 <= 100
    assert a.high_52w >= a.low_52w
    assert a.trend()  # non-empty
    assert a.signal() in {
        "Strong bullish momentum",
        "Mildly bullish",
        "Neutral / mixed",
        "Mildly bearish",
        "Strong bearish momentum",
    }


def test_analyze_requires_close_column():
    with pytest.raises(ValueError):
        analyze(pd.DataFrame({"Open": [1, 2, 3]}), "X")
