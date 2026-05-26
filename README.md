# StockBot

A Discord bot for live stock data, persistent watchlists, threshold price
alerts, technical-indicator analysis, and AI-generated commentary.

[![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![discord.py](https://img.shields.io/badge/discord.py-2.7-5865F2)
![SQLite](https://img.shields.io/badge/storage-SQLite-003B57)
![License](https://img.shields.io/badge/license-MIT-green)

> **Analysis only. This bot does not give financial advice.**

## Features

| Command | Description |
|---|---|
| `$help` | Lists every command |
| `$price AAPL` | Current price, change, % change |
| `$info TSLA` | Price, day range, volume, market cap |
| `$watch add\|remove\|list` | Persistent per-user watchlists (SQLite) |
| `$alert AAPL above 200` | Background task fires when triggered |
| `$alerts` / `$alert remove <id>` | Manage active alerts |
| `$analyze AAPL` | SMA(20/50/200), RSI, MACD, 52-week range |
| `$signal NVDA` | One-line momentum bucket |
| `$summary AAPL` | Gemini-written analysis (optional) |

## Tech stack

- **Python 3.11+** with `asyncio`
- **discord.py** for the gateway connection and command framework
- **yfinance + pandas + numpy** for market data and indicator math (RSI / MACD / SMA / EMA)
- **aiosqlite** for async persistence of watchlists and alerts
- **Google Gemini** (`gemini-2.5-flash`) for the optional `$summary` command
- **pytest + pytest-asyncio** for unit / integration tests
- **GitHub Actions** for CI (lint + tests on Python 3.11 and 3.12)
- **Docker** for reproducible deployment

## Quick start

```bash
git clone https://github.com/Ashvinan19/StockBot.git
cd YOUR_REPO

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and paste in your DISCORD_TOKEN (and optionally GOOGLE_API_KEY)

python bot.py
```

Expected startup:

```
INFO stockbot: Loaded cog: src.cogs.general
... (six cogs) ...
INFO stockbot: Logged on as YourBot#0000 (id=...)
INFO stockbot: Prefix: '$'  |  AI provider: gemini
```

Then in any channel where the bot is present:

```
$help
$price AAPL
$watch add MSFT
$alert NVDA above 1000
$analyze TSLA
$summary AAPL
```

## Required Discord setup

1. [Discord Developer Portal](https://discord.com/developers/applications) → your app → **Bot**
2. **Reset Token**, paste the new value into `DISCORD_TOKEN` in `.env`
3. Under **Privileged Gateway Intents**, enable **MESSAGE CONTENT INTENT**
4. Invite the bot with at least: `Send Messages`, `Embed Links`, `Read Message History`

## Configuration

All configuration is environment-driven. Copy `.env.example` to `.env` and fill in:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | (required) | Bot token from the Developer Portal |
| `COMMAND_PREFIX` | `$` | Prefix for every command |
| `DATABASE_PATH` | `data/bot.db` | SQLite file (auto-created) |
| `ALERT_CHECK_INTERVAL_SECONDS` | `300` | How often the alert task polls prices |
| `GOOGLE_API_KEY` | _empty_ | Enables `$summary`. Get one at [aistudio.google.com](https://aistudio.google.com/app/apikey) |

If `GOOGLE_API_KEY` is unset, every other command still works; `$summary`
politely tells the user it's disabled.

## Project layout

```
discordbot/
├── bot.py                  # entry point: load config + start StockBot
├── src/
│   ├── bot.py              # commands.Bot subclass with typed config/db/ai
│   ├── config.py           # typed Config loaded from .env
│   ├── db.py               # aiosqlite wrapper for watchlist + alerts
│   ├── stocks.py           # yfinance wrappers (async via asyncio.to_thread)
│   ├── indicators.py       # SMA, EMA, RSI, MACD, Analysis snapshot
│   ├── ai.py               # Gemini summary client
│   └── cogs/
│       ├── general.py      # $hello, $ping, $help
│       ├── stocks_cog.py   # $price, $info
│       ├── watchlist.py    # $watch add/remove/list
│       ├── alerts.py       # $alert ... + background checker
│       ├── analysis.py     # $analyze, $signal
│       └── summary.py      # $summary (AI)
├── tests/
│   ├── test_indicators.py  # indicator math
│   └── test_db.py          # async SQLite tests
├── .github/workflows/ci.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Architecture notes

- **Subclassed `commands.Bot`** (`src/bot.py`) holds typed `config`, `db`, and
  `ai` attributes — cogs access them with full type-checking instead of duck
  typing.
- **`yfinance` is synchronous**, so every public call in `src/stocks.py` is
  wrapped with `asyncio.to_thread` to avoid blocking the gateway loop.
- **Indicators are pure pandas/numpy** — no `ta-lib`, no native deps, so they
  install cleanly on every platform and are easy to unit-test.
- **Alerts persist across restarts.** Active alerts live in SQLite; the
  in-process `tasks.loop` re-loads them on startup via `setup_hook`.

## Run the tests

```bash
pip install pytest pytest-asyncio
pytest -v
```

12 tests cover indicator math (SMA, EMA, RSI, MACD, end-to-end analyze) and
the SQLite watchlist + alerts schema.

## Run in Docker

```bash
docker build -t stockbot .
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  stockbot
```

The volume keeps the SQLite database persistent across restarts.

## Deploy

### Render (recommended, free background-worker tier)

1. Push this repo to GitHub.
2. On Render, **New → Background Worker** (not Web Service — there's no HTTP).
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `python bot.py`
5. Add `DISCORD_TOKEN` and `GOOGLE_API_KEY` as environment variables.
6. Add a persistent disk mounted at `/app/data` so watchlists and alerts
   survive redeploys.

### Railway

1. **New Project → Deploy from GitHub repo**.
2. Set `DISCORD_TOKEN` and optional `GOOGLE_API_KEY`.
3. Add a volume mounted at `/app/data`.

### Fly.io

1. `fly launch` (picks up the `Dockerfile`).
2. `fly secrets set DISCORD_TOKEN=... GOOGLE_API_KEY=...`
3. `fly volumes create data --size 1` and mount it at `/app/data` in `fly.toml`.

## Notes & limitations

- `yfinance` is unofficial and occasionally rate-limited — fine for personal
  use, but don't rely on it for production trading systems.
- The alert checker runs in-process. If the bot restarts, pending alerts
  resume from the DB at the next interval.
- `$summary` uses `gemini-2.5-flash` by default; swap models in `src/ai.py`.
- Never commit your real `.env`. `.gitignore` already excludes it.

## License

MIT — see `LICENSE`.
