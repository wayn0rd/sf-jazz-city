"""Shared image-URL normalization for venue scrapers.

Pure, synchronous, side-effect-free. No network access, no third-party
dependencies (stdlib only) — see spec.md cycle 2, D-s5 / D-s6.
"""

from typing import Optional
from urllib.parse import urljoin, urlsplit

__all__ = ["normalize_image_url"]


def normalize_image_url(raw: Optional[str], base_url: str) -> Optional[str]:
    """Normalize a scraped image URL to an absolute http(s) URL, or None.

    Rejects (returns None):
      - None, the empty string, whitespace-only strings
      - any value whose lowercased form starts with ``data:``
      - any value whose path component (query string and fragment ignored)
        ends in ``.svg`` (case-insensitive)

    Otherwise returns an absolute URL:
      - a relative path is joined against ``base_url``
      - a protocol-relative ``//host/path`` is given the ``https:`` scheme
      - an already-absolute ``http://`` / ``https://`` URL is returned unchanged

    The return value is always either None or a str starting with ``http://``
    or ``https://``.
    """
    if raw is None or not isinstance(raw, str):
        return None

    value = raw.strip()
    if not value:
        return None

    lowered = value.lower()
    if lowered.startswith("data:"):
        return None

    # .svg check looks at the path only, so query strings/fragments don't hide it
    try:
        path = urlsplit(value).path
    except ValueError:
        return None
    if path.lower().endswith(".svg"):
        return None

    if value.startswith("//"):
        absolute = "https:" + value
    elif lowered.startswith("http://") or lowered.startswith("https://"):
        absolute = value
    else:
        absolute = urljoin(base_url, value)

    # C3: never hand back something that isn't an absolute http(s) URL.
    if not absolute.lower().startswith(("http://", "https://")):
        return None

    return absolute
