"""T1 - normalize_image_url (C1-C3). Table test; each row asserts exact equality.

Frozen from .loopzai/spec.md section 5, Layer 1, T1.
"""
import pytest

from scraper.image_utils import normalize_image_url

YOSHIS = "https://yoshis.com"
TIPPLES = "https://mrtipplessf.com"

# (raw, base_url, expected) - verbatim from the spec T1 table.
T1_TABLE = [
    (
        "/userfiles/events/images/2866/keikomatsui2-copy.jpeg",
        YOSHIS,
        "https://yoshis.com/userfiles/events/images/2866/keikomatsui2-copy.jpeg",
    ),
    (
        "https://mrtipplessf.com/wp-content/uploads/Sam-Bevin-.jpg",
        TIPPLES,
        "https://mrtipplessf.com/wp-content/uploads/Sam-Bevin-.jpg",
    ),
    ("//cdn.example.com/a.jpg", YOSHIS, "https://cdn.example.com/a.jpg"),
    (None, YOSHIS, None),
    ("", YOSHIS, None),
    ("   ", YOSHIS, None),
    ("data:image/svg+xml;base64,PHN2Zz4=", YOSHIS, None),
    ("data:image/png;base64,iVBORw0KGgo=", YOSHIS, None),
    ("/assets/placeholder.svg", YOSHIS, None),
    ("/assets/placeholder.SVG?v=2", YOSHIS, None),
]


@pytest.mark.parametrize("raw,base,expected", T1_TABLE)
def test_t1_table_exact_equality(raw, base, expected):
    assert normalize_image_url(raw, base) == expected


@pytest.mark.parametrize("raw,base,expected", T1_TABLE)
def test_t1_property_none_or_absolute(raw, base, expected):
    """For every input in the table: result is None or a str starting http(s)://."""
    result = normalize_image_url(raw, base)
    assert result is None or (
        isinstance(result, str)
        and (result.startswith("http://") or result.startswith("https://"))
    )


@pytest.mark.parametrize("raw,base,expected", T1_TABLE)
def test_t1_none_rows_are_none_not_empty_string(raw, base, expected):
    """C4: never the empty string - rejects must be None, not ''."""
    if expected is None:
        assert normalize_image_url(raw, base) is None
