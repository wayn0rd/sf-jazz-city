"""One-shot, idempotent maintenance for Mr. Tipple's HTML-entity title rows.

Background (spec.md cycle 2, D-s4 / C21-C23): the Mr. Tipple's adapter used to
write JSON-LD titles verbatim, so rows like "Richard Howell&#8217;s Sudden
Changes" landed in the DB alongside their decoded DOM twin "Richard Howell's
Sudden Changes". Now that titles are html.unescape'd, the entity rows can never
be updated again and would render as permanent duplicate cards.

This routine copies each entity row's image onto its decoded twin (only when
the twin has none) and then deletes the entity row. It is lossless, bounded to
one venue, and safe to run repeatedly.
"""

import argparse
import html
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

VENUE = "Mr. Tipple's"

__all__ = ["cleanup_entity_titles", "VENUE"]


def _is_blank(value) -> bool:
    return value is None or not str(value).strip()


def cleanup_entity_titles(db_path: str = "scraper/events.db") -> dict:
    """Collapse Mr. Tipple's entity-title rows onto their decoded twins.

    For every row with venue "Mr. Tipple's" whose title contains "&#":
      - find the row whose (title, date) equals (html.unescape(title), date)
      - if no such twin exists, leave the row alone and log it (C22)
      - otherwise copy the entity row's image_url onto the twin if and only if
        the twin's image_url is null/empty, then delete the entity row

    No other venue and no row without "&#" in its title is touched (C23).
    Running it a second time is a no-op. Returns a stats dict.
    """
    stats = {
        "examined": 0,
        "images_copied": 0,
        "deleted": 0,
        "orphans": [],
        "foreign_twins": [],
    }

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT id, title, date, image_url FROM events "
            "WHERE venue = ? AND title LIKE '%&#%'",
            (VENUE,),
        ).fetchall()

        for row in rows:
            stats["examined"] += 1
            decoded = html.unescape(row["title"])
            if decoded == row["title"]:
                # "&#" present but not a decodable entity — leave it alone.
                stats["orphans"].append((row["title"], row["date"]))
                logger.warning(
                    f"Cleanup: title has no decodable entity, left in place: "
                    f"{row['title']!r} ({row['date']})"
                )
                continue

            twin = conn.execute(
                "SELECT id, venue, image_url FROM events WHERE title = ? AND date = ?",
                (decoded, row["date"]),
            ).fetchone()

            if twin is None:
                stats["orphans"].append((row["title"], row["date"]))
                logger.warning(
                    f"Cleanup: no decoded twin for {row['title']!r} "
                    f"({row['date']}) — row left in place"
                )
                continue

            if twin["venue"] != VENUE:
                # Cannot happen with today's data; refuse to touch another venue.
                stats["foreign_twins"].append((row["title"], row["date"]))
                logger.warning(
                    f"Cleanup: twin of {row['title']!r} ({row['date']}) belongs "
                    f"to {twin['venue']!r} — row left in place"
                )
                continue

            if _is_blank(twin["image_url"]) and not _is_blank(row["image_url"]):
                conn.execute(
                    "UPDATE events SET image_url = ?, updated_at = ? WHERE id = ?",
                    (row["image_url"], datetime.now().isoformat(), twin["id"]),
                )
                stats["images_copied"] += 1

            conn.execute("DELETE FROM events WHERE id = ?", (row["id"],))
            stats["deleted"] += 1

        conn.commit()

    logger.info(f"Cleanup complete: {stats}")
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(
        description="Collapse Mr. Tipple's HTML-entity title rows onto their twins"
    )
    parser.add_argument("--db", default="scraper/events.db", help="Database file path")
    args = parser.parse_args()

    stats = cleanup_entity_titles(args.db)
    print(f"Examined:      {stats['examined']}")
    print(f"Images copied: {stats['images_copied']}")
    print(f"Rows deleted:  {stats['deleted']}")
    if stats["orphans"]:
        print(f"Left in place (no twin): {len(stats['orphans'])}")
        for title, date in stats["orphans"]:
            print(f"  {date}  {title}")
    if stats["foreign_twins"]:
        print(f"Left in place (twin in another venue): {len(stats['foreign_twins'])}")


if __name__ == "__main__":
    main()
