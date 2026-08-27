"""Shared fixtures for the cycle-2 frozen scraper test suite.

Derived from .loopzai/spec.md section 5 (FROZEN at approval).
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "scraper"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture(scope="session")
def yoshis_html_with_image(fixture_dir) -> str:
    return (fixture_dir / "yoshis_detail_with_image.html").read_text(
        encoding="utf-8", errors="replace"
    )


@pytest.fixture(scope="session")
def yoshis_html_no_image(fixture_dir) -> str:
    return (fixture_dir / "yoshis_detail_no_image.html").read_text(
        encoding="utf-8", errors="replace"
    )
