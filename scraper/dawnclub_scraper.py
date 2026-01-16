"""Dawn Club event scraper - extracts from Squarespace static HTML."""

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from .models import Event
from .database import EventDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.dawnclub.com"
MUSIC_URL = f"{BASE_URL}/music"


class DawnClubScraper:
    """Scraper for Dawn Club events."""

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

    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse date from text like 'Friday, January 17, 2025'."""
        if not date_text:
            return None

        # Clean up the text
        date_text = date_text.strip()

        # Try parsing full date format
        formats = [
            "%A, %B %d, %Y",  # Friday, January 17, 2025
            "%B %d, %Y",      # January 17, 2025
            "%m/%d/%Y",       # 01/17/2025
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_text, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Try to extract date components manually
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }

        date_lower = date_text.lower()
        for month_name, month_num in months.items():
            if month_name in date_lower:
                # Find day number
                day_match = re.search(r'\b(\d{1,2})\b', date_text)
                year_match = re.search(r'\b(20\d{2})\b', date_text)
                if day_match:
                    day = int(day_match.group(1))
                    year = int(year_match.group(1)) if year_match else datetime.now().year
                    return f"{year}-{month_num:02d}-{day:02d}"

        return None

    def _parse_time(self, time_text: str) -> Optional[str]:
        """Parse time from text like '8:00 PM' or '8:00 PM 11:59 PM'."""
        if not time_text:
            return None

        # Extract first time (start time)
        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)', time_text, re.IGNORECASE)
        if time_match:
            return time_match.group(1).strip()

        return None

    async def scrape_events(self) -> list[Event]:
        """Scrape all events from Dawn Club."""
        events = []

        try:
            await self._init_browser()
            page = await self._context.new_page()

            logger.info(f"Navigating to {MUSIC_URL}")
            await self._retry_operation(
                page.goto, MUSIC_URL, wait_until="networkidle", timeout=30000
            )

            # Wait for content to load
            await asyncio.sleep(2)

            # Find event items - Squarespace uses various selectors
            selectors = [
                ".eventlist-event",
                ".eventlist--upcoming article",
                "[class*='eventlist'] article",
                ".summary-item",
                "article[class*='event']",
            ]

            event_elements = []
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    event_elements = elements
                    logger.info(f"Found {len(elements)} events using selector: {selector}")
                    break

            if not event_elements:
                # Fallback: look for links to event pages
                logger.warning("No event elements found with standard selectors")
                event_elements = await page.query_selector_all("a[href*='/music/']")

            for element in event_elements:
                try:
                    event = await self._parse_event_element(element)
                    if event and event.title:
                        events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing event: {e}")
                    continue

            await page.close()

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise
        finally:
            await self._close_browser()

        # Deduplicate
        unique_events = list({(e.title, e.date): e for e in events}.values())
        logger.info(f"Total unique events: {len(unique_events)}")

        return unique_events

    async def _parse_event_element(self, element) -> Optional[Event]:
        """Parse a single event element."""
        try:
            # Extract title
            title = None
            title_selectors = [
                ".eventlist-title a",
                ".eventlist-title",
                "h1 a", "h2 a", "h3 a",
                ".summary-title a",
                ".summary-title",
            ]
            for sel in title_selectors:
                title_el = await element.query_selector(sel)
                if title_el:
                    title = await title_el.inner_text()
                    if title:
                        title = title.strip()
                        break

            if not title:
                # Try getting from element text
                text = await element.inner_text()
                if text:
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    title = lines[0] if lines else None

            if not title:
                return None

            # Extract date
            date_str = None
            date_selectors = [
                ".eventlist-datetag",
                ".event-date",
                "time.event-date",
                ".summary-metadata-item--date",
                "[class*='date']",
            ]
            for sel in date_selectors:
                date_el = await element.query_selector(sel)
                if date_el:
                    date_text = await date_el.inner_text()
                    if date_text:
                        date_str = self._parse_date(date_text)
                        if date_str:
                            break

            # Try datetime attribute
            if not date_str:
                time_el = await element.query_selector("time[datetime]")
                if time_el:
                    dt_attr = await time_el.get_attribute("datetime")
                    if dt_attr:
                        date_str = dt_attr[:10]  # Get YYYY-MM-DD

            # Extract time
            time_str = None
            time_selectors = [
                ".eventlist-time",
                ".event-time",
                ".event-time-12hr",
                "[class*='time']",
            ]
            for sel in time_selectors:
                time_el = await element.query_selector(sel)
                if time_el:
                    time_text = await time_el.inner_text()
                    if time_text:
                        time_str = self._parse_time(time_text)
                        if time_str:
                            break

            # Extract URL
            ticket_url = None
            link = await element.query_selector("a[href*='/music/']")
            if link:
                href = await link.get_attribute("href")
                if href:
                    ticket_url = urljoin(BASE_URL, href)

            # Extract image
            image_url = None
            img_selectors = [
                ".eventlist-thumbnail img",
                ".summary-thumbnail img",
                "img[class*='event']",
                "img",
            ]
            for sel in img_selectors:
                img = await element.query_selector(sel)
                if img:
                    src = await img.get_attribute("src")
                    if not src:
                        src = await img.get_attribute("data-src")
                    if src:
                        image_url = urljoin(BASE_URL, src)
                        break

            # Extract description
            description = None
            desc_selectors = [
                ".eventlist-excerpt",
                ".summary-excerpt",
                ".event-description",
                "p",
            ]
            for sel in desc_selectors:
                desc_el = await element.query_selector(sel)
                if desc_el:
                    desc_text = await desc_el.inner_text()
                    if desc_text and len(desc_text) > 10:
                        description = desc_text.strip()[:500]
                        break

            return Event(
                title=title,
                date=date_str or datetime.now().strftime("%Y-%m-%d"),
                time=time_str,
                venue="Dawn Club",
                artists=[title],
                description=description,
                ticket_url=ticket_url,
                image_url=image_url,
            )

        except Exception as e:
            logger.error(f"Error parsing event element: {e}")
            return None

    async def scrape_and_save(self) -> dict:
        """Scrape events and save to database."""
        start_time = datetime.now()
        events = await self.scrape_events()

        inserted, updated = self.db.save_events(events)

        stats = {
            "venue": "Dawn Club",
            "total_scraped": len(events),
            "inserted": inserted,
            "updated": updated,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "scraped_at": start_time.isoformat(),
        }

        logger.info(f"Scraping complete: {stats}")
        return stats


async def main():
    """Run the Dawn Club scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Dawn Club events")
    parser.add_argument("--db", type=str, default="events.db", help="Database file path")
    parser.add_argument("--export", type=str, help="Export to JSON file")
    args = parser.parse_args()

    scraper = DawnClubScraper(db_path=args.db)
    stats = await scraper.scrape_and_save()

    print(f"\nDawn Club Scraping Results:")
    print(f"  Total events: {stats['total_scraped']}")
    print(f"  New: {stats['inserted']}, Updated: {stats['updated']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")

    if args.export:
        count = scraper.db.export_to_json(args.export)
        print(f"  Exported {count} events to {args.export}")


if __name__ == "__main__":
    asyncio.run(main())
