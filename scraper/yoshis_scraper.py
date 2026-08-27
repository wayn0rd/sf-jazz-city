"""Yoshi's Oakland event scraper - uses the JSON calendar API (no browser needed).

Event images are not present in the calendar feed; they live on each event's
detail page as ``<img class="event-img">``. The detail pages are plain
server-rendered HTML, so they are fetched with aiohttp (no browser), once per
unique detail URL, under a small concurrency cap.
"""

import asyncio
import logging
import re
import aiohttp
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin

from .models import Event
from .database import EventDatabase
from .image_utils import normalize_image_url

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

# The class token that marks the event hero image on a detail page. Deliberately
# a *token* test, not a substring test: "event-image-wrapper" must not match.
EVENT_IMAGE_CLASS = "event-img"

# Detail pages are plain HTML; 20s is generous (the live pages answer in <1s).
DETAIL_TIMEOUT_SECONDS = 20

# re.DOTALL matters: the live pages break lines *inside* the <img> tag.
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE | re.DOTALL)
_ATTR_RE = re.compile(
    r"""([A-Za-z_:][-\w:.]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))""",
    re.DOTALL,
)


def _tag_attributes(tag: str) -> dict:
    """Parse the attributes of a single HTML start tag into a lowercased dict."""
    attrs: dict = {}
    for match in _ATTR_RE.finditer(tag):
        name = match.group(1).lower()
        value = match.group(2)
        if value is None:
            value = match.group(3)
        if value is None:
            value = match.group(4) or ""
        attrs.setdefault(name, value)
    return attrs


def extract_image_url(html_text: str) -> Optional[str]:
    """Return the absolute URL of the ``event-img`` image on a detail page.

    Pure and synchronous. Returns None when the page carries no such element,
    or when the element's src is rejected by normalize_image_url (data URI,
    SVG, empty). The site logo and the Facebook tracking pixel are <img>
    elements on every detail page; neither carries the event-img class token,
    so neither can be returned.
    """
    if not html_text:
        return None

    for match in _IMG_TAG_RE.finditer(html_text):
        attrs = _tag_attributes(match.group(0))
        if EVENT_IMAGE_CLASS not in attrs.get("class", "").split():
            continue
        url = normalize_image_url(attrs.get("src"), BASE_URL)
        if url:
            return url
    return None


def detail_url_from_item(item: dict) -> Optional[str]:
    """Return the absolute detail-page URL for a calendar JSON item, or None."""
    if not isinstance(item, dict):
        return None

    raw = item.get("url")
    if not isinstance(raw, str):
        return None

    raw = raw.strip()
    if not raw:
        return None

    if raw.lower().startswith(("http://", "https://")):
        return raw
    return urljoin(BASE_URL, raw)


async def fetch_detail_image(
    session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore
) -> Optional[str]:
    """Fetch one detail page and extract its event image URL.

    Never raises: a network error, timeout, non-200 status or image-less page
    all yield None.
    """
    async with semaphore:
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=DETAIL_TIMEOUT_SECONDS)
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        f"Yoshi's detail page {url} returned HTTP {resp.status}"
                    )
                    return None
                html_text = await resp.text()
        except Exception as e:
            logger.warning(f"Yoshi's detail fetch failed for {url}: {e}")
            return None

    return extract_image_url(html_text)


async def fetch_detail_images(
    session: aiohttp.ClientSession, urls: list[str]
) -> dict[str, Optional[str]]:
    """Fetch every *unique* detail URL once and map it to its image URL.

    Concurrency is capped at 4 in-flight requests. Never raises for an
    individual URL; the caller still guards the whole call.
    """
    unique: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            unique.append(url)

    if not unique:
        return {}

    semaphore = asyncio.Semaphore(4)  # C11: at most 4 concurrent detail fetches
    logger.info(f"Fetching {len(unique)} unique Yoshi's detail pages for images")

    results = await asyncio.gather(
        *(fetch_detail_image(session, url, semaphore) for url in unique),
        return_exceptions=True,
    )

    images: dict[str, Optional[str]] = {}
    for url, result in zip(unique, results):
        if isinstance(result, BaseException):
            logger.warning(f"Yoshi's detail fetch raised for {url}: {result}")
            images[url] = None
        else:
            images[url] = result
    return images


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

            # Prefer etix URL (direct purchase), fall back to detail page URL.
            # C13: image fetching must not change this preference.
            detail_url = detail_url_from_item(item)
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

    async def _fetch_detail_images(
        self, session: aiohttp.ClientSession, urls: list[str]
    ) -> dict[str, Optional[str]]:
        """Instance seam over fetch_detail_images (kept for test injection)."""
        return await fetch_detail_images(session, urls)

    async def scrape_events(self) -> list[Event]:
        """Fetch events from Yoshi's JSON calendar API, with detail-page images."""
        now = datetime.now()
        end = now + timedelta(days=30 * self.months_ahead)

        payload = {
            "start": now.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
        }

        # One session for the calendar POST and every detail GET (C10).
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

            parsed: list[tuple[Event, Optional[str]]] = []
            for item in data:
                event = self._parse_event(item)
                if event:
                    parsed.append((event, detail_url_from_item(item)))

            # Deduplicate by (title, date, time) — same show can have two sets
            # (e.g. 7:30 and 9:30). Key and last-wins semantics unchanged (C14).
            unique_map: dict[tuple, tuple[Event, Optional[str]]] = {}
            for event, detail_url in parsed:
                unique_map[(event.title, event.date, event.time)] = (event, detail_url)
            pairs = list(unique_map.values())

            # C12: a detail-page outage degrades to today's behaviour (no
            # images); it must never fail the venue or the run.
            images: dict[str, Optional[str]] = {}
            try:
                images = await self._fetch_detail_images(
                    session, [url for _, url in pairs if url]
                )
            except Exception as e:
                logger.error(f"Yoshi's detail-image fetch failed entirely: {e}")
                images = {}

        for event, detail_url in pairs:
            if detail_url:
                event.image_url = images.get(detail_url)

        unique = [event for event, _ in pairs]
        with_images = sum(1 for e in unique if e.image_url)
        logger.info(
            f"Total unique events: {len(unique)} ({with_images} with images)"
        )
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
