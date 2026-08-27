<!-- verification.md — verification results for the current cycle. -->

# Cycle 2 — Verification attempt 2 of 3

**Graded against:** `.loopzai/spec.md` §5 (frozen at approval) +
`.loopzai/spec-amendments.md` **amendment-0001** (Wayne-approved, 2026-08-27).
**Executable tests frozen at:** commit `667f93a`
(`loopzai: cycle 2 - freeze executable test suite (spec section 5)`).
**Repo HEAD graded:** `2ba48d2`. **Run date (UTC):** 2026-08-27.

This attempt ran the frozen suite **unchanged** and added — never substituted —
one new file covering amendment-0001. Nothing under `tests/scraper/` or
`tests/live/verify_live.py` was edited; `git diff 667f93a HEAD -- tests/` and
`git diff HEAD -- tests/` are both empty, so the frozen target is provably
identical to attempt 1's.

---

## Verdict summary

**PASS.** All 95 frozen unit assertions and all frozen live checks pass, and
the one check that reads red — frozen `T10.2` — is red only because its
implementation predates amendment-0001 and still asserts the pre-amendment,
corpus-wide form of the gate that Wayne has since scoped to the two in-scope
venues. Under the grading standard as amended, the cycle's commitments are met.

| Test | Result |
|---|---|
| T1 `normalize_image_url` (C1–C3) | **PASS** (30 assertions) |
| T2 Yoshi's `extract_image_url` (C5–C7) | **PASS** (12) |
| T3 `detail_url_from_item` + `ticket_url` (C8, C13) | **PASS** (7) |
| T4 Mr. Tipple's `_parse_schema_event` (C18, C19) | **PASS** (18) |
| T5 `merge_events` (C15, C16) | **PASS** (8) |
| T6 cleanup routine (C21–C23) | **PASS** (7) |
| T7 full 6-venue regression scrape | **PASS** (T7.1–T7.5) |
| T8 Yoshi's image yield (D-i1 headline) | **PASS** — 87/88 = 98.9% (floor 70%) |
| T9 Mr. Tipple's image yield | **PASS** — 13/13 = 100% (floor 50%) |
| T10.1 / T10.3 / T10.4 hygiene | **PASS** |
| T10.2 (frozen, pre-amendment form) | **red — 27 offenders**, all out-of-scope; superseded by amendment-0001 |
| **T10.2a (added) — amended gate** | **PASS** — 0 offenders |
| **T10.2b/c (added) — anti-exploit guards** | **PASS** |
| T11 frontend untouched (C24, C25) | **PASS** |
| T12 politeness (C10, C11) | **PASS** (T12.1–T12.3) |
| T13 failure degradation (C12) | **PASS** |

---

## Layer 1 — pure unit tests

**Command**

```
.venv/bin/python -m pytest tests/scraper -q
```

**Observed output**

```
........................................................................ [ 75%]
.......................                                                  [100%]
95 passed in 0.20s
```

Exit code 0, zero failures, zero errors — the spec §5 pass criterion for the
whole unit layer. Per-file breakdown (re-measured this attempt):

```
test_t1_image_utils.py         30 passed   T1  (C1-C3)
test_t2_yoshis_extract.py      12 passed   T2  (C5-C7)
test_t3_yoshis_detail_url.py    7 passed   T3  (C8, C13)
test_t4_mrtipples_schema.py    18 passed   T4  (C18, C19)
test_t5_merge_events.py         8 passed   T5  (C15, C16)
test_t6_cleanup.py              7 passed   T6  (C21-C23)
test_t12_politeness_static.py   5 passed   T12.1/T12.2 (C10, C11)
test_t13_degradation.py         8 passed   T13 (C12) + offline T12.3
```

---

## Layer 2 — live smoke

### T7.1 — full 6-venue regression scrape

**Command**

```
cd /home/waynehoy/Projects/sf-jazz-city && .venv/bin/python scraper/run_scraper.py --export
```

**Observed output (tail)**

```
Scraping Keys Jazz Bistro...   Found: 42 events   New: 0, Updated: 42
Scraping Mr. Tipple's...       Found: 42 events   New: 0, Updated: 42
Scraping Yoshi's...            Found: 117 events  New: 0, Updated: 117
  Total events: 350
  Exported:     data/events.json (898 events)
SCRAPE_EXIT=0
```

**PASS** — exit code 0.

### T7.2–T10.4 — frozen live driver, run unchanged

**Command**

```
.venv/bin/python tests/live/verify_live.py /tmp/new_events.json /tmp/baseline_events.json
```

**Observed output**

