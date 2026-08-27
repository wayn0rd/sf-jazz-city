"""T4 - Mr. Tipple's _parse_schema_event (C18, C19).

Frozen from .loopzai/spec.md section 5, Layer 1, T4.
"""
import pytest

from scraper.mrtipples_scraper import MrTipplesScraper

START = "2026-09-04T18:15:00-08:00"


@pytest.fixture()
def scraper(tmp_path):
    return MrTipplesScraper(db_path=str(tmp_path / "test.db"))


def _data(**overrides):
    base = {"@type": "Event", "name": "A", "startDate": START}
    base.update(overrides)
    return base


def test_t4_1_string_image(scraper):
    ev = scraper._parse_schema_event(
        _data(image="https://mrtipplessf.com/wp-content/uploads/a.jpg")
    )
    assert ev.image_url == "https://mrtipplessf.com/wp-content/uploads/a.jpg"


def test_t4_2_list_image_takes_first(scraper):
    ev = scraper._parse_schema_event(
        _data(image=["https://mrtipplessf.com/a.jpg", "https://mrtipplessf.com/b.jpg"])
    )
    assert ev.image_url == "https://mrtipplessf.com/a.jpg"


def test_t4_3_dict_image(scraper):
    ev = scraper._parse_schema_event(
        _data(image={"url": "https://mrtipplessf.com/a.jpg"})
    )
    assert ev.image_url == "https://mrtipplessf.com/a.jpg"


def test_t4_4_absent_image(scraper):
    assert scraper._parse_schema_event(_data()).image_url is None


def test_t4_5_empty_string_image_is_none_not_empty(scraper):
    ev = scraper._parse_schema_event(_data(image=""))
    assert ev.image_url is None
    assert ev.image_url != ""


def test_t4_6_data_uri_image_is_none(scraper):
    ev = scraper._parse_schema_event(_data(image="data:image/svg+xml;base64,PHN2Zz4="))
    assert ev.image_url is None


def test_t4_7_relative_image_absolutized(scraper):
    ev = scraper._parse_schema_event(_data(image="/wp-content/uploads/a.jpg"))
    assert ev.image_url == "https://mrtipplessf.com/wp-content/uploads/a.jpg"


def test_t4_8_entity_decoding_curly_quotes(scraper):
    ev = scraper._parse_schema_event(
        _data(name="Patrick Wolff&#8217;s &#8220;Swinging Organ&#8221; Quartet")
    )
    assert ev.title == "Patrick Wolff’s “Swinging Organ” Quartet"


def test_t4_9_entity_decoding_ampersand(scraper):
    ev = scraper._parse_schema_event(
        _data(name="Carla Helmbrecht &#038; The Brad Leali Quartet")
    )
    assert ev.title == "Carla Helmbrecht & The Brad Leali Quartet"


@pytest.mark.parametrize(
    "data",
    [
        _data(image="https://mrtipplessf.com/wp-content/uploads/a.jpg"),
        _data(image=["https://mrtipplessf.com/a.jpg", "https://mrtipplessf.com/b.jpg"]),
        _data(image={"url": "https://mrtipplessf.com/a.jpg"}),
        _data(),
        _data(image=""),
        _data(image="data:image/svg+xml;base64,PHN2Zz4="),
        _data(image="/wp-content/uploads/a.jpg"),
        _data(name="Patrick Wolff&#8217;s &#8220;Swinging Organ&#8221; Quartet"),
        _data(name="Carla Helmbrecht &#038; The Brad Leali Quartet"),
    ],
)
def test_t4_10_no_entities_in_any_title(scraper, data):
    ev = scraper._parse_schema_event(data)
    assert ev is not None
    assert "&#" not in ev.title
