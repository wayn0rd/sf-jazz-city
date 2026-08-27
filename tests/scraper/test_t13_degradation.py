"""T13 - Failure degradation (C12), plus the offline half of T12.3 (C10).

Frozen from .loopzai/spec.md section 5, Layer 1/2, T13 and T12.3.

Runs fully offline: aiohttp.ClientSession is replaced inside the
yoshis_scraper module namespace with a fake that serves the calendar POST
from an in-memory payload. No socket is opened.
"""
import asyncio

import pytest

from scraper import yoshis_scraper
from scraper.yoshis_scraper import YoshisScraper

# Three shows across two unique detail URLs (7:30 + 9:30 sets share a page).
CALENDAR_ITEMS = [
    {
        "title": '7:30PM KEIKO MATSUI<br/><a href="https://www.etix.com/ticket/p/1/a">Buy Tickets</a>',
        "start": "2026-08-26 19:30:00",
        "end": "2026-08-26",
        "eventOrder": 1,
        "className": "Buy Tickets",
        "url": "https://yoshis.com/events/keiko-matsui-14/detail",
    },
    {
        "title": '9:30PM KEIKO MATSUI<br/><a href="https://www.etix.com/ticket/p/1/a">Buy Tickets</a>',
        "start": "2026-08-26 21:30:00",
        "end": "2026-08-26",
        "eventOrder": 2,
        "className": "Buy Tickets",
        "url": "https://yoshis.com/events/keiko-matsui-14/detail",
    },
    {
        "title": '8:00PM SOMEONE ELSE<br/><a href="https://www.etix.com/ticket/p/2/b">Buy Tickets</a>',
        "start": "2026-08-27 20:00:00",
        "end": "2026-08-27",
        "eventOrder": 1,
        "className": "Sold Out",
        "url": "https://yoshis.com/events/someone-else/detail",
    },
]

UNIQUE_DETAIL_URLS = 2
EXPECTED_EVENT_COUNT = 3
DETAIL_HTML = (
    '<html><body><img src="/images/yoshi-logo.png" class="logo"/>'
    '<img\n  src="/userfiles/events/images/1/a.jpeg"\n  class="lazy event-img"/>'
    '<img src="https://facebook.com/tr?id=1" /></body></html>'
)


class _FakeResponse:
    def __init__(self, status=200, json_data=None, text=""):
        self.status = status
        self._json = json_data
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    async def json(self, content_type=None):
        return self._json

    async def text(self):
        return self._text


class _FakeSession:
    """Minimal stand-in for aiohttp.ClientSession."""

    instances = []

    def __init__(self, *args, **kwargs):
        self.get_calls = []
        self.post_calls = []
        _FakeSession.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def post(self, url, **kwargs):
        self.post_calls.append(url)
        return _FakeResponse(json_data=CALENDAR_ITEMS)

    def get(self, url, **kwargs):
        self.get_calls.append(url)
        return _FakeResponse(status=200, text=DETAIL_HTML)


@pytest.fixture(autouse=True)
def fake_network(monkeypatch):
    _FakeSession.instances = []

    class _FakeAiohttp:
        ClientSession = _FakeSession
        ClientTimeout = yoshis_scraper.aiohttp.ClientTimeout

    monkeypatch.setattr(yoshis_scraper, "aiohttp", _FakeAiohttp)
    yield


@pytest.fixture()
def scraper(tmp_path):
    return YoshisScraper(db_path=str(tmp_path / "test.db"))


def _run(coro):
    return asyncio.run(coro)


# --- baseline: detail fetching disabled (returns no images) ---


def test_t13_baseline_fetching_disabled(scraper, monkeypatch):
    monkeypatch.setattr(
        yoshis_scraper, "fetch_detail_images", lambda session, urls: _noop()
    )
    events = _run(scraper.scrape_events())
    assert len(events) == EXPECTED_EVENT_COUNT
    assert all(e.image_url is None for e in events)


async def _noop():
    return {}


# --- T13: the detail-fetch helper raises on every call ---


def test_t13_helper_raises_all_events_survive(scraper, monkeypatch):
    async def _boom(session, urls):
        raise RuntimeError("detail fetch exploded")

    monkeypatch.setattr(yoshis_scraper, "fetch_detail_images", _boom)

    events = _run(scraper.scrape_events())  # must not raise
    assert len(events) == EXPECTED_EVENT_COUNT
    assert all(e.image_url is None for e in events)


def test_t13_per_url_helper_raises(scraper, monkeypatch):
    """Per-URL fetch failures also degrade to None, not an exception."""

    async def _boom(session, url, semaphore):
        raise RuntimeError("single fetch exploded")

    monkeypatch.setattr(yoshis_scraper, "fetch_detail_image", _boom)

    events = _run(scraper.scrape_events())
    assert len(events) == EXPECTED_EVENT_COUNT
    assert all(e.image_url is None for e in events)


def test_t13_non_200_degrades_to_none(scraper, monkeypatch):
    monkeypatch.setattr(
        _FakeSession, "get", lambda self, url, **kw: _FakeResponse(status=503)
    )
    events = _run(scraper.scrape_events())
    assert len(events) == EXPECTED_EVENT_COUNT
    assert all(e.image_url is None for e in events)


# --- happy path through the same offline harness (C9) ---


def test_happy_path_populates_images(scraper):
    events = _run(scraper.scrape_events())
    assert len(events) == EXPECTED_EVENT_COUNT
    assert all(
        e.image_url == "https://yoshis.com/userfiles/events/images/1/a.jpeg"
        for e in events
    )


# --- T12.3 offline: at most one GET per unique detail URL (C10) ---


def test_t12_3_offline_one_get_per_unique_detail_url(scraper):
    _run(scraper.scrape_events())
    assert len(_FakeSession.instances) == 1, "more than one ClientSession was opened"
    session = _FakeSession.instances[0]
    assert len(session.get_calls) <= UNIQUE_DETAIL_URLS
    assert len(session.get_calls) == len(set(session.get_calls))
    assert len(session.get_calls) < EXPECTED_EVENT_COUNT, (
        "detail pages were not cached per URL"
    )


def test_t12_2_offline_single_session_for_post_and_gets(scraper):
    """C10: the calendar POST and every detail GET share one session."""
    _run(scraper.scrape_events())
    assert len(_FakeSession.instances) == 1
    session = _FakeSession.instances[0]
    assert len(session.post_calls) == 1
    assert len(session.get_calls) >= 1


# --- T3.2 / C13 through the full path: ticket_url must stay etix ---


def test_c13_ticket_url_unchanged_after_image_fetch(scraper):
    events = _run(scraper.scrape_events())
    by_title = {e.title: e for e in events}
    assert by_title["KEIKO MATSUI"].ticket_url == "https://www.etix.com/ticket/p/1/a"
    assert by_title["SOMEONE ELSE"].ticket_url == "https://www.etix.com/ticket/p/2/b"
    assert by_title["SOMEONE ELSE"].status == "Sold Out"
