#!/usr/bin/env python3
"""T10.2a - amendment-0001 scoped variant of frozen live check T10.2.

ADDED at verification attempt 2 of cycle 2 under the spec-amendment mechanism.
This file is an ADDITION. The frozen implementation of T10.2 in
tests/live/verify_live.py is NOT modified, NOT weakened and still runs
unchanged every attempt; its raw result is reported alongside this one.

Authority: .loopzai/spec-amendments.md, cycle 2 amendment-0001 (Wayne-approved,
2026-08-27, Option A) - "T10.2's prohibition on `data:` image URLs applies to
events of the cycle-2 in-scope venues - Yoshi's and Mr. Tipple's - only,
matching the venue-scoped formulation of T10.3/T10.4."

Usage:
  .venv/bin/python tests/live/verify_amendment_0001.py <new_events.json> <baseline_events.json>
"""
import json
import sys

IN_SCOPE = ("Yoshi's", "Mr. Tipple's")

results = []


def check(tid, desc, ok, detail=""):
    results.append((tid, desc, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {tid}  {desc}" + (f"  --  {detail}" if detail else ""))
    return ok


def datauris(events, venues=None):
    return [
        e for e in events
        if isinstance(e.get("image_url"), str)
        and e["image_url"].lower().startswith("data:")
        and (venues is None or e.get("venue") in venues)
    ]


def main():
    new = json.load(open(sys.argv[1]))
    base = json.load(open(sys.argv[2]))

    # --- T10.2a: the amended gate ---
    off = datauris(new, IN_SCOPE)
    check(
        "T10.2a",
        "no Yoshi's / Mr. Tipple's event has a data: image_url (amendment-0001)",
        not off,
        f"{len(off)} offenders"
        + (f" e.g. {off[0]['venue']} {off[0]['title']!r}" if off else ""),
    )

    # --- T10.2b: the amendment's own premise, re-verified, not taken on trust.
    # Every remaining corpus-wide data: row must be out-of-scope AND pre-existing
    # (present byte-identically in the baseline). This makes the narrowing
    # non-exploitable: cycle-2 code cannot hide a new data: URL behind it.
    all_off = datauris(new)
    out_of_scope = [e for e in all_off if e.get("venue") not in IN_SCOPE]
    check(
        "T10.2b",
        "every corpus-wide data: row belongs to an out-of-scope venue",
        len(all_off) == len(out_of_scope),
        f"{len(all_off)} total, {len(out_of_scope)} out-of-scope, "
        f"venues={sorted({e.get('venue') for e in all_off})}",
    )

    def key(e):
        return (e.get("venue"), e.get("title"), e.get("date"), e.get("image_url"))

    base_keys = {key(e) for e in datauris(base)}
    novel = [e for e in all_off if key(e) not in base_keys]
    check(
        "T10.2c",
        "no data: row is new relative to the pre-attempt baseline",
        not novel,
        f"{len(novel)} newly-introduced"
        + (f" e.g. {novel[0]['venue']} {novel[0]['title']!r}" if novel else ""),
    )

    failed = [r for r in results if not r[2]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    for tid, desc, _, detail in failed:
        print(f"  FAIL {tid}  {desc}  --  {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
