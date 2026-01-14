"""Black Cat SF event scraper - extracts from embedded JSON data."""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from .models import Event
from .database import EventDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://blackcatsf.turntabletickets.com"


class BlackCatScraper:
    """Scraper for Black Cat SF jazz club events."""

    def __init__(
        self,
        db_path: str = "events.db",
        headless: bool = True,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.db = EventDatabase(db_path)
        self.headless = headless
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._browser = None
        self._context = None

    async def _init_browser(self):
        """Initialize Playwright browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        logger.info("Browser initialized")

    async def _close_browser(self):
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    async def _retry_operation(self, operation, *args, **kwargs):
        """Execute operation with retry logic."""
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except (PlaywrightTimeout, Exception) as e:
                last_error = e
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed: {str(e)}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
        raise last_error

    async def _extract_preload_data(self, page) -> Optional[dict]:
        """Extract the __tt_preload JSON data from the page."""
        try:
            data = await page.evaluate("""() => {
                if (window.__tt_preload) {
                    return window.__tt_preload;
                }
                return null;
            }""")
            return data
        except Exception as e:
            logger.error(f"Error extracting preload data: {e}")
            return None

    def _parse_performance(self, perf: dict) -> Optional[Event]:
        """Parse a single performance object into an Event."""
        try:
            # Show details are nested in 'show' object
            show = perf.get("show", {})

            # Extract datetime from performance level
            dt_str = perf.get("datetime", "")
            pacific = ZoneInfo("America/Los_Angeles")
            if dt_str:
                # Parse ISO format datetime (UTC) and convert to Pacific
                dt_utc = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                dt_local = dt_utc.astimezone(pacific)
                date_str = dt_local.strftime("%Y-%m-%d")
                time_str = dt_local.strftime("%-I:%M %p")
            else:
                # Fallback to date/time strings
                date_str = perf.get("date", datetime.now().strftime("%Y-%m-%d"))
                time_str = perf.get("time")

            # Extract title/artist from show object
            title = show.get("name", "")
            if not title:
                return None

            # Extract description from show object
            description = show.get("description", "")
            if description:
                # Clean up HTML if present
                description = description.replace("<br>", "\n").replace("<br/>", "\n")
                # Truncate long descriptions
                if len(description) > 500:
                    description = description[:497] + "..."

            # Extract price range from show object
            prices = show.get("price_per_person", [])
            if prices:
                if len(prices) == 1:
                    price_str = f"${prices[0]}"
                elif len(prices) >= 2:
                    price_str = f"${prices[0]} - ${prices[-1]}"
                else:
                    price_str = None
            else:
                price_str = None

            # Build ticket URL
            show_id = perf.get("show_id") or show.get("id", "")
            ticket_url = f"{BASE_URL}/shows/{show_id}/?date={date_str}" if show_id else None

            # Extract image from show object's srcset
            srcset = show.get("srcset", {})
            image_url = show.get("image")  # Fallback to direct image
            if srcset:
                # Try to get a medium-sized image
                for size in ["rectSm", "sqSm", "sqLg", "original"]:
                    if size in srcset and srcset[size]:
                        img_data = srcset[size]
                        if isinstance(img_data, dict) and img_data.get("src"):
                            image_url = img_data["src"]
                            break

            # Extract status
            status = None
            if perf.get("sold_out"):
                status = "Sold Out"
            elif perf.get("few_remaining"):
                status = "Few Tickets Left"

            return Event(
                title=title,
                date=date_str,
                time=time_str,
                venue="Black Cat SF",
                artists=[title],
                description=description if description else None,
                ticket_url=ticket_url,
                price=price_str,
                status=status,
                series=perf.get("category"),
                image_url=image_url,
            )

        except Exception as e:
            logger.error(f"Error parsing performance: {e}")
            return None

    async def scrape_events(self) -> list[Event]:
        """Scrape all events from Black Cat SF."""
        events = []

        try:
            await self._init_browser()
            page = await self._context.new_page()

            logger.info(f"Navigating to {BASE_URL}")
            await self._retry_operation(
                page.goto, BASE_URL, wait_until="networkidle", timeout=30000
            )

            # Wait for JS to load
            await asyncio.sleep(2)

            # Extract preloaded data
            preload_data = await self._extract_preload_data(page)

            if not preload_data:
                logger.error("Could not extract preload data")
                return events

            # Get performances from pagination data
            pagination = preload_data.get("pagination", {})
            performances = pagination.get("performances", [])

            if not performances:
                # Try alternate location
                performances = preload_data.get("performances", [])

            logger.info(f"Found {len(performances)} performances in preload data")

            for perf in performances:
                event = self._parse_performance(perf)
                if event:
                    events.append(event)

            await page.close()

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise
        finally:
            await self._close_browser()

        # Deduplicate by title and date
        unique_events = list({(e.title, e.date): e for e in events}.values())
        logger.info(f"Total unique events: {len(unique_events)}")

        return unique_events

    async def scrape_and_save(self) -> dict:
        """Scrape events and save to database."""
        start_time = datetime.now()
        events = await self.scrape_events()

        inserted, updated = self.db.save_events(events)

        stats = {
            "venue": "Black Cat SF",
            "total_scraped": len(events),
            "inserted": inserted,
            "updated": updated,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "scraped_at": start_time.isoformat(),
        }

        logger.info(f"Scraping complete: {stats}")
        return stats


async def main():
    """Run the Black Cat scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Black Cat SF events")
    parser.add_argument(
        "--db", type=str, default="events.db", help="Database file path"
    )
    parser.add_argument(
        "--export", type=str, help="Export to JSON file after scraping"
    )
    args = parser.parse_args()

    scraper = BlackCatScraper(db_path=args.db)
    stats = await scraper.scrape_and_save()

    print(f"\nBlack Cat SF Scraping Results:")
    print(f"  Total events: {stats['total_scraped']}")
    print(f"  New events: {stats['inserted']}")
    print(f"  Updated: {stats['updated']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")

    if args.export:
        count = scraper.db.export_to_json(args.export)
        print(f"  Exported {count} events to {args.export}")


if __name__ == "__main__":
    asyncio.run(main())