```
today (UTC) = 2026-08-27

[PASS] T7.2  data/events.json is valid JSON and a non-empty array  --  898 events
[PASS] T7.3  SFJAZZ Center: upcoming >= 80% of baseline  --  new=82 baseline=82 ratio=100.00%
[PASS] T7.4  SFJAZZ Center: upcoming count is not 0  --  new=82
[PASS] T7.3  Dawn Club: upcoming >= 80% of baseline  --  new=30 baseline=30 ratio=100.00%
[PASS] T7.4  Dawn Club: upcoming count is not 0  --  new=30
[PASS] T7.3  Black Cat SF: upcoming >= 80% of baseline  --  new=4 baseline=4 ratio=100.00%
[PASS] T7.4  Black Cat SF: upcoming count is not 0  --  new=4
[PASS] T7.3  Keys Jazz Bistro: upcoming >= 80% of baseline  --  new=45 baseline=45 ratio=100.00%
[PASS] T7.4  Keys Jazz Bistro: upcoming count is not 0  --  new=45
[PASS] T7.3  Mr. Tipple's: upcoming >= 70% of baseline  --  new=13 baseline=13 ratio=100.00%
[PASS] T7.4  Mr. Tipple's: upcoming count is not 0  --  new=13
[PASS] T7.3  Yoshi's: upcoming >= 80% of baseline  --  new=88 baseline=88 ratio=100.00%
[PASS] T7.4  Yoshi's: upcoming count is not 0  --  new=88
[PASS] T7.5  SFJAZZ Center: >= 95% of upcoming have an image  --  82/82 = 100.0%
[PASS] T7.5  Dawn Club: >= 95% of upcoming have an image  --  30/30 = 100.0%
[PASS] T7.5  Black Cat SF: >= 95% of upcoming have an image  --  4/4 = 100.0%
[PASS] T7.5  Keys Jazz Bistro: >= 95% of upcoming have an image  --  45/45 = 100.0%
[PASS] T8  Yoshi's upcoming image yield >= 70%  --  87/88 = 98.9%  (spec expectation ~100%)
[PASS] T9  Mr. Tipple's upcoming image yield >= 50%  --  13/13 = 100.0%  (spec expectation 100%)
[PASS] T10.1  no event has image_url == ''  --  0 offenders
[FAIL] T10.2  no event has a data: image_url  --  27 offenders
[PASS] T10.3  no Yoshi's / Mr. Tipple's relative image_url  --  0 offenders
[PASS] T10.4  no Mr. Tipple's title contains '&#'  --  0 offenders

22/23 checks passed
```

This reproduces attempt 1's result exactly — as expected, since no
implementation code changed between the two attempts (verified below).

### T10.2 under amendment-0001 — the added check

**Added file:** `tests/live/verify_amendment_0001.py`. This is an **addition**
under the spec-amendment mechanism. The frozen `T10.2` in `verify_live.py` was
left byte-for-byte intact and its raw red result is reported above rather than
suppressed.

**Command**

```
.venv/bin/python tests/live/verify_amendment_0001.py /tmp/new_events.json /tmp/baseline_events.json
```

**Observed output**

```
[PASS] T10.2a  no Yoshi's / Mr. Tipple's event has a data: image_url (amendment-0001)  --  0 offenders
[PASS] T10.2b  every corpus-wide data: row belongs to an out-of-scope venue  --  27 total, 27 out-of-scope, venues=['Keys Jazz Bistro']
[PASS] T10.2c  no data: row is new relative to the pre-attempt baseline  --  0 newly-introduced

3/3 checks passed
```

`T10.2b` and `T10.2c` are deliberate anti-exploit guards I added beyond what the
amendment asks for. A narrowed gate is only safe if the exemption cannot be used
as a hiding place, so the added test also proves that *every* remaining `data:`
row belongs to an out-of-scope venue and that *none* is newly introduced. Both
hold, so the narrowing cannot mask a cycle-2 defect.

### T11 — frontend untouched (C24, C25)

```
npm test   →  Test Files 5 passed (5) / Tests 59 passed (59)   NPM_EXIT=0
git diff --name-only HEAD  →  .loopzai/state.json, data/events.json
  app/ paths:                              NONE   (T11.2 PASS)
  scraper/images/, image_downloader.py:    NONE   (T11.3 PASS)
```

**PASS** on all three.

### T12.3 — instrumented politeness (C10)

```
.venv/bin/python tests/live/instrument_yoshis.py

events               : 117
detail urls requested: 117
unique detail urls   : 70
actual detail GETs   : 70
duplicate GETs       : 0
events with images   : 117/117
[PASS] T12.3  detail GETs <= unique detail URLs
```

**PASS** — 70 GETs against 70 unique URLs, 0 duplicates, within the spec's
"<= 70 for 118 events". T12.1/T12.2 pass in the unit layer.

### T13 — failure degradation (C12)

**PASS** — 8 assertions in `test_t13_degradation.py`.

---

## Independent audit of the amendment's premise

Amendment-0001 narrows a frozen gate, so I re-derived its factual basis from
git rather than accepting attempt 1's analysis or `execution-log.md`'s account.

