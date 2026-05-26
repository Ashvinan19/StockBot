"""Gemini-backed stock summaries.

Builds a structured prompt from live indicators and asks Gemini to write a
short, breakdown of the stock. The system prompt explicitly requires 'analysis'
wording.
"""

from __future__ import annotations

import asyncio
import logging

from .config import Config
from .indicators import Analysis
from .stocks import StockInfo, format_money

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a neutral stock market commentator. Given recent technical "
    "indicators for a stock, write a 2-4 sentence plain-English analysis. "
    "Describe momentum and trend, give buy/sell/hold recommendations. "
    "Use the word 'analysis', never 'advice'. Avoid hype."
)

DEFAULT_MODEL = "gemini-2.5-flash"


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
    """Gemini wrapper. Disabled  if GOOGLE_API_KEY is not set."""

    provider = "gemini"

    def __init__(self, config: Config, model: str = DEFAULT_MODEL):
        self._model = None
        if not config.google_api_key:
            log.info("GOOGLE_API_KEY not set; $summary will be disabled.")
            return
        try:
            import google.generativeai as genai

            genai.configure(api_key=config.google_api_key)
            self._model = genai.GenerativeModel(
                model, system_instruction=SYSTEM_PROMPT
            )
        except Exception as e:
            log.warning("Failed to initialize Gemini client: %s", e)
            self._model = None

    @property
    def available(self) -> bool:
        return self._model is not None

    async def summarize(self, info: StockInfo, analysis: Analysis) -> str:
        if not self.available:
            raise RuntimeError(
                "No AI provider configured. Set GOOGLE_API_KEY in your .env."
            )
        prompt = _build_prompt(info, analysis)
        return await asyncio.to_thread(self._generate, prompt)

    def _generate(self, prompt: str) -> str:
        resp = self._model.generate_content(prompt)
        text = getattr(resp, "text", "") or ""
        return text.strip() or "(no summary returned)"
