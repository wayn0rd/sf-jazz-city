"""Database storage for scraped events."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .models import Event


class EventDatabase:
    """SQLite database for storing scraped events."""

    def __init__(self, db_path: str = "events.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_scraped_at ON events(scraped_at)
            """)
            conn.commit()

    def save_event(self, event: Event) -> bool:
        """
        Save or update an event in the database.

        Returns True if inserted, False if updated.
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO events (
                        title, date, time, venue, artists, description,
                        ticket_url, price, status, series, image_url, scraped_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.title,
                        event.date,
                        event.time,
                        event.venue,
                        json.dumps(event.artists),
                        event.description,
                        event.ticket_url,
                        event.price,
                        event.status,
                        event.series,
                        event.image_url,
                        event.scraped_at,
                    ),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                conn.execute(
                    """
                    UPDATE events SET
                        time = ?, venue = ?, artists = ?, description = ?,
                        ticket_url = ?, price = ?, status = ?, series = ?,
                        image_url = ?, scraped_at = ?, updated_at = ?
                    WHERE title = ? AND date = ?
                    """,
                    (
                        event.time,
                        event.venue,
                        json.dumps(event.artists),
                        event.description,
                        event.ticket_url,
                        event.price,
                        event.status,
                        event.series,
                        event.image_url,
                        event.scraped_at,
                        datetime.now().isoformat(),
                        event.title,
                        event.date,
                    ),
                )
                conn.commit()
                return False

    def save_events(self, events: list[Event]) -> tuple[int, int]:
        """
        Save multiple events.

        Returns tuple of (inserted_count, updated_count).
        """
        inserted = 0
        updated = 0
        for event in events:
            if self.save_event(event):
                inserted += 1
            else:
                updated += 1
        return inserted, updated

    def get_all_events(self) -> list[Event]:
        """Retrieve all events from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM events ORDER BY date")
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_upcoming_events(self, from_date: Optional[str] = None) -> list[Event]:
        """Get events from a specific date onwards."""
        if from_date is None:
            from_date = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM events WHERE date >= ? ORDER BY date", (from_date,)
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def search_events(self, query: str) -> list[Event]:
        """Search events by title or artist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE title LIKE ? OR artists LIKE ?
                ORDER BY date
                """,
                (f"%{query}%", f"%{query}%"),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        """Convert database row to Event object."""
        artists = json.loads(row["artists"]) if row["artists"] else []
        return Event(
            title=row["title"],
            date=row["date"],
            time=row["time"],
            venue=row["venue"],
            artists=artists,
            description=row["description"],
            ticket_url=row["ticket_url"],
            price=row["price"],
            status=row["status"],
            series=row["series"],
            image_url=row["image_url"],
            scraped_at=row["scraped_at"],
        )

    def export_to_json(self, filepath: str = "events.json") -> int:
        """Export all events to JSON file. Returns count of events exported."""
        events = self.get_all_events()
        with open(filepath, "w") as f:
            json.dump([e.to_dict() for e in events], f, indent=2)
        return len(events)

    def get_stats(self) -> dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            latest = conn.execute(
                "SELECT MAX(scraped_at) FROM events"
            ).fetchone()[0]
            return {
                "total_events": total,
                "last_scraped": latest,
            }