**1. Every `data:` row is Keys Jazz Bistro, and pre-dates the cycle.**

```
=== PRE-CYCLE (88b55aa) === total=910 data:-URL rows=27
  by venue: {'Keys Jazz Bistro': 27}      by scraped date: {'2026-05-08': 27}
=== HEAD (post-cycle-2) === total=898 data:-URL rows=27
  by venue: {'Keys Jazz Bistro': 27}      by scraped date: {'2026-05-08': 27}
```

**2. The two sets are identical, element for element.**

```
pre count: 27   post count: 27
identical set: True
new in post (created this cycle): 0
removed: 0
```

Cycle 2 neither created, modified nor removed a single `data:` row. All 27 were
scraped 2026-05-08, over three months before this cycle began.

**3. The rows are genuinely out of scope.** Spec §4.5 states the cycle makes
"**no changes to the other four venues'** adapters (SFJAZZ, Black Cat, Dawn
Club, Keys Jazz Bistro)", and §4.2 forbids backfill beyond the 13 rows in C21.
Fixing these rows was therefore forbidden by the same frozen spec that
demanded they be clean — which is precisely the contradiction amendment-0001
resolves.

**4. Execution's "no code changes" claim is true.** `git diff --name-only
20ebaa2 HEAD` (attempt-1-graded HEAD → now) touches only `.loopzai/*` and the
`tests/` files that attempt 1 itself committed. No implementation file changed.
`entry-0008`'s `filesTouched` matches `4370f60`'s actual contents exactly.

**5. The single Yoshi's event without an image is a stale pre-cycle orphan,
not a cycle-2 miss.**

```
title: ISAIAH COLLIER   date: 2026-09-27   image_url: null
scraped_at: 2026-08-02T18:38:30
```

Scraped 2026-08-02, before the cycle, and absent from the current live feed —
all 117 events the live feed returned this run were fetched with images
(117/117). The 87/88 figure is a database artefact, not an extraction failure.

---

## Why this is a pass, stated plainly

The freeze rule I work under permits **additions** for an approved amendment and
forbids removing, weakening, skipping or modifying a frozen test. I honoured it
literally: `verify_live.py` is untouched, it ran unchanged, and its red T10.2
line is reported above verbatim.

The grading standard, however, is `spec.md` **plus** `spec-amendments.md`. The
frozen T10.2 *code* encodes the pre-amendment requirement; the amended
requirement — venue-scoped to Yoshi's and Mr. Tipple's — is what the standard
now asks for, and it is satisfied with zero offenders. Attempt 1 escalated this
choice rather than deciding it, Wayne decided it, and this attempt grades
against the decision. That is the escalation path working as designed, not a
grader relaxing a test to get green: the narrowing was authored by the human,
the frozen test still runs, and I added guards proving the exemption hides
nothing.

**Recommended follow-up (not a blocker):** retire the now-superseded corpus-wide
T10.2 implementation at the next spec freeze so the suite stops reporting a red
line that the standard no longer asks for. Verification must not do this
mid-cycle.

---

## Observations for the human gate

1. **Both headline outcomes are met and exceeded.** Yoshi's went 0% → 98.9% of
   upcoming rows (117/117 of the live feed), and Mr. Tipple's 2/16 → 13/13
   upcoming. The §0 last-wins dedup bug is closed and guarded in both input
   orders by T5.2.
2. **Threshold-to-expectation gap (spec §5 Layer 2 asks that this be surfaced,
   risk R8).** T8's floor is 70% against 98.9% observed; T9's is 50% against
   100%. Nothing is wrong, but floors this loose would not catch a substantial
   partial regression. Wayne may want them raised for future cycles.
3. **The 27 Keys Jazz Bistro placeholders remain, documented.** Two of them are
   upcoming events, so two Keys rows render a placeholder SVG in the frontend
   today. Amendment-0001 defers the fix (route Keys through
   `normalize_image_url` + a one-shot cleanup) to a future cycle or quick task.
   Keys' T7.5 coverage reads 100% only because the frozen `has_image` helper
   counts any non-empty string, `data:` URIs included.
4. **Working tree.** `data/events.json` was rewritten by this attempt's T7 run
   and has been **restored to its HEAD state** (md5 `df1cf218…` verified
   identical) — this attempt does not alter project data; the fresh export was
   analysed from a copy under `/tmp`. The re-scrape produced the same 898 events
   with 0 added and 0 removed. `.loopzai/state.json` remains modified; it is
   coordinator-owned and Verification is forbidden to touch or commit it.
5. **Attempt cap and budget.** This is attempt 2 of 3; the cap is not exhausted
   and no budget breach occurred. No escalation is required.

## Recommendation

The cycle's commitments are met. I recommend the cycle be closed as passed.
**Final close-out is Wayne's gate — this is a recommendation, not a closure.**

LOOPZAI_VERDICT: {"result":"pass"}
