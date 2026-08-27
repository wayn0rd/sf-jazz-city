"""T6 - Cleanup routine (C21-C23), offline.

Frozen from .loopzai/spec.md section 5, Layer 1, T6.
"""
import sqlite3

import pytest

from scraper.cleanup import cleanup_entity_titles

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT,
    venue TEXT DEFAULT 'SFJAZZ Center',
    artists TEXT,
    description TEXT,
    ticket_url TEXT,
    price TEXT,
    status TEXT,
    series TEXT,
    image_url TEXT,
    scraped_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(title, date)
);
"""

TIPPLES = "Mr. Tipple's"
ENTITY_TWINNED = "Richard Howell&#8217;s Sudden Changes"
DECODED_TWIN = "Richard Howell’s Sudden Changes"
ENTITY_ORPHAN = "Nobody&#8217;s Twin Here"
DAWN_ENTITY = "Dawn &#038; Friends"


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "events.db"
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    rows = [
        (ENTITY_TWINNED, "2026-05-01", TIPPLES, "https://h/r.jpg"),
        (DECODED_TWIN, "2026-05-01", TIPPLES, None),
        (ENTITY_ORPHAN, "2026-06-02", TIPPLES, "https://h/o.jpg"),
        ("Dawn Club", "2026-05-01", "Dawn Club", "https://h/d.jpg"),
        (DAWN_ENTITY, "2026-07-03", "Dawn Club", "https://h/dc.jpg"),
        ("Plain Tipples Show", "2026-05-05", TIPPLES, "https://h/p.jpg"),
    ]
    for title, date, venue, image in rows:
        conn.execute(
            "INSERT INTO events (title, date, venue, image_url, scraped_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, date, venue, image, "2026-08-27T00:00:00"),
        )
    conn.commit()
    conn.close()
    return str(path)


def _fetch(db_path, title, date):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT title, date, venue, image_url FROM events WHERE title = ? AND date = ?",
        (title, date),
    ).fetchone()
    conn.close()
    return row


def _count(db_path):
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    conn.close()
    return n


def _snapshot(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT title, date, venue, image_url FROM events ORDER BY title, date"
    ).fetchall()
    conn.close()
    return rows


def test_t6_1_twin_gets_the_image(db_path):
    cleanup_entity_titles(db_path)
    assert _fetch(db_path, DECODED_TWIN, "2026-05-01")[3] == "https://h/r.jpg"


def test_t6_2_twinned_entity_row_deleted(db_path):
    cleanup_entity_titles(db_path)
    assert _fetch(db_path, ENTITY_TWINNED, "2026-05-01") is None


def test_t6_3_orphan_entity_row_survives(db_path):
    """C22: delete only when the decoded twin exists."""
    cleanup_entity_titles(db_path)
    row = _fetch(db_path, ENTITY_ORPHAN, "2026-06-02")
    assert row is not None
    assert row[3] == "https://h/o.jpg"


def test_t6_4_other_venues_untouched(db_path):
    """C23: touches no venue other than Mr. Tipple's."""
    before = [r for r in _snapshot(db_path) if r[2] == "Dawn Club"]
    cleanup_entity_titles(db_path)
    after = [r for r in _snapshot(db_path) if r[2] == "Dawn Club"]
    assert after == before
    assert _fetch(db_path, DAWN_ENTITY, "2026-07-03") is not None


def test_t6_4b_rows_without_entities_untouched(db_path):
    """C23: no rows without '&#' in the title are touched."""
    cleanup_entity_titles(db_path)
    row = _fetch(db_path, "Plain Tipples Show", "2026-05-05")
    assert row is not None
    assert row[3] == "https://h/p.jpg"


def test_t6_5_idempotent(db_path):
    cleanup_entity_titles(db_path)
    first = _snapshot(db_path)
    cleanup_entity_titles(db_path)
    assert _snapshot(db_path) == first


def test_t6_6_row_count_drops_by_exactly_twinned_entity_count(db_path):
    before = _count(db_path)
    cleanup_entity_titles(db_path)
    # exactly one entity row (ENTITY_TWINNED) has a decoded twin
    assert _count(db_path) == before - 1
