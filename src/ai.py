"""LLM-backed summaries.

Supports Google Gemini (preferred if GOOGLE_API_KEY is set) or OpenAI as a
fallback. The provider is chosen at import-time based on the env vars.

Important: prompts explicitly require neutral 'analysis' wording, not 'buy/sell'
recommendations. We don't want this bot to give direct financial advice.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from .config import Config
from .indicators import Analysis
from .stocks import StockInfo, format_money

SYSTEM_PROMPT = (
    "You are a neutral stock market commentator. Given recent technical "
    "indicators for a stock, write a 2-4 sentence plain-English analysis. "
    "Describe momentum and trend, but DO NOT give buy/sell/hold recommendations. "
    "Use the word 'analysis', never 'advice'. Avoid hype."
)


def _build_prompt(info: StockInfo, analysis: Analysis) -> str:
    return (
        f"Ticker: {analysis.ticker} ({info.name or 'n/a'})\n"
        f"Current price: {format_money(info.price, info.currency)}\n"
        f"Day change: {info.change_pct:+.2f}%\n"
        f"52-week range: {format_money(analysis.low_52w)} - {format_money(analysis.high_52w)}\n"
        f"20-day SMA: {format_money(analysis.sma_20)}\n"
        f"50-day SMA: {format_money(analysis.sma_50)}\n"
        f"200-day SMA: {format_money(analysis.sma_200)}\n"
        f"RSI(14): {analysis.rsi_14:.1f}\n"
        f"MACD histogram: {analysis.macd_hist:+.3f}\n"
        f"Indicator summary: {analysis.trend()}\n\n"
        "Write the analysis now."
    )


class AIClient:
    """Picks a provider at construction and exposes a single async method."""

    def __init__(self, config: Config):
        self.provider: Optional[str] = None
        self._gemini = None
        self._openai = None

        if config.google_api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=config.google_api_key)
                self._gemini = genai.GenerativeModel(
                    "gemini-2.5-flash",
                    system_instruction=SYSTEM_PROMPT,
                )
                self.provider = "gemini"
            except Exception:
                self._gemini = None

        if not self.provider and config.openai_api_key:
            try:
                from openai import OpenAI

                self._openai = OpenAI(api_key=config.openai_api_key)
                self.provider = "openai"
            except Exception:
                self._openai = None

    @property
    def available(self) -> bool:
        return self.provider is not None

    async def summarize(self, info: StockInfo, analysis: Analysis) -> str:
        if not self.available:
            raise RuntimeError(
                "No AI provider configured. Set GOOGLE_API_KEY or OPENAI_API_KEY."
            )
        prompt = _build_prompt(info, analysis)
        if self.provider == "gemini":
            return await asyncio.to_thread(self._gemini_call, prompt)
        return await asyncio.to_thread(self._openai_call, prompt)

    def _gemini_call(self, prompt: str) -> str:
        resp = self._gemini.generate_content(prompt)
        text = getattr(resp, "text", "") or ""
        return text.strip() or "(no summary returned)"

    def _openai_call(self, prompt: str) -> str:
        resp = self._openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=300,
        )
        return (resp.choices[0].message.content or "").strip() or "(no summary returned)"
