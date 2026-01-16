"""Keys Jazz Bistro event scraper - extracts from WordPress static HTML."""

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

BASE_URL = "https://keysjazzbistro.com"
SHOWS_URL = f"{BASE_URL}/upcoming-shows/"


class KeysJazzScraper:
    """Scraper for Keys Jazz Bistro events."""

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
        # Use default context - custom user agents get blocked by this site
        self._context = await self._browser.new_context()
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

    def _parse_date_time(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse date and time from text like:
        'Friday, January 17th @ 7:00pm' or 'Jan 17, 2025 7:00 PM'
        """
        if not text:
            return None, None

        text = text.strip()

        # Extract time first
        time_match = re.search(r'@?\s*(\d{1,2}:\d{2}\s*(?:am|pm)?)', text, re.IGNORECASE)
        time_str = time_match.group(1).strip() if time_match else None
        if time_str:
            time_str = time_str.upper().replace(" ", "")
            # Format nicely
            time_str = re.sub(r'(\d+:\d+)(AM|PM)', r'\1 \2', time_str)

        # Parse date
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }

        text_lower = text.lower()
        date_str = None

        for month_name, month_num in months.items():
            if month_name in text_lower:
                # Find day number (handle 1st, 2nd, 3rd, 4th, etc.)
                day_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?', text)
                if day_match:
                    day = int(day_match.group(1))
                    # Find year or use current/next year
                    year_match = re.search(r'\b(20\d{2})\b', text)
                    if year_match:
                        year = int(year_match.group(1))
                    else:
                        year = datetime.now().year
                        # If date is in the past, assume next year
                        try:
                            test_date = datetime(year, month_num, day)
                            if test_date < datetime.now():
                                year += 1
                        except ValueError:
                            pass

                    try:
                        date_str = f"{year}-{month_num:02d}-{day:02d}"
                    except:
                        pass
                break

        return date_str, time_str

    async def scrape_events(self) -> list[Event]:
        """Scrape all events from Keys Jazz Bistro."""
        events = []

        try:
            await self._init_browser()
            page = await self._context.new_page()

            logger.info(f"Navigating to {SHOWS_URL}")
            await self._retry_operation(
                page.goto, SHOWS_URL, wait_until="networkidle", timeout=30000
            )

            await asyncio.sleep(2)

            # WordPress block template - find event posts
            selectors = [
                ".wp-block-post",
                ".wp-block-post-template > li",
                ".wp-block-query li",
                "article.post",
                "li.wp-block-post",
            ]

            event_elements = []
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    event_elements = elements
                    logger.info(f"Found {len(elements)} events using selector: {selector}")
                    break

            if not event_elements:
                # Fallback: find by heading links
                logger.warning("No event containers found, trying heading extraction")
                headings = await page.query_selector_all("h2 a[href*='upcoming-shows'], h2 a[href*='event']")
                for h in headings:
                    parent = await h.evaluate_handle("el => el.closest('li') || el.parentElement.parentElement")
                    if parent:
                        event_elements.append(parent)

            for element in event_elements:
                try:
                    parsed_events = await self._parse_event_element(element)
                    events.extend(parsed_events)
                except Exception as e:
                    logger.error(f"Error parsing event: {e}")
                    continue

            await page.close()

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise
        finally:
            await self._close_browser()

        # Deduplicate by title + date + time
        unique_events = list({(e.title, e.date, e.time): e for e in events}.values())
        logger.info(f"Total unique events: {len(unique_events)}")

        return unique_events

    async def _parse_event_element(self, element) -> list[Event]:
        """
        Parse event element - may return multiple events if multiple showtimes.
        """
        events = []

        try:
            # Extract title
            title = None
            title_selectors = [
                "h2.wp-block-post-title a",
                "h2.wp-block-post-title",
                ".wp-block-post-title a",
                "h2 a",
                "h2",
            ]
            for sel in title_selectors:
                title_el = await element.query_selector(sel)
                if title_el:
                    title = await title_el.inner_text()
                    if title:
                        title = title.strip()
                        # Skip non-event titles
                        if title.lower() in ["tickets", "get tickets", "upcoming shows", "previous shows"]:
                            title = None
                            continue
                        break

            if not title:
                return events

            # Extract event URL
            event_url = None
            link = await element.query_selector("h2 a, a[href*='upcoming-shows']")
            if link:
                href = await link.get_attribute("href")
                if href:
                    event_url = urljoin(BASE_URL, href)

            # Extract image
            image_url = None
            img = await element.query_selector("img")
            if img:
                src = await img.get_attribute("src")
                if src:
                    image_url = urljoin(BASE_URL, src)

            # Extract description
            description = None
            desc_el = await element.query_selector("p")
            if desc_el:
                desc_text = await desc_el.inner_text()
                if desc_text and len(desc_text) > 20:
                    description = desc_text.strip()[:500]

            # Get full text to find dates and times
            full_text = await element.inner_text()
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]

            # Look for date/time patterns in the text
            found_showtimes = []
            for line in lines:
                # Skip common non-date lines
                if any(skip in line.lower() for skip in ['seating', 'policy', 'ticket', 'get tickets', '$']):
                    continue

                # Check if line contains date info
                if re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', line.lower()):
                    date_str, time_str = self._parse_date_time(line)
                    if date_str:
                        found_showtimes.append((date_str, time_str))

            # Also look for ticket buttons with times
            ticket_buttons = await element.query_selector_all("a.wp-block-button__link, a[href*='add-to-cart']")
            for btn in ticket_buttons:
                btn_text = await btn.inner_text()
                if btn_text and re.search(r'\d{1,2}:\d{2}', btn_text):
                    # Try to extract date context from nearby text
                    parent = await btn.evaluate_handle("el => el.closest('div')")
                    if parent:
                        parent_text = await parent.evaluate("el => el.innerText")
                        date_str, time_str = self._parse_date_time(parent_text)
                        if not time_str:
                            time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm)?)', btn_text, re.IGNORECASE)
                            if time_match:
                                time_str = time_match.group(1).upper()
                        if date_str and (date_str, time_str) not in found_showtimes:
                            found_showtimes.append((date_str, time_str))

            # Extract price from text
            price = None
            price_match = re.search(r'\$(\d+(?:\.\d{2})?)', full_text)
            if price_match:
                price = f"${price_match.group(1)}"

            # Create events for each showtime, or one event if no specific times found
            if found_showtimes:
                for date_str, time_str in found_showtimes:
                    events.append(Event(
                        title=title,
                        date=date_str,
                        time=time_str,
                        venue="Keys Jazz Bistro",
                        artists=[title],
                        description=description,
                        ticket_url=event_url,
                        price=price,
                        image_url=image_url,
                    ))
            else:
                # No specific showtimes found - create single event
                events.append(Event(
                    title=title,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    time=None,
                    venue="Keys Jazz Bistro",
                    artists=[title],
                    description=description,
                    ticket_url=event_url,
                    price=price,
                    image_url=image_url,
                ))

        except Exception as e:
            logger.error(f"Error parsing event element: {e}")

        return events

    async def scrape_and_save(self) -> dict:
        """Scrape events and save to database."""
        start_time = datetime.now()
        events = await self.scrape_events()

        inserted, updated = self.db.save_events(events)

        stats = {
            "venue": "Keys Jazz Bistro",
            "total_scraped": len(events),
            "inserted": inserted,
            "updated": updated,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "scraped_at": start_time.isoformat(),
        }

        logger.info(f"Scraping complete: {stats}")
        return stats


async def main():
    """Run the Keys Jazz Bistro scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Keys Jazz Bistro events")
    parser.add_argument("--db", type=str, default="events.db", help="Database file path")
    parser.add_argument("--export", type=str, help="Export to JSON file")
    args = parser.parse_args()

    scraper = KeysJazzScraper(db_path=args.db)
    stats = await scraper.scrape_and_save()

    print(f"\nKeys Jazz Bistro Scraping Results:")
    print(f"  Total events: {stats['total_scraped']}")
    print(f"  New: {stats['inserted']}, Updated: {stats['updated']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")

    if args.export:
        count = scraper.db.export_to_json(args.export)
        print(f"  Exported {count} events to {args.export}")


if __name__ == "__main__":
    asyncio.run(main())
