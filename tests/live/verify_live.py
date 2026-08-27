#!/usr/bin/env python3
"""Layer 2 live smoke checks - T7.2-T7.5, T8, T9, T10 from .loopzai/spec.md section 5.

Frozen at verification attempt 1 of cycle 2.

Usage:
  .venv/bin/python tests/live/verify_live.py <new_events.json> <baseline_events.json>

T7.1 (scrape exit code), T11 (npm test / git diff) and T12.3 (instrumented run)
are executed by the verification driver, not this script.
"""
import json
import sys
from datetime import datetime, timezone

VENUES = [
    "SFJAZZ Center",
    "Dawn Club",
    "Black Cat SF",
    "Keys Jazz Bistro",
    "Mr. Tipple's",
    "Yoshi's",
]
HEALTHY_FOUR = ["SFJAZZ Center", "Dawn Club", "Black Cat SF", "Keys Jazz Bistro"]

results = []


def check(tid, desc, ok, detail=""):
    results.append((tid, desc, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {tid}  {desc}" + (f"  --  {detail}" if detail else ""))
    return ok


def upcoming(events, venue, today):
    return [e for e in events if e.get("venue") == venue and (e.get("date") or "") >= today]


def has_image(e):
    v = e.get("image_url")
    return bool(v) and isinstance(v, str) and v.strip() != ""


def main():
    new_path, base_path = sys.argv[1], sys.argv[2]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"today (UTC) = {today}\nnew = {new_path}\nbaseline = {base_path}\n")

    # --- T7.2 ---
    try:
        new = json.load(open(new_path))
        ok = isinstance(new, list) and len(new) > 0
    except Exception as exc:  # noqa: BLE001
        new, ok = [], False
        print(f"json load error: {exc}")
    check("T7.2", "data/events.json is valid JSON and a non-empty array", ok, f"{len(new)} events")

    base = json.load(open(base_path))

    # --- T7.3 / T7.4 ---
    floors = {v: 0.80 for v in VENUES}
    floors["Mr. Tipple's"] = 0.70
    for v in VENUES:
        n = len(upcoming(new, v, today))
        b = len(upcoming(base, v, today))
        ratio = (n / b) if b else float("inf")
        check(
            "T7.3",
            f"{v}: upcoming >= {int(floors[v] * 100)}% of baseline",
            b == 0 or ratio >= floors[v],
            f"new={n} baseline={b} ratio={ratio:.2%}",
        )
        check("T7.4", f"{v}: upcoming count is not 0", n > 0, f"new={n}")

    # --- T7.5 ---
    for v in HEALTHY_FOUR:
        ups = upcoming(new, v, today)
        withimg = [e for e in ups if has_image(e)]
        frac = (len(withimg) / len(ups)) if ups else 0.0
        check("T7.5", f"{v}: >= 95% of upcoming have an image", frac >= 0.95,
              f"{len(withimg)}/{len(ups)} = {frac:.1%}")

    # --- T8 ---
    ups = upcoming(new, "Yoshi's", today)
    good = [
        e for e in ups
        if has_image(e)
        and e["image_url"].startswith("https://yoshis.com/")
        and not e["image_url"].startswith("data:")
    ]
    frac = (len(good) / len(ups)) if ups else 0.0
    check("T8", "Yoshi's upcoming image yield >= 70%", frac >= 0.70,
          f"{len(good)}/{len(ups)} = {frac:.1%}  (spec expectation ~100%)")

    # --- T9 ---
    ups = upcoming(new, "Mr. Tipple's", today)
    good = [
        e for e in ups
        if has_image(e)
        and e["image_url"].startswith("https://")
        and not e["image_url"].startswith("data:")
    ]
    frac = (len(good) / len(ups)) if ups else 0.0
    check("T9", "Mr. Tipple's upcoming image yield >= 50%", frac >= 0.50,
          f"{len(good)}/{len(ups)} = {frac:.1%}  (spec expectation 100%)")

    # --- T10 ---
    empties = [e for e in new if e.get("image_url") == ""]
    check("T10.1", "no event has image_url == ''", not empties, f"{len(empties)} offenders")

    datauris = [e for e in new if isinstance(e.get("image_url"), str)
                and e["image_url"].lower().startswith("data:")]
    check("T10.2", "no event has a data: image_url", not datauris, f"{len(datauris)} offenders")

    rel = [
        e for e in new
        if e.get("venue") in ("Yoshi's", "Mr. Tipple's")
        and isinstance(e.get("image_url"), str) and e["image_url"] != ""
        and not e["image_url"].startswith(("http://", "https://"))
    ]
    check("T10.3", "no Yoshi's / Mr. Tipple's relative image_url", not rel,
          f"{len(rel)} offenders" + (f" e.g. {rel[0]['image_url']!r}" if rel else ""))

    ents = [e for e in new if e.get("venue") == "Mr. Tipple's" and "&#" in (e.get("title") or "")]
    check("T10.4", "no Mr. Tipple's title contains '&#'", not ents,
          f"{len(ents)} offenders" + (f" e.g. {ents[0]['title']!r}" if ents else ""))

    # --- summary ---
    failed = [r for r in results if not r[2]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILURES:")
        for tid, desc, _, detail in failed:
            print(f"  {tid}  {desc}  --  {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
