"""Yoshi's Oakland event scraper - uses the JSON calendar API (no browser needed)."""

import asyncio
import logging
import re
import aiohttp
from datetime import datetime, timedelta
from typing import Optional

from .models import Event
from .database import EventDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://yoshis.com"
CALENDAR_JSON_URL = f"{BASE_URL}/events/default/calendarJson"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": f"{BASE_URL}/events/calendar",
    "X-Requested-With": "XMLHttpRequest",
}


class YoshisScraper:
    """Scraper for Yoshi's Oakland events using the JSON calendar API."""

    def __init__(self, db_path: str = "events.db", months_ahead: int = 3):
        self.db = EventDatabase(db_path)
        self.months_ahead = months_ahead

    def _parse_event(self, item: dict) -> Optional[Event]:
        """Parse a single calendar JSON item into an Event."""
        try:
            # Parse start datetime — format is "YYYY-MM-DD HH:MM:SS"
            start_str = item.get("start", "")
            if not start_str:
                return None

            dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%Y-%m-%d")
            # strftime %I gives zero-padded hour; lstrip removes it (e.g. "07:30 PM" → "7:30 PM")
            time_str = dt.strftime("%I:%M %p").lstrip("0")

            # Title field is HTML: "7:30 PM ARTIST NAME<br/><a href='...'>Buy Tickets</a>"
            raw_title = item.get("title", "")

            # Extract etix ticket URL from the embedded <a> tag before stripping HTML
            etix_match = re.search(r'href="(https://(?:www\.)?etix\.com/[^"]+)"', raw_title)
            etix_url = etix_match.group(1) if etix_match else None

            # Remove <a> elements entirely (tag + inner text) so "Buy Tickets" isn't left behind
            clean = re.sub(r"<a\b[^>]*>.*?</a>", "", raw_title, flags=re.DOTALL)
            # Strip remaining HTML tags (e.g. <br/>)
            clean = re.sub(r"<[^>]+>", "", clean).strip()
            # Remove leading time prefix (e.g. "7:30 PM " or "9:30PM ")
            clean = re.sub(r"^\d{1,2}:\d{2}\s*(?:AM|PM)\s*", "", clean, flags=re.IGNORECASE).strip()

            if not clean:
                return None

            # Prefer etix URL (direct purchase), fall back to detail page URL
            detail_url = item.get("url", "")
            if detail_url and not detail_url.startswith("http"):
                detail_url = BASE_URL + detail_url
            ticket_url = etix_url or detail_url or None

            # Status from className field
            class_name = item.get("className", "")
            status = "Sold Out" if "Sold Out" in class_name else None

            return Event(
                title=clean,
                date=date_str,
                time=time_str,
                venue="Yoshi's",
                artists=[clean],
                ticket_url=ticket_url,
                status=status,
            )

        except Exception as e:
            logger.error(f"Error parsing event item: {e}")
            return None

    async def scrape_events(self) -> list[Event]:
        """Fetch events from Yoshi's JSON calendar API."""
        now = datetime.now()
        end = now + timedelta(days=30 * self.months_ahead)

        payload = {
            "start": now.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
        }

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.post(
                CALENDAR_JSON_URL,
                data=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)

        if not data:
            logger.warning("No data returned from Yoshi's API")
            return []

        logger.info(f"Fetched {len(data)} raw events from Yoshi's API")

        events = []
        for item in data:
            event = self._parse_event(item)
            if event:
                events.append(event)

        # Deduplicate by (title, date) — same show can have two sets (e.g. 7:30 and 9:30)
        unique = list({(e.title, e.date, e.time): e for e in events}.values())
        logger.info(f"Total unique events: {len(unique)}")
        return unique

    async def scrape_and_save(self) -> dict:
        """Scrape events and save to database."""
        start_time = datetime.now()
        events = await self.scrape_events()
        inserted, updated = self.db.save_events(events)

        stats = {
            "venue": "Yoshi's",
            "total_scraped": len(events),
            "inserted": inserted,
            "updated": updated,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "scraped_at": start_time.isoformat(),
        }
        logger.info(f"Scraping complete: {stats}")
        return stats
