# StockBot

A Discord bot for live stock data, up to date accurate watchlists  aswell as threshold prices, alerts, technical-indicator analysis, and a summary of the stock and where it stands.

![StockBot demo](stockbotdemo.gif)

## Features

| Command (stock can be changed) | Description |
|---|---|
| `$help` | Lists every command |
| `$price AAPL` | Current price, change, % change |
| `$info TSLA` | Price, day range, volume, market cap |
| `$watch add\|remove\|list` | Persistent per user watchlists (SQLite) |
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
cd StockBot

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

**Entry point**
- `bot.py` — what you actually run; loads config and starts the bot

**Core (`src/`)**
- `bot.py` — the bot itself (a typed subclass of discord.py's `commands.Bot`)
- `config.py` — reads your `.env` file into a `Config` object
- `db.py` — all SQLite reads/writes for watchlists and alerts
- `stocks.py` — fetches live prices and history from yfinance
- `indicators.py` — math for RSI, MACD, moving averages, 52-week range
- `ai.py` — talks to Gemini for the `$summary` command

**Commands (`src/cogs/`)** — one file per command group
- `general.py` → `$hello`, `$ping`, `$help`
- `stocks_cog.py` → `$price`, `$info`
- `watchlist.py` → `$watch add/remove/list`
- `alerts.py` → `$alert ...` plus the background price checker
- `analysis.py` → `$analyze`, `$signal`
- `summary.py` → `$summary`

**Tests (`tests/`)**
- `test_indicators.py` — checks the math (RSI on monotonic series, MACD shape, etc.)
- `test_db.py` — checks the SQLite layer with an in-memory DB

**Project meta**
- `Dockerfile`, `requirements.txt`, `pyproject.toml`, `.github/workflows/ci.yml`

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

### Render (Render is paid to host the bot)

1. Push this repo to GitHub.
2. On Render, **New → Background Worker** (not Web Service — there's no HTTP).
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `python bot.py`
5. Add `DISCORD_TOKEN` and `GOOGLE_API_KEY` as environment variables.
6. Add a persistent disk mounted at `/app/data` so watchlists and alerts
   survive redeploys.


## License

MIT — see `LICENSE`.
