#!/usr/bin/env python3
"""T12.3 - instrumented Yoshi's-only run (C10).

Counts real detail-page GETs and compares against the number of unique detail
URLs derived from the live calendar feed. Frozen at verification attempt 1.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scraper import yoshis_scraper  # noqa: E402
from scraper.yoshis_scraper import YoshisScraper, detail_url_from_item  # noqa: E402

get_calls = []
parsed_items = {"raw": 0}

_real_fetch_one = yoshis_scraper.fetch_detail_image
_real_fetch_many = yoshis_scraper.fetch_detail_images


async def counting_fetch_one(session, url, semaphore):
    get_calls.append(url)
    return await _real_fetch_one(session, url, semaphore)


async def counting_fetch_many(session, urls):
    parsed_items["requested_urls"] = len(urls)
    parsed_items["unique_urls"] = len({u for u in urls if u})
    return await _real_fetch_many(session, urls)


yoshis_scraper.fetch_detail_image = counting_fetch_one
yoshis_scraper.fetch_detail_images = counting_fetch_many


async def main():
    scraper = YoshisScraper(db_path="/tmp/loopz-verif/instrument.db")
    events = await scraper.scrape_events()
    unique_urls = parsed_items.get("unique_urls", 0)
    with_images = sum(1 for e in events if e.image_url)
    print(f"events               : {len(events)}")
    print(f"detail urls requested: {parsed_items.get('requested_urls')}")
    print(f"unique detail urls   : {unique_urls}")
    print(f"actual detail GETs   : {len(get_calls)}")
    print(f"duplicate GETs       : {len(get_calls) - len(set(get_calls))}")
    print(f"events with images   : {with_images}/{len(events)}")
    ok = len(get_calls) <= unique_urls and len(get_calls) == len(set(get_calls))
    print(f"[{'PASS' if ok else 'FAIL'}] T12.3  detail GETs <= unique detail URLs")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
