"""Integration tests against a temporary SQLite database."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio

from src.db import Database


@pytest_asyncio.fixture
async def db(tmp_path: Path) -> Database:
    d = Database(tmp_path / "test.db")
    await d.init()
    return d


@pytest.mark.asyncio
async def test_watchlist_add_dedup_remove(db: Database):
    assert await db.add_watch(1, "AAPL") is True
    assert await db.add_watch(1, "aapl") is False  # case-insensitive dedup
    assert await db.list_watch(1) == ["AAPL"]
    assert await db.remove_watch(1, "AAPL") is True
    assert await db.remove_watch(1, "AAPL") is False
    assert await db.list_watch(1) == []


@pytest.mark.asyncio
async def test_watchlist_isolated_by_user(db: Database):
    await db.add_watch(1, "AAPL")
    await db.add_watch(2, "TSLA")
    assert await db.list_watch(1) == ["AAPL"]
    assert await db.list_watch(2) == ["TSLA"]


@pytest.mark.asyncio
async def test_alerts_crud_and_trigger(db: Database):
    aid = await db.add_alert(7, 100, "AAPL", "above", 200.0)
    assert aid > 0

    active = await db.active_alerts()
    assert len(active) == 1
    assert active[0]["ticker"] == "AAPL"

    await db.mark_triggered([aid])
    assert await db.active_alerts() == []

    listed = await db.list_alerts(7)
    assert listed[0]["triggered"] == 1


@pytest.mark.asyncio
async def test_remove_alert_only_owner(db: Database):
    aid = await db.add_alert(7, 100, "AAPL", "below", 50.0)
    assert await db.remove_alert(8, aid) is False  # different user
    assert await db.remove_alert(7, aid) is True


@pytest.mark.asyncio
async def test_alert_direction_validation(db: Database):
    with pytest.raises(ValueError):
        await db.add_alert(1, 1, "AAPL", "sideways", 100.0)
