"""T3 - Yoshi's detail_url_from_item + ticket_url non-regression (C8, C13).

Frozen from .loopzai/spec.md section 5, Layer 1, T3.
"""
import pytest

from scraper.yoshis_scraper import YoshisScraper, detail_url_from_item

# Verbatim live item from the spec.
LIVE_ITEM = {
    "title": (
        '7:30PM KEIKO MATSUI<br/><a href="https://www.etix.com/ticket/p/69261880/'
        "keiko-matsui-wed82626-oakland-yoshis\" target='_blank' "
        "class='calendarBuyTickets'>Buy Tickets</a>"
    ),
    "start": "2026-08-26 19:30:00",
    "end": "2026-08-26",
    "eventOrder": 1,
    "className": "Buy Tickets",
    "url": "https://yoshis.com/events/sold-out/keiko-matsui-14/detail",
}

ETIX = "https://www.etix.com/ticket/p/69261880/keiko-matsui-wed82626-oakland-yoshis"


@pytest.fixture()
def scraper(tmp_path):
    return YoshisScraper(db_path=str(tmp_path / "test.db"))


def test_t3_1_detail_url_from_live_item():
    assert (
        detail_url_from_item(LIVE_ITEM)
        == "https://yoshis.com/events/sold-out/keiko-matsui-14/detail"
    )


def test_t3_2_ticket_url_is_still_etix_not_detail(scraper):
    """C13 / R6: the most likely silent regression in this cycle."""
    event = scraper._parse_event(LIVE_ITEM)
    assert event is not None
    assert event.ticket_url == ETIX
    assert event.ticket_url != LIVE_ITEM["url"]


def test_t3_3_title(scraper):
    assert scraper._parse_event(LIVE_ITEM).title == "KEIKO MATSUI"


def test_t3_4_date_and_time(scraper):
    event = scraper._parse_event(LIVE_ITEM)
    assert event.date == "2026-08-26"
    assert event.time == "7:30 PM"


def test_t3_5_missing_or_empty_url_is_none():
    assert detail_url_from_item({}) is None
    assert detail_url_from_item({"url": ""}) is None


def test_t3_6_relative_url_absolutized():
    assert (
        detail_url_from_item({"url": "/events/x/detail"})
        == "https://yoshis.com/events/x/detail"
    )


def test_t3_7_sold_out_status_preserved(scraper):
    item = dict(LIVE_ITEM)
    item["className"] = "Sold Out"
    event = scraper._parse_event(item)
    assert event is not None
    assert event.status == "Sold Out"
