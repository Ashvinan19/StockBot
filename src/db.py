"""Database functions for watchlists and alerts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS watchlist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    ticker      TEXT    NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, ticker)
);

CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    channel_id  INTEGER NOT NULL,
    ticker      TEXT    NOT NULL,
    direction   TEXT    NOT NULL CHECK (direction IN ('above', 'below')),
    price       REAL    NOT NULL,
    triggered   INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(triggered);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
"""


class Database:
    """Thin async wrapper over aiosqlite for our two tables."""

    def __init__(self, path: Path):
        self.path = str(path)

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    # ----- watchlist -----

    async def add_watch(self, user_id: int, ticker: str) -> bool:
        """Returns True if added, False if it already existed."""
        async with aiosqlite.connect(self.path) as db:
            try:
                await db.execute(
                    "INSERT INTO watchlist (user_id, ticker) VALUES (?, ?)",
                    (user_id, ticker.upper()),
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def remove_watch(self, user_id: int, ticker: str) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
                (user_id, ticker.upper()),
            )
            await db.commit()
            return cur.rowcount > 0

    async def list_watch(self, user_id: int) -> list[str]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY ticker",
                (user_id,),
            )
            rows = await cur.fetchall()
            return [r[0] for r in rows]

    # ----- alerts -----

    async def add_alert(
        self,
        user_id: int,
        channel_id: int,
        ticker: str,
        direction: str,
        price: float,
    ) -> int:
        if direction not in ("above", "below"):
            raise ValueError("direction must be 'above' or 'below'")
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                """INSERT INTO alerts (user_id, channel_id, ticker, direction, price)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, channel_id, ticker.upper(), direction, float(price)),
            )
            await db.commit()
            return cur.lastrowid or 0

    async def list_alerts(self, user_id: int) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """SELECT id, ticker, direction, price, triggered, created_at
                   FROM alerts WHERE user_id = ?
                   ORDER BY triggered ASC, created_at DESC""",
                (user_id,),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def active_alerts(self) -> list[dict]:
        """All alerts that haven't fired yet (used by the background checker)."""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """SELECT id, user_id, channel_id, ticker, direction, price
                   FROM alerts WHERE triggered = 0"""
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def mark_triggered(self, alert_ids: Iterable[int]) -> None:
        ids = list(alert_ids)
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                f"UPDATE alerts SET triggered = 1 WHERE id IN ({placeholders})",
                ids,
            )
            await db.commit()

    async def remove_alert(self, user_id: int, alert_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "DELETE FROM alerts WHERE id = ? AND user_id = ?",
                (alert_id, user_id),
            )
            await db.commit()
            return cur.rowcount > 0
