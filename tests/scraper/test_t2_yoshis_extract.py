"""T2 - Yoshi's extract_image_url (C5-C7).

Frozen from .loopzai/spec.md section 5, Layer 1, T2.
"""
import re

import pytest

from scraper.yoshis_scraper import extract_image_url

EXPECTED = "https://yoshis.com/userfiles/events/images/2866/keikomatsui2-copy.jpeg"


# --- spec section 5 "Fixtures" preconditions (fixtures must retain these) ---


def test_fixture_with_image_retains_required_elements(yoshis_html_with_image):
    html = yoshis_html_with_image
    assert "event-img" in html, "fixture must retain the img.event-img element"
    assert "/images/yoshi-logo.png" in html, "fixture must retain the logo <img>"
    assert "facebook.com/tr" in html, "fixture must retain the FB tracking pixel"
    assert re.search(r"<[a-zA-Z][^<>]*\n[^<>]*>", html), (
        "fixture must retain at least one tag with a newline inside it"
    )


def test_fixture_no_image_has_event_img_removed(yoshis_html_no_image):
    html = yoshis_html_no_image
    assert not re.search(r"""class\s*=\s*["'][^"']*\bevent-img\b""", html), (
        "no_image fixture must have the event-img element removed"
    )
    assert "/images/yoshi-logo.png" in html
    assert "facebook.com/tr" in html


# --- T2.1 - T2.10 ---


def test_t2_1_fixture_with_image(yoshis_html_with_image):
    assert extract_image_url(yoshis_html_with_image) == EXPECTED


def test_t2_2_fixture_no_image(yoshis_html_no_image):
    assert extract_image_url(yoshis_html_no_image) is None


def test_t2_3_not_the_logo(yoshis_html_with_image):
    assert "yoshi-logo" not in (extract_image_url(yoshis_html_with_image) or "")


def test_t2_4_not_the_fb_pixel(yoshis_html_with_image):
    assert "facebook.com/tr" not in (extract_image_url(yoshis_html_with_image) or "")


def test_t2_5_src_before_class():
    assert (
        extract_image_url('<img src="/a/b.jpg" class="event-img" />')
        == "https://yoshis.com/a/b.jpg"
    )


def test_t2_6_class_before_src():
    assert (
        extract_image_url('<img class="event-img" src="/a/b.jpg" />')
        == "https://yoshis.com/a/b.jpg"
    )


def test_t2_7_newline_inside_tag():
    assert (
        extract_image_url('<img\n  src="/a/b.jpg"\n  class="event-img" />')
        == "https://yoshis.com/a/b.jpg"
    )


def test_t2_8_multi_token_class():
    assert (
        extract_image_url('<img src="/a/b.jpg" class="lazy event-img rounded" />')
        == "https://yoshis.com/a/b.jpg"
    )


def test_t2_9_substring_must_not_match_token():
    assert extract_image_url('<img src="/a/b.jpg" class="event-image-wrapper" />') is None


def test_t2_10_data_uri_rejected_after_extraction():
    assert (
        extract_image_url(
            '<img src="data:image/svg+xml;base64,PHN2Zz4=" class="event-img" />'
        )
        is None
    )
