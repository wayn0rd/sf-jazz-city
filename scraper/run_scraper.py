#!/usr/bin/env python3
"""
SF Jazz Event Scraper - aggregates events from multiple venues.

Usage:
    python run_scraper.py                    # Scrape all venues
    python run_scraper.py --venue sfjazz     # Scrape SFJAZZ only
    python run_scraper.py --venue blackcat   # Scrape Black Cat only
    python run_scraper.py --export           # Export to JSON
    python run_scraper.py --list             # List saved events
    python run_scraper.py --search "Miles"   # Search events
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper import SFJazzScraper, BlackCatScraper, EventDatabase

VENUES = {
    "sfjazz": ("SFJAZZ Center", SFJazzScraper),
    "blackcat": ("Black Cat SF", BlackCatScraper),
}


async def scrape_venue(venue_key: str, months: int = 3) -> dict:
    """Scrape a single venue."""
    venue_name, scraper_class = VENUES[venue_key]
    print(f"\nScraping {venue_name}...")

    scraper = scraper_class(db_path="scraper/events.db")

    if venue_key == "sfjazz":
        stats = await scraper.scrape_and_save(months_ahead=months)
    else:
        stats = await scraper.scrape_and_save()

    print(f"  Found: {stats['total_scraped']} events")
    print(f"  New: {stats['inserted']}, Updated: {stats['updated']}")
    return stats


async def scrape_all(venues: list[str], months: int = 3, export: bool = False):
    """Scrape specified venues."""
    print("=" * 55)
    print("SF Jazz Event Aggregator")
    print("=" * 55)

    total_scraped = 0
    total_inserted = 0
    total_updated = 0

    for venue_key in venues:
        if venue_key not in VENUES:
            print(f"Unknown venue: {venue_key}")
            continue
        try:
            stats = await scrape_venue(venue_key, months)
            total_scraped += stats["total_scraped"]
            total_inserted += stats["inserted"]
            total_updated += stats["updated"]
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n{'=' * 55}")
    print("Summary")
    print("=" * 55)
    print(f"  Total events: {total_scraped}")
    print(f"  New events:   {total_inserted}")
    print(f"  Updated:      {total_updated}")

    if export:
        db = EventDatabase("scraper/events.db")
        count = db.export_to_json("scraper/events.json")
        print(f"  Exported:     scraper/events.json ({count} events)")


def list_events(venue_filter: str = None):
    """List all saved events, optionally filtered by venue."""
    db = EventDatabase("scraper/events.db")
    events = db.get_all_events()

    if venue_filter:
        venue_name = VENUES.get(venue_filter, (venue_filter,))[0]
        events = [e for e in events if e.venue == venue_name]

    if not events:
        print("No events found.")
        return

    # Group by venue
    by_venue = {}
    for e in events:
        by_venue.setdefault(e.venue, []).append(e)

    print(f"\n{'=' * 60}")
    print(f"Found {len(events)} events")
    print("=" * 60)

    for venue, venue_events in sorted(by_venue.items()):
        print(f"\n{venue} ({len(venue_events)} events)")
        print("-" * 40)
        for e in venue_events[:15]:  # Show first 15 per venue
            time_str = f" {e.time}" if e.time else ""
            price_str = f" ({e.price})" if e.price else ""
            status_str = f" [{e.status}]" if e.status else ""
            print(f"  {e.date}{time_str}: {e.title}{price_str}{status_str}")
        if len(venue_events) > 15:
            print(f"  ... and {len(venue_events) - 15} more")


def search_events(query: str):
    """Search events by title or artist."""
    db = EventDatabase("scraper/events.db")
    events = db.search_events(query)

    if not events:
        print(f"No events found matching '{query}'")
        return

    print(f"\nFound {len(events)} events matching '{query}':\n")
    for event in events:
        venue = f"[{event.venue}]"
        print(f"  {event.date}: {event.title} {venue}")
        if event.ticket_url:
            print(f"    -> {event.ticket_url}")


def show_stats():
    """Show database statistics by venue."""
    db = EventDatabase("scraper/events.db")
    events = db.get_all_events()

    by_venue = {}
    for e in events:
        by_venue.setdefault(e.venue, []).append(e)

    stats = db.get_stats()
    print(f"\nDatabase Statistics:")
    print(f"  Total events: {stats['total_events']}")
    print(f"  Last scraped: {stats['last_scraped']}")
    print(f"\nBy Venue:")
    for venue, venue_events in sorted(by_venue.items()):
        print(f"  {venue}: {len(venue_events)} events")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SF Jazz Event Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported venues:
  sfjazz   - SFJAZZ Center (sfjazz.org)
  blackcat - Black Cat SF (blackcatsf.turntabletickets.com)

Examples:
  python run_scraper.py                      # Scrape all venues
  python run_scraper.py --venue sfjazz       # Scrape SFJAZZ only
  python run_scraper.py --venue blackcat     # Scrape Black Cat only
  python run_scraper.py --export             # Scrape all and export JSON
  python run_scraper.py --list               # Show all events
  python run_scraper.py --list --venue blackcat  # Show Black Cat events
  python run_scraper.py --search "Coltrane"  # Search events
  python run_scraper.py --stats              # Show statistics
        """,
    )
    parser.add_argument(
        "--venue",
        type=str,
        choices=list(VENUES.keys()),
        help="Scrape specific venue only",
    )
    parser.add_argument(
        "--months", type=int, default=3, help="Months to scrape ahead (SFJAZZ only)"
    )
    parser.add_argument(
        "--export", action="store_true", help="Export to JSON after scraping"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all saved events"
    )
    parser.add_argument(
        "--search", type=str, help="Search events by title/artist"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show database statistics"
    )

    args = parser.parse_args()

    if args.list:
        list_events(args.venue)
    elif args.search:
        search_events(args.search)
    elif args.stats:
        show_stats()
    else:
        venues = [args.venue] if args.venue else list(VENUES.keys())
        asyncio.run(scrape_all(venues, months=args.months, export=args.export))
