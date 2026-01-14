"""SFJAZZ.org event scraper using Playwright for JavaScript rendering."""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

from .models import Event
from .database import EventDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.sfjazz.org"
CALENDAR_URL = f"{BASE_URL}/calendar/"


class SFJazzScraper:
    """Scraper for SFJAZZ.org events."""

    def __init__(
        self,
        db_path: str = "events.db",
        headless: bool = True,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        """
        Initialize the scraper.

        Args:
            db_path: Path to SQLite database file
            headless: Run browser in headless mode
            max_retries: Maximum retry attempts for failed requests
            retry_delay: Delay between retries in seconds
        """
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
            viewport={"width": 1280, "height": 720},
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
                logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed: {str(e)}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
        raise last_error

    async def _wait_for_events_loaded(self, page: Page):
        """Wait for event cards to load on the page."""
        await page.wait_for_load_state("networkidle", timeout=30000)
        # Wait longer for Angular to finish rendering
        await asyncio.sleep(3)
        # Try to wait for actual content (not Angular templates)
        try:
            await page.wait_for_function(
                """() => {
                    // Check that Angular templates have been rendered (no {{ }} visible)
                    const body = document.body.innerText;
                    const hasUnrenderedTemplates = body.includes('{{') && body.includes('}}');
                    // Look for any event-like links
                    const eventLinks = document.querySelectorAll('a[href*="/tickets/"]');
                    return !hasUnrenderedTemplates && eventLinks.length > 0;
                }""",
                timeout=10000,
            )
        except PlaywrightTimeout:
            logger.warning("Timeout waiting for Angular rendering, proceeding anyway")
        await asyncio.sleep(1)

    async def _extract_events_from_page(self, page: Page) -> list[Event]:
        """Extract event data from loaded page."""
        events = []

        # First, try to extract embedded JSON data from the page
        json_events = await self._extract_json_data(page)
        if json_events:
            logger.info(f"Extracted {len(json_events)} events from embedded JSON")
            return json_events

        # Try multiple selectors that SFJAZZ might use
        selectors = [
            ".calendar-list-item",
            ".event-card",
            ".calendar-event",
            ".show-item",
            "[class*='calendar-item']",
            "[class*='event-item']",
            ".show-card",
            "article[class*='event']",
            # SFJAZZ specific - cards with ticket links
            "div:has(a[href*='/tickets/'])",
        ]

        event_elements = []
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    # Filter out very small elements (likely not event cards)
                    valid_elements = []
                    for el in elements:
                        box = await el.bounding_box()
                        if box and box['height'] > 50:
                            valid_elements.append(el)
                    if valid_elements:
                        event_elements = valid_elements
                        logger.info(f"Found {len(valid_elements)} events using selector: {selector}")
                        break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        if not event_elements:
            # Fallback: parse ticket links directly from the page
            logger.warning("No event cards found, extracting from ticket links")
            events = await self._extract_from_ticket_links(page)
            return events

        # Titles to filter out (navigation/UI elements)
        invalid_titles = {
            "MORE INFO", "BUY TICKETS", "LEARN MORE", "SOLD OUT",
            "ABOUT", "CONTACT", "SUPPORT", "DONATE", "JOIN", "LOGIN",
            "SIGN IN", "CALENDAR", "EVENTS", "HOME", "MENU", "TICKETS",
            "SUBSCRIBE", "MEMBERSHIP", "GIFT CARDS", "SEARCH",
            "SFJAZZ CENTER", "SFJAZZ", "201 FRANKLIN ST",
        }

        for element in event_elements:
            try:
                event = await self._parse_event_element(page, element)
                if event and event.title:
                    # Clean up title - remove newlines, take first line
                    clean_title = event.title.split('\n')[0].strip()
                    event.title = clean_title
                    event.artists = [clean_title] if clean_title else []

                    # Filter invalid titles
                    if clean_title.upper() in invalid_titles:
                        continue
                    # Filter very short titles (likely UI elements)
                    if len(clean_title) < 4:
                        continue
                    # Filter titles that start with "W/" (supporting artist lines)
                    if clean_title.upper().startswith("W/"):
                        continue
                    # Filter titles that look like dates
                    if re.match(r'^(MON|TUE|WED|THU|FRI|SAT|SUN)', clean_title.upper()):
                        continue

                    events.append(event)
            except Exception as e:
                logger.error(f"Error parsing event element: {e}")
                continue

        return events

    async def _extract_json_data(self, page: Page) -> list[Event]:
        """Try to extract event data from embedded JavaScript/JSON."""
        events = []
        try:
            # Look for Angular scope data or embedded JSON
            data = await page.evaluate("""() => {
                // Try to find event data in Angular scope
                const calendarEl = document.querySelector('[ng-controller*="calendar"], [data-ng-controller*="calendar"]');
                if (calendarEl && window.angular) {
                    const scope = window.angular.element(calendarEl).scope();
                    if (scope && scope.events) {
                        return scope.events;
                    }
                }
                // Try to find data in window object
                if (window.calendarEvents) return window.calendarEvents;
                if (window.events) return window.events;
                if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.events) {
                    return window.__INITIAL_STATE__.events;
                }
                return null;
            }""")

            if data and isinstance(data, list):
                for item in data:
                    try:
                        event = Event(
                            title=item.get('name') or item.get('title', ''),
                            date=self._parse_date(item.get('date') or item.get('startDate', '')),
                            time=item.get('timeString') or item.get('time'),
                            venue=item.get('venueName', 'SFJAZZ Center'),
                            artists=[item.get('name', '')] if item.get('name') else [],
                            description=item.get('description'),
                            ticket_url=item.get('url') or item.get('ticketUrl'),
                            status=item.get('status'),
                            series=item.get('seriesName'),
                        )
                        if event.title:
                            events.append(event)
                    except Exception as e:
                        logger.debug(f"Error parsing JSON event: {e}")
        except Exception as e:
            logger.debug(f"Could not extract JSON data: {e}")

        return events

    async def _extract_from_ticket_links(self, page: Page) -> list[Event]:
        """Extract events by parsing ticket links on the page."""
        events = []
        seen_urls = set()

        # Get all ticket links
        links = await page.query_selector_all('a[href*="/tickets/events/"]')
        logger.info(f"Found {len(links)} ticket links to parse")

        for link in links:
            try:
                href = await link.get_attribute("href")
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                # Get the parent container for context
                parent = await link.evaluate_handle("el => el.closest('div') || el.parentElement")

                # Extract text content
                text = await link.inner_text()
                if not text or text.strip() in ["", "MORE INFO", "BUY TICKETS", "LEARN MORE"]:
                    # Try parent text
                    if parent:
                        text = await parent.evaluate("el => el.innerText")

                if not text:
                    continue

                lines = [l.strip() for l in text.split('\n') if l.strip()]
                lines = [l for l in lines if l not in ["MORE INFO", "BUY TICKETS", "LEARN MORE", "SOLD OUT"]]

                if not lines:
                    continue

                # Parse the text - typically format is:
                # "DAY, MON DD" or date info
                # "Event Title"
                # "Time info"
                title = None
                date_str = None
                time_str = None

                for line in lines:
                    # Check if line looks like a date
                    if re.match(r'^(MON|TUE|WED|THU|FRI|SAT|SUN)', line.upper()):
                        date_str = line
                    elif re.match(r'^\d{1,2}:\d{2}|^\d{1,2}(AM|PM)', line.upper()):
                        time_str = line
                    elif not title and len(line) > 3:
                        title = line

                if not title:
                    title = lines[0] if lines else None

                if title:
                    event = Event(
                        title=title,
                        date=self._parse_date(date_str) if date_str else datetime.now().strftime("%Y-%m-%d"),
                        time=time_str,
                        venue="SFJAZZ Center",
                        artists=[title],
                        ticket_url=urljoin(BASE_URL, href) if href else None,
                    )
                    events.append(event)

            except Exception as e:
                logger.debug(f"Error parsing link: {e}")
                continue

        return events

    async def _parse_event_element(self, page: Page, element) -> Optional[Event]:
        """Parse a single event element into an Event object."""
        try:
            # Extract title
            title = None
            title_selectors = [
                "h2", "h3", "h4",
                ".event-title", ".title",
                "[class*='title']", "[class*='name']",
            ]
            for sel in title_selectors:
                title_el = await element.query_selector(sel)
                if title_el:
                    title = await title_el.inner_text()
                    title = title.strip()
                    if title:
                        break

            if not title:
                # Try getting text from the element itself
                title = await element.inner_text()
                title = title.split("\n")[0].strip() if title else None

            if not title:
                return None

            # Extract date
            date_text = None
            date_selectors = [
                ".date", ".event-date", "[class*='date']",
                "time", "[datetime]",
            ]
            for sel in date_selectors:
                date_el = await element.query_selector(sel)
                if date_el:
                    date_text = await date_el.inner_text()
                    if not date_text:
                        date_text = await date_el.get_attribute("datetime")
                    if date_text:
                        break

            # Extract time
            time_text = None
            time_selectors = [".time", ".event-time", "[class*='time']"]
            for sel in time_selectors:
                time_el = await element.query_selector(sel)
                if time_el:
                    time_text = await time_el.inner_text()
                    if time_text:
                        break

            # Parse date - handle formats like "SAT, JAN 17" or "2025-01-17"
            parsed_date = self._parse_date(date_text) if date_text else None
            if not parsed_date:
                parsed_date = datetime.now().strftime("%Y-%m-%d")

            # Extract URL
            ticket_url = None
            link = await element.query_selector("a[href*='ticket'], a[href*='event'], a[href*='show']")
            if link:
                href = await link.get_attribute("href")
                if href:
                    ticket_url = urljoin(BASE_URL, href)
            else:
                # Element itself might be a link
                href = await element.get_attribute("href")
                if href:
                    ticket_url = urljoin(BASE_URL, href)

            # Extract image
            image_url = None
            img = await element.query_selector("img")
            if img:
                image_url = await img.get_attribute("src")
                if image_url and not image_url.startswith("http"):
                    image_url = urljoin(BASE_URL, image_url)

            # Extract status (Sold Out, etc.)
            status = None
            status_selectors = [".status", ".badge", "[class*='sold-out']", "[class*='status']"]
            for sel in status_selectors:
                status_el = await element.query_selector(sel)
                if status_el:
                    status = await status_el.inner_text()
                    if status:
                        status = status.strip()
                        break

            # Extract series/category
            series = None
            series_selectors = [".series", ".category", "[class*='series']"]
            for sel in series_selectors:
                series_el = await element.query_selector(sel)
                if series_el:
                    series = await series_el.inner_text()
                    if series:
                        series = series.strip()
                        break

            # Extract description
            description = None
            desc_selectors = [".description", ".summary", "p"]
            for sel in desc_selectors:
                desc_el = await element.query_selector(sel)
                if desc_el:
                    description = await desc_el.inner_text()
                    if description:
                        description = description.strip()[:500]  # Limit length
                        break

            # Parse time and venue from combined string like "7:00 PM | Joe Henderson Lab"
            parsed_time, parsed_venue = self._parse_time_venue(time_text or description)

            return Event(
                title=title,
                date=parsed_date,
                time=parsed_time,
                venue=parsed_venue or "SFJAZZ Center",
                artists=[title] if title else [],  # Often title is artist name
                description=description if description != time_text else None,
                ticket_url=ticket_url,
                status=status,
                series=series,
                image_url=image_url,
            )

        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None

    def _parse_time_venue(self, text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse time and venue from strings like '7:00 PM | Joe Henderson Lab'."""
        if not text:
            return None, None

        text = text.strip()

        # Check for pipe separator
        if "|" in text:
            parts = [p.strip() for p in text.split("|")]
            time_part = None
            venue_part = None

            for part in parts:
                # Check if this looks like a time
                if re.match(r'^\d{1,2}:\d{2}\s*(AM|PM)?', part, re.IGNORECASE):
                    time_part = part
                elif part and not time_part:
                    # First non-time part might be venue
                    if any(v in part.lower() for v in ["lab", "auditorium", "hall", "room", "lounge"]):
                        venue_part = part

            return time_part, venue_part

        # Check for just a time
        time_match = re.match(r'^(\d{1,2}:\d{2}\s*(AM|PM)?)', text, re.IGNORECASE)
        if time_match:
            return time_match.group(1), None

        return None, None

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats into YYYY-MM-DD."""
        if not date_str:
            return None

        date_str = date_str.strip().upper()

        # Handle ISO format
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str[:10]

        # Handle "SAT, JAN 17" or "JAN 17, 2025" format
        months = {
            "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
            "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
        }

        # Try to extract month and day
        for month_abbr, month_num in months.items():
            if month_abbr in date_str:
                # Find day number
                day_match = re.search(r"\b(\d{1,2})\b", date_str)
                if day_match:
                    day = int(day_match.group(1))
                    # Find year or use current year
                    year_match = re.search(r"\b(20\d{2})\b", date_str)
                    year = int(year_match.group(1)) if year_match else datetime.now().year

                    # Adjust year if date seems to be in the past
                    test_date = datetime(year, month_num, day)
                    if test_date < datetime.now() - timedelta(days=30):
                        year += 1

                    return f"{year}-{month_num:02d}-{day:02d}"

        return None

    async def scrape_calendar(self, months_ahead: int = 3) -> list[Event]:
        """
        Scrape events from the SFJAZZ calendar.

        Args:
            months_ahead: Number of months to scrape ahead

        Returns:
            List of scraped Event objects
        """
        all_events = []

        try:
            await self._init_browser()
            page = await self._context.new_page()

            logger.info(f"Navigating to {CALENDAR_URL}")
            await self._retry_operation(
                page.goto, CALENDAR_URL, wait_until="domcontentloaded", timeout=30000
            )

            await self._wait_for_events_loaded(page)

            # Scrape current page
            events = await self._extract_events_from_page(page)
            all_events.extend(events)
            logger.info(f"Scraped {len(events)} events from main calendar")

            # Try to navigate through months
            for _ in range(months_ahead - 1):
                try:
                    next_button = await page.query_selector(
                        "button[class*='next'], .next-month, [aria-label*='next']"
                    )
                    if next_button:
                        await next_button.click()
                        await asyncio.sleep(2)
                        await self._wait_for_events_loaded(page)
                        month_events = await self._extract_events_from_page(page)
                        all_events.extend(month_events)
                        logger.info(f"Scraped {len(month_events)} events from next month")
                except Exception as e:
                    logger.warning(f"Could not navigate to next month: {e}")
                    break

            await page.close()

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise
        finally:
            await self._close_browser()

        # Deduplicate events
        unique_events = list({e for e in all_events if e.title})
        logger.info(f"Total unique events scraped: {len(unique_events)}")

        return unique_events

    async def scrape_and_save(self, months_ahead: int = 3) -> dict:
        """
        Scrape events and save to database.

        Returns:
            Dictionary with scraping statistics
        """
        start_time = datetime.now()
        events = await self.scrape_calendar(months_ahead)

        inserted, updated = self.db.save_events(events)

        stats = {
            "total_scraped": len(events),
            "inserted": inserted,
            "updated": updated,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "scraped_at": start_time.isoformat(),
        }

        logger.info(f"Scraping complete: {stats}")
        return stats

    def export_json(self, filepath: str = "events.json") -> int:
        """Export events to JSON file."""
        count = self.db.export_to_json(filepath)
        logger.info(f"Exported {count} events to {filepath}")
        return count


async def main():
    """Run the scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape SFJAZZ.org events")
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Number of months to scrape ahead (default: 3)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default="events.db",
        help="Database file path (default: events.db)",
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export to JSON file after scraping",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with visible window",
    )
    args = parser.parse_args()

    scraper = SFJazzScraper(
        db_path=args.db,
        headless=not args.no_headless,
    )

    stats = await scraper.scrape_and_save(months_ahead=args.months)
    print(f"\nScraping Results:")
    print(f"  Total events scraped: {stats['total_scraped']}")
    print(f"  New events: {stats['inserted']}")
    print(f"  Updated events: {stats['updated']}")
    print(f"  Duration: {stats['duration_seconds']:.1f}s")

    if args.export:
        count = scraper.export_json(args.export)
        print(f"  Exported {count} events to {args.export}")


if __name__ == "__main__":
    asyncio.run(main())
