# StockBot — Discord bot for stocks, watchlists, alerts, and AI analysis

A Discord bot that fetches live stock data, tracks watchlists, fires price
alerts, computes technical indicators, and (optionally) writes short
AI-generated analysis blurbs.

> **Analysis only. This bot does not give financial advice.**

## Features

- `$price AAPL` — current price, change, % change
- `$info TSLA` — price, day range, volume, market cap
- `$watch add|remove|list` — persistent per-user watchlists (SQLite)
- `$alert AAPL above 200` — background task fires when triggered
- `$analyze AAPL` — SMA(20/50/200), RSI, MACD, 52w range
- `$signal NVDA` — quick momentum bucket
- `$summary AAPL` — neutral AI commentary (Gemini or OpenAI)

## Quick start

```bash
git clone <your-repo-url>
cd discordbot
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and paste in your DISCORD_TOKEN

python bot.py
```

You should see:

```
INFO stockbot: Logged on as MemeBot#3995 (id=...)
INFO stockbot: Prefix: '$'  |  AI provider: gemini
```

In any channel the bot has access to:

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
2. **Reset token**, copy the new token into `DISCORD_TOKEN` in `.env`
3. Under **Privileged Gateway Intents**, enable **MESSAGE CONTENT INTENT**
4. Invite the bot to your server with at least: `Send Messages`, `Embed Links`, `Read Message History`

## Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | (required) | Bot token from Developer Portal |
| `COMMAND_PREFIX` | `$` | Prefix for every command |
| `DATABASE_PATH` | `data/bot.db` | SQLite file (auto-created) |
| `ALERT_CHECK_INTERVAL_SECONDS` | `300` | How often to poll prices for alerts |
| `GOOGLE_API_KEY` | _empty_ | Enable Gemini-powered `$summary` |
| `OPENAI_API_KEY` | _empty_ | Fallback if no Gemini key |

If neither AI key is set, every other command still works; `$summary` will
politely tell the user it's disabled.

## Project layout

```
discordbot/
├── bot.py                  # entry point
├── src/
│   ├── config.py           # loads .env into a typed Config
│   ├── db.py               # aiosqlite wrapper for watchlist + alerts
│   ├── stocks.py           # yfinance wrappers (async via to_thread)
│   ├── indicators.py       # SMA, EMA, RSI, MACD, Analysis snapshot
│   ├── ai.py               # Gemini/OpenAI summary client
│   └── cogs/
│       ├── general.py
│       ├── stocks_cog.py
│       ├── watchlist.py
│       ├── alerts.py
│       ├── analysis.py
│       └── summary.py
├── tests/
│   ├── test_indicators.py
│   └── test_db.py
├── .github/workflows/ci.yml
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

## Run the tests

```bash
pip install pytest pytest-asyncio
pytest -v
```

## Run in Docker

```bash
docker build -t stockbot .
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  stockbot
```

The `data/` volume keeps the SQLite database persistent across restarts.

## Deploy

### Render

1. Push this repo to GitHub.
2. On Render, **New → Background Worker** (not Web Service — there's no HTTP).
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Add `DISCORD_TOKEN` (and any AI keys) as Environment Variables.
6. Add a persistent disk mounted at `/app/data` so the watchlist/alerts survive restarts.

### Railway

1. **New Project → Deploy from GitHub repo**.
2. Variables: `DISCORD_TOKEN`, optional `GOOGLE_API_KEY`/`OPENAI_API_KEY`.
3. Add a volume mounted at `/app/data`.
4. Start command (auto-detected from the Dockerfile, or set manually): `python bot.py`.

### Fly.io

1. `fly launch` (pick the Dockerfile).
2. `fly secrets set DISCORD_TOKEN=...`
3. Attach a volume:
   ```bash
   fly volumes create data --size 1
   ```
   and mount it at `/app/data` in `fly.toml`.

## Notes & limitations

- `yfinance` is unofficial and occasionally rate-limited; this is fine for
  personal use but don't rely on it for production trading.
- The alert checker runs in-process. If the bot restarts, pending alerts
  resume from the DB.
- AI summaries use `gemini-1.5-flash` / `gpt-4o-mini` by default — cheap and
  fast. Swap models in `src/ai.py` if you want.
- Never commit your real `.env`. `.gitignore` already excludes it.

## License

MIT (do whatever you want, no warranty).
