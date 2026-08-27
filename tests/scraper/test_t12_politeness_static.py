"""T12.1 / T12.2 - Politeness static checks on scraper/yoshis_scraper.py (C10, C11).

Frozen from .loopzai/spec.md section 5, Layer 2, T12 (static portions).
T12.3 (instrumented live run) lives in tests/live/verify_live.py.
"""
import re
from pathlib import Path

import pytest

SRC = (
    Path(__file__).resolve().parents[2] / "scraper" / "yoshis_scraper.py"
).read_text(encoding="utf-8")


def test_t12_1_semaphore_limit_at_most_4():
    matches = re.findall(r"asyncio\.Semaphore\(\s*([0-9]+)\s*\)", SRC)
    assert matches, "no asyncio.Semaphore(n) found in yoshis_scraper.py"
    for n in matches:
        assert int(n) <= 4, f"asyncio.Semaphore({n}) exceeds the limit of 4"


def test_t12_1b_semaphore_referenced_where_detail_fetching_happens():
    assert "Semaphore" in SRC
    # the semaphore must actually gate something (used as an async context manager)
    assert re.search(r"async with\s+\w*sem\w*", SRC, re.IGNORECASE), (
        "semaphore is created but never used to guard requests"
    )


def test_t12_1c_request_timeout_at_most_30s():
    nums = [
        float(n)
        for n in re.findall(r"ClientTimeout\(\s*total\s*=\s*([0-9.]+)", SRC)
    ] + [
        float(n) for n in re.findall(r"timeout\s*=\s*([0-9.]+)", SRC)
    ]
    assert nums, "no request timeout found in yoshis_scraper.py (C11)"
    assert max(nums) <= 30, f"timeout {max(nums)}s exceeds 30s (C11)"


def test_t12_2_single_client_session_construction():
    """C10: one aiohttp.ClientSession reused for the calendar POST and detail GETs."""
    constructions = re.findall(r"aiohttp\.ClientSession\(", SRC)
    assert len(constructions) == 1, (
        f"expected exactly 1 aiohttp.ClientSession(...) construction, "
        f"found {len(constructions)}"
    )


def test_t12_2b_detail_fetch_takes_a_session_argument():
    """The detail fetch layer must receive a session rather than opening its own."""
    assert re.search(
        r"async def fetch_detail_image[s]?\([^)]*session", SRC, re.DOTALL
    ), "detail fetch helpers do not accept a shared session parameter"
