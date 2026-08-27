"""T5 - merge_events (C15, C16). The core regression test.

Frozen from .loopzai/spec.md section 5, Layer 1, T5.
"""
from scraper.models import Event
from scraper.mrtipples_scraper import merge_events

IMG = "https://h/a.jpg"


def A():
    return Event(title="X", date="2026-09-04", image_url=IMG)


def B():
    return Event(title="X", date="2026-09-04", image_url=None)


def test_t5_1_image_first():
    out = merge_events([A(), B()])
    assert len(out) == 1
    assert out[0].image_url == IMG


def test_t5_2_image_last_order_independence():
    """This fails against the pre-cycle last-wins comprehension."""
    out = merge_events([B(), A()])
    assert len(out) == 1
    assert out[0].image_url == IMG


def test_t5_3_empty_string_counts_as_missing():
    out = merge_events([A(), Event(title="X", date="2026-09-04", image_url="")])
    assert len(out) == 1
    assert out[0].image_url == IMG
    out2 = merge_events([Event(title="X", date="2026-09-04", image_url=""), A()])
    assert len(out2) == 1
    assert out2[0].image_url == IMG


def test_t5_4_field_fill_in():
    out = merge_events(
        [
            Event(title="X", date="D", time=None, price="$20"),
            Event(title="X", date="D", time="8:00 PM", price=None),
        ]
    )
    assert len(out) == 1
    assert out[0].time == "8:00 PM"
    assert out[0].price == "$20"


def test_t5_5_distinct_keys_preserved():
    assert len(merge_events([Event(title="X", date="D1"), Event(title="X", date="D2")])) == 2
    assert len(merge_events([Event(title="Y", date="D1"), Event(title="Z", date="D1")])) == 2


def test_t5_6_empty_input():
    assert merge_events([]) == []


def test_t5_7_idempotence():
    xs = [
        Event(title="X", date="2026-09-04", image_url=None, time="8:00 PM"),
        Event(title="X", date="2026-09-04", image_url=IMG),
        Event(title="Y", date="2026-09-04", image_url=""),
        Event(title="Y", date="2026-09-05", image_url="https://h/y.jpg"),
        Event(title="Z", date="2026-09-06"),
    ]

    def key(events):
        return sorted((e.title, e.date, e.image_url) for e in events)

    once = merge_events(xs)
    twice = merge_events(merge_events(xs))
    assert key(twice) == key(once)


def test_t5_all_field_first_non_empty():
    """C15: image_url, time, price, ticket_url, description all take first non-empty."""
    out = merge_events(
        [
            Event(title="X", date="D", image_url="", time="", price=None,
                  ticket_url=None, description=""),
            Event(title="X", date="D", image_url=IMG, time="9:00 PM", price="$10",
                  ticket_url="https://t/1", description="desc"),
        ]
    )
    assert len(out) == 1
    e = out[0]
    assert e.image_url == IMG
    assert e.time == "9:00 PM"
    assert e.price == "$10"
    assert e.ticket_url == "https://t/1"
    assert e.description == "desc"
