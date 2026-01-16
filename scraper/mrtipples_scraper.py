"""Mr. Tipple's Recording Studio event scraper - extracts from The Events Calendar plugin."""

import asyncio
import logging
import re
import json
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

BASE_URL = "https://mrtipplessf.com"
CALENDAR_URL = f"{BASE_URL}/calendar/"


class MrTipplesScraper:
    """Scraper for Mr. Tipple's Recording Studio events."""

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

    async def _init_browser(self):
        """Initialize Playwright browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context()
        logger.info("Browser initialized")

    async def _close_browser(self):
        """Close browser and cleanup."""
        if hasattr(self, '_context') and self._context:
            await self._context.close()
        if hasattr(self, '_browser') and self._browser:
            await self._browser.close()
        if hasattr(self, '_playwright') and self._playwright:
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

    async def _extract_schema_events(self, page) -> list[dict]:
        """Extract events from Schema.org JSON-LD markup."""
        events = []
        try:
            # Find all JSON-LD script tags
            scripts = await page.query_selector_all('script[type="application/ld+json"]')
            for script in scripts:
                content = await script.inner_text()
                try:
                    data = json.loads(content)
                    # Handle both single events and arrays
                    if isinstance(data, list):
                        for item in data:
                            if item.get("@type") == "Event":
                                events.append(item)
                    elif data.get("@type") == "Event":
                        events.append(data)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.debug(f"Error extracting schema events: {e}")
        return events

    def _parse_schema_event(self, data: dict) -> Optional[Event]:
        """Parse a Schema.org Event object into our Event model."""
        try:
            title = data.get("name", "")
            if not title:
                return None

            # Parse date/time
            start_date = data.get("startDate", "")
            date_str = None
            time_str = None
            if start_date:
                try:
                    # Handle ISO format: 2026-01-02T18:15:00-08:00
                    dt = datetime.fromisoformat(start_date)
                    date_str = dt.strftime("%Y-%m-%d")
                    time_str = dt.strftime("%-I:%M %p")
                except:
                    pass

            # Parse price
            price = None
            offers = data.get("offers", {})
            if isinstance(offers, dict):
                price_val = offers.get("price", "")
                if price_val:
                    price = f"${price_val}" if not str(price_val).startswith("$") else str(price_val)
            elif isinstance(offers, list) and offers:
                prices = [o.get("price", "") for o in offers if o.get("price")]
                if prices:
                    price = f"${min(prices)} - ${max(prices)}" if len(prices) > 1 else f"${prices[0]}"

            # Get URL
            ticket_url = data.get("url", "")

            # Get image
            image_url = None
            image = data.get("image", "")
            if isinstance(image, str):
                image_url = image
            elif isinstance(image, list) and image:
                image_url = image[0]
            elif isinstance(image, dict):
                image_url = image.get("url", "")

            # Get description
            description = data.get("description", "")
            if description and len(description) > 500:
                description = description[:497] + "..."

            return Event(
                title=title,
                date=date_str or datetime.now().strftime("%Y-%m-%d"),
                time=time_str,
                venue="Mr. Tipple's",
                artists=[title],
                description=description if description else None,
                ticket_url=ticket_url,
                price=price,
                image_url=image_url,
            )
        except Exception as e:
            logger.error(f"Error parsing schema event: {e}")
            return None

    async def _extract_calendar_events(self, page) -> list[Event]:
        """Extract events from the calendar view HTML."""
        events = []

        # Try different selectors for The Events Calendar plugin
        selectors = [
            ".tribe-events-calendar-list__event",
            ".tribe-common-g-row",
            ".tribe-events-pro-photo__event",
            "article.tribe-events-pro-photo__event",
            ".type-tribe_events",
            "[class*='tribe-events'] article",
        ]

        event_elements = []
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                event_elements = elements
                logger.info(f"Found {len(elements)} calendar events using: {selector}")
                break

        for el in event_elements:
            try:
                event = await self._parse_calendar_element(el)
                if event:
                    events.append(event)
            except Exception as e:
                logger.debug(f"Error parsing calendar element: {e}")

        return events

    async def _parse_calendar_element(self, element) -> Optional[Event]:
        """Parse an event element from the calendar HTML."""
        try:
            # Extract title
            title = None
            title_selectors = [
                ".tribe-events-calendar-list__event-title a",
                ".tribe-events-pro-photo__event-title a",
                "h3 a", "h2 a",
                ".tribe-events-title a",
                "a.tribe-event-url",
            ]
            for sel in title_selectors:
                title_el = await element.query_selector(sel)
                if title_el:
                    title = await title_el.inner_text()
                    if title:
                        title = title.strip()
                        break

            if not title:
                return None

            # Extract URL
            ticket_url = None
            link = await element.query_selector("a[href*='event']")
            if link:
                href = await link.get_attribute("href")
                if href:
                    ticket_url = urljoin(BASE_URL, href)

            # Extract date/time
            date_str = None
            time_str = None
            datetime_el = await element.query_selector("time[datetime], [datetime]")
            if datetime_el:
                dt_attr = await datetime_el.get_attribute("datetime")
                if dt_attr:
                    try:
                        dt = datetime.fromisoformat(dt_attr)
                        date_str = dt.strftime("%Y-%m-%d")
                        time_str = dt.strftime("%-I:%M %p")
                    except:
                        pass

            # Fallback: extract from text
            if not date_str:
                text = await element.inner_text()
                # Look for date patterns
                date_match = re.search(
                    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})',
                    text, re.IGNORECASE
                )
                if date_match:
                    months = {
                        "january": 1, "february": 2, "march": 3, "april": 4,
                        "may": 5, "june": 6, "july": 7, "august": 8,
                        "september": 9, "october": 10, "november": 11, "december": 12
                    }
                    month = months.get(date_match.group(1).lower(), 1)
                    day = int(date_match.group(2))
                    year = datetime.now().year
                    date_str = f"{year}-{month:02d}-{day:02d}"

            # Extract price
            price = None
            price_el = await element.query_selector(".tribe-events-c-small-cta__price, [class*='price']")
            if price_el:
                price_text = await price_el.inner_text()
                if price_text:
                    price = price_text.strip()

            # Extract image
            image_url = None
            img = await element.query_selector("img")
            if img:
                src = await img.get_attribute("src")
                if src:
                    image_url = urljoin(BASE_URL, src)

            return Event(
                title=title,
                date=date_str or datetime.now().strftime("%Y-%m-%d"),
                time=time_str,
                venue="Mr. Tipple's",
                artists=[title],
                ticket_url=ticket_url,
                price=price,
                image_url=image_url,
            )
        except Exception as e:
            logger.debug(f"Error parsing element: {e}")
            return None

    async def scrape_events(self) -> list[Event]:
        """Scrape all events from Mr. Tipple's."""
        events = []

        try:
            await self._init_browser()
            page = await self._context.new_page()

            logger.info(f"Navigating to {CALENDAR_URL}")
            await self._retry_operation(
                page.goto, CALENDAR_URL, wait_until="networkidle", timeout=30000
            )
            await asyncio.sleep(2)

            # First try to extract from Schema.org JSON-LD
            schema_events = await self._extract_schema_events(page)
            if schema_events:
                logger.info(f"Found {len(schema_events)} events in Schema.org data")
                for data in schema_events:
                    event = self._parse_schema_event(data)
                    if event:
                        events.append(event)

            # Also extract from calendar HTML as backup/supplement
            calendar_events = await self._extract_calendar_events(page)
            events.extend(calendar_events)

            await page.close()

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise
        finally:
            await self._close_browser()

        # Deduplicate by title + date
        unique_events = list({(e.title, e.date): e for e in events}.values())
        logger.info(f"Total unique events: {len(unique_events)}")

        return unique_events

    async def scrape_and_save(self) -> dict:
        """Scrape events and save to database."""
        start_time = datetime.now()
        events = await self.scrape_events()

        inserted, updated = self.db.save_events(events)

        stats = {
            "venue": "Mr. Tipple's",
            "total_scraped": len(events),
            "inserted": inserted,
            "updated": updated,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "scraped_at": start_time.isoformat(),
        }

        logger.info(f"Scraping complete: {stats}")
        return stats


async def main():
    """Run the Mr. Tipple's scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Mr. Tipple's events")
    parser.add_argument("--db", type=str, default="events.db", help="Database file path")
    parser.add_argument("--export", type=str, help="Export to JSON file")
    args = parser.parse_args()

    scraper = MrTipplesScraper(db_path=args.db)
    stats = await scraper.scrape_and_save()

    print(f"\nMr. Tipple's Scraping Results:")
    print(f"  Total events: {stats['total_scraped']}")
    print(f"  New: {stats['inserted']}, Updated: {stats['updated']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")

    if args.export:
        count = scraper.db.export_to_json(args.export)
        print(f"  Exported {count} events to {args.export}")


if __name__ == "__main__":
    asyncio.run(main())
