<!-- verification.md — verification results for the current cycle. -->

# Cycle 2 — Verification attempt 1 of 3

**Graded against:** `.loopzai/spec.md` §5 (frozen at approval) +
`.loopzai/spec-amendments.md` (empty — no amendments this cycle).
**Executable tests frozen at:** commit `667f93a`
(`loopzai: cycle 2 - freeze executable test suite (spec section 5)`).
**Repo HEAD graded:** `20ebaa2`. **Run date (UTC):** 2026-08-27.

Tests were derived from `spec.md` alone and committed **before**
`execution-log.md` or the implementation diff were read.

---

## Verdict summary

**FAIL — 1 frozen check of 24 live checks fails.** The unit layer is fully
green (95/95) and every image-yield, politeness, degradation and scope
commitment holds. The single failure is **T10.2**, and it is **not caused by
this cycle's implementation** — see §"Failure hypothesis".

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
| T10 post-run data hygiene | **FAIL** — T10.1 ✓, **T10.2 ✗**, T10.3 ✓, T10.4 ✓ |
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

Exit code 0, zero failures, zero errors — the spec's stated pass criterion for
the whole unit layer. Per-file breakdown:

```
tests/scraper/test_t1_image_utils.py         30 passed
tests/scraper/test_t2_yoshis_extract.py      12 passed
tests/scraper/test_t3_yoshis_detail_url.py    7 passed
tests/scraper/test_t4_mrtipples_schema.py    18 passed
tests/scraper/test_t5_merge_events.py         8 passed
tests/scraper/test_t6_cleanup.py              7 passed
tests/scraper/test_t12_politeness_static.py   5 passed
tests/scraper/test_t13_degradation.py         8 passed
```

### T1 — `normalize_image_url` (C1–C3) — PASS
All ten spec table rows assert exact equality and all pass, including the two
`data:` rejections, both `.svg` rejections (`/assets/placeholder.svg` and
`/assets/placeholder.SVG?v=2`, i.e. case-insensitive with a query string), the
protocol-relative `//cdn.example.com/a.jpg → https://cdn.example.com/a.jpg`
promotion and the unchanged-absolute passthrough. The spec's property
assertion (result is `None` or a `str` starting `http://`/`https://`) is run
over every row, plus an added C4 guard that every rejection is `None` and never
`""`.

### T2 — Yoshi's `extract_image_url` (C5–C7) — PASS
All ten spec sub-cases pass:
`yoshis_detail_with_image.html` →
`https://yoshis.com/userfiles/events/images/2866/keikomatsui2-copy.jpeg`
(exactly the string the Specification phase recorded from the live page);
`yoshis_detail_no_image.html` → `None`; the result contains neither
`yoshi-logo` nor `facebook.com/tr`; attribute order either way, a newline
inside the tag, and a multi-token `class="lazy event-img rounded"` all extract;
`class="event-image-wrapper"` correctly does **not** match (token test, not
substring); and a `data:` `src` on an `event-img` element returns `None`.

**Added check (fixture integrity).** The two HTML fixtures were captured by the
Execution phase (`execution-log.md` entry-0003, commit `771bc09`), so they were
not taken on trust. Two added tests assert the spec §5 "Fixtures" preconditions
mechanically: the with-image fixture retains the `img.event-img` element, the
`/images/yoshi-logo.png` logo `<img>`, the `facebook.com/tr` pixel `<img>` and
at least one tag with a newline inside it; the no-image fixture has the
`event-img` element removed while retaining the logo and the pixel. Both pass.
See §"Observations for the human gate" for the protocol note.

### T3 — `detail_url_from_item` + `ticket_url` non-regression (C8, C13) — PASS
Using the verbatim live item from the spec: `detail_url_from_item(item)` ==
`https://yoshis.com/events/sold-out/keiko-matsui-14/detail`; `_parse_event`
still yields `ticket_url ==
https://www.etix.com/ticket/p/69261880/keiko-matsui-wed82626-oakland-yoshis`
(the etix URL, **not** the detail URL — this is R6, the cycle's most likely
silent regression, and it is clean); `title == "KEIKO MATSUI"`;
`date == "2026-08-26"`; `time == "7:30 PM"`; `detail_url_from_item({})` and
`{"url": ""}` are both `None`; `{"url": "/events/x/detail"}` absolutizes; and a
`Sold Out` `className` still yields `status == "Sold Out"`.

### T4 — Mr. Tipple's `_parse_schema_event` (C18, C19) — PASS
All nine sub-cases pass — `str`/`list`(first element)/`dict`(`url`) image
shapes, absent image → `None`, `""` → `None` (not `""`), `data:` → `None`,
relative → absolutized against `https://mrtipplessf.com`, and both entity
decodings: `Patrick Wolff&#8217;s &#8220;Swinging Organ&#8221; Quartet` →
`Patrick Wolff’s “Swinging Organ” Quartet` and `Carla Helmbrecht &#038; The
Brad Leali Quartet` → `Carla Helmbrecht & The Brad Leali Quartet`. T4.10
(`"&#" not in event.title`) is parametrised across all nine cases.

### T5 — `merge_events` (C15, C16) — PASS
The core regression guard is green in **both** orders: `merge_events([A, B])`
and `merge_events([B, A])` each return length 1 with
`image_url == "https://h/a.jpg"`. The last-wins comprehension at the old
`mrtipples_scraper.py:321` is gone. Empty string counts as missing (both
orders); `time`/`price` fill-in works; distinct `(title, date)` keys are
preserved in both directions; `merge_events([])` is `[]`; idempotence holds.
An added test exercises all five spec-named fields (`image_url`, `time`,
`price`, `ticket_url`, `description`) taking first-non-empty in one pass.

### T6 — cleanup routine (C21–C23) — PASS
Against a temporary SQLite DB built with the project schema: the decoded twin
receives `https://h/r.jpg`; the twinned entity row is deleted; the entity row
**without** a twin survives untouched with its image (C22); the Dawn Club rows
— including one whose title contains `&#` — are byte-identical before and after
(C23); an added check confirms a Mr. Tipple's row **without** `&#` is untouched;
a second run changes nothing (idempotent); and total row count drops by exactly
1, the number of entity rows that had twins.

**Against the real project DB** (`scraper/events.db`, 898 rows): 0 Mr. Tipple's
rows with `&#`, 0 rows of any venue with `&#`. The one-shot cleanup landed.

---

## Layer 2 — live smoke

### T7 — full 6-venue regression scrape — PASS

**Command**

```
cd /home/waynehoy/Projects/sf-jazz-city && .venv/bin/python scraper/run_scraper.py --export
```

**Observed tail**

```
  Total events: 350
  New events:   0
  Updated:      350
  Exported:     data/events.json (898 events)
EXIT_CODE=0
```

**T7.1** exit code 0 — PASS.
**T7.2** valid JSON, non-empty array, 898 events — PASS.

**T7.3 / T7.4** — baseline is `git show HEAD:data/events.json`, both sides
computed with the same `today = 2026-08-27` (UTC), per the spec.

| Venue | new upcoming | baseline | ratio | floor | T7.3 | T7.4 |
|---|---|---|---|---|---|---|
| SFJAZZ Center | 82 | 82 | 100.0% | 80% | PASS | PASS |
| Dawn Club | 30 | 30 | 100.0% | 80% | PASS | PASS |
| Black Cat SF | 4 | 4 | 100.0% | 80% | PASS | PASS |
| Keys Jazz Bistro | 45 | 45 | 100.0% | 80% | PASS | PASS |
| Mr. Tipple's | 13 | 13 | 100.0% | **70%** | PASS | PASS |
| Yoshi's | 88 | 88 | 100.0% | 80% | PASS | PASS |

No venue is at 0. The Mr. Tipple's 45 → 42 merge collapse the spec anticipated
had already happened in Execution's export, so this attempt's ratio is 1.00
against it; the live adapter reported `Total unique events: 42 (37 with
images)`, matching the spec's §2 measurement exactly.

**T7.5** — the four healthy venues do not regress on images (floor 95%):
SFJAZZ 82/82 = 100%, Dawn Club 30/30 = 100%, Black Cat 4/4 = 100%,
Keys Jazz Bistro 45/45 = 100%. PASS.

### T8 — Yoshi's image yield (the D-i1 headline) — PASS

Among Yoshi's events with `date >= 2026-08-27`, the fraction whose `image_url`
is non-empty, starts `https://yoshis.com/`, and does not start `data:`:

```
[PASS] T8  Yoshi's upcoming image yield >= 70%  --  87/88 = 98.9%  (spec expectation ~100%)
```

98.9% clears the 70% floor and sits above the spec's "below ~90% warrants
investigation" line. The single miss was investigated anyway and is **not** an
extraction failure: it is a stale DB row `("ISAIAH COLLIER", 2026-09-27,
7:00 PM)` last scraped **2026-08-02**, before this cycle. Yoshi's has since
renamed the show, and the current row `("ISAIAH COLLIER: ‘COLLIER PLAYS
COLTRANE’", 2026-09-27, 7:00 PM)` was scraped today **with** its image
(`.../2849/isaiah-collier2-copy.jpeg`). The live run itself reported
`Total unique events: 117 (117 with images)` — 100% of everything the feed
currently serves. The stale row is the pre-existing "renamed show leaves an
orphan" phenomenon; spec §4.2 explicitly leaves historical rows alone.

### T9 — Mr. Tipple's image yield — PASS

```
[PASS] T9  Mr. Tipple's upcoming image yield >= 50%  --  13/13 = 100.0%  (spec expectation 100%)
```

100% of upcoming events carry an `https://` image. The §0 data-loss bug is
fixed.

### T10 — post-run data hygiene — **FAIL (T10.2)**

**Command**

```
cd /home/waynehoy/Projects/sf-jazz-city && .venv/bin/python tests/live/verify_live.py \
    <fresh data/events.json> <git show HEAD:data/events.json>
```

**Observed output**

```
[PASS] T10.1  no event has image_url == ''  --  0 offenders
[FAIL] T10.2  no event has a data: image_url  --  27 offenders
[PASS] T10.3  no Yoshi's / Mr. Tipple's relative image_url  --  0 offenders
[PASS] T10.4  no Mr. Tipple's title contains '&#'  --  0 offenders

22/23 checks passed
FAILURES:
  T10.2  no event has a data: image_url  --  27 offenders
```

**T10.1 PASS** — zero events of any venue have `image_url == ""` (C4 holds).

**T10.2 FAIL** — 27 events carry an `image_url` beginning `data:`. All 27 are
**Keys Jazz Bistro**; zero are Yoshi's or Mr. Tipple's. Sample:

```
Keys Jazz Bistro 2013-02-20 Attakid                       | data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewB…
Keys Jazz Bistro 2026-05-08 Janice Maxie Reid             | data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewB…
Keys Jazz Bistro 2026-05-09 Paula West                    | data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewB…
Keys Jazz Bistro 2026-05-09 Late Set: Simon Rowe Organ Trio | data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewB…
```

Date range 2013-02-20 → 2027-03-19; 2 of the 27 are upcoming. These are
WordPress lazy-load placeholder SVGs captured by `scraper/keysjazz_scraper.py`.

**They are pre-existing and identical across all three snapshots** — counted
mechanically:

| Snapshot | `data:` offenders | venues |
|---|---|---|
| Pre-cycle-2 baseline (`88b55aa:data/events.json`) | 27 | Keys Jazz Bistro ×27 |
| Execution's export (`HEAD:data/events.json`, `ea6c9ec`) | 27 | Keys Jazz Bistro ×27 |
| This attempt's fresh scrape | 27 | Keys Jazz Bistro ×27 |

Cycle 2 neither introduced, worsened, nor was committed to fix this. Full
analysis in §"Failure hypothesis".

**T10.3 PASS** — no Yoshi's or Mr. Tipple's event has a relative `image_url`;
every non-null value starts `http://` or `https://` (C3/C4 hold on both
in-scope venues).

**T10.4 PASS** — no Mr. Tipple's title contains `&#` in `data/events.json`, and
independently 0 such rows remain in `scraper/events.db` (C18 + C21).

### T11 — frontend untouched (C24, C25) — PASS

**T11.1** `npm test`:

```
 Test Files  5 passed (5)
      Tests  59 passed (59)
   Duration  1.89s
EXIT_CODE=0
```

(This also confirms the spec's claim that Vitest's include glob does not pick
up the new `.py`/`.html` files — the count is unchanged from cycle 1's 59.)

**T11.2 / T11.3** `git diff --name-only HEAD` at grading time lists only
`.loopzai/state.json` and `data/events.json` (the latter from this attempt's
own T7 run, since restored) — **no** path starting with `app/`, **no** path
starting with `scraper/images/`, and not `scraper/image_downloader.py`. PASS.

**Added check — whole-cycle scope integrity.** Because `git diff HEAD` only
sees uncommitted work, the commitments were also checked across the entire
cycle-2 diff (`88b55aa..HEAD`). Changed files:

```
.loopzai/{assumptions,execution-log,ideation,spec,state}.md/.json
.loopzai/interventions.jsonl, .loopzai/milestones.json
data/events.json
scraper/__init__.py, scraper/cleanup.py, scraper/image_utils.py
scraper/mrtipples_scraper.py, scraper/requirements.txt, scraper/yoshis_scraper.py
tests/fixtures/scraper/yoshis_detail_{no_image,with_image}.html
```

Zero paths under `app/`, zero under `scraper/images/`, and
`scraper/image_downloader.py` untouched — **C24 and C25 hold for the whole
cycle**, not merely for the working tree.

**C26** — the entire `scraper/requirements.txt` diff for the cycle is:

```
+
+# Test runner for the scraper unit tests (tests/scraper/)
+pytest>=8
```

One dependency added, and it is `pytest>=8`. PASS.

### T12 — politeness (C10, C11) — PASS

**T12.1** static: `scraper/yoshis_scraper.py` contains exactly one
`asyncio.Semaphore(4)`; 4 ≤ 4. An added assertion confirms it is actually used
as an `async with` guard rather than merely constructed. An added assertion
confirms the request timeout is ≤ 30 s (`ClientTimeout(total=DETAIL_TIMEOUT_SECONDS)`
resolves to 20 s; the calendar POST uses 30 s).

**T12.2** static: exactly one `aiohttp.ClientSession(` construction in the
module, and the detail-fetch helpers take a `session` parameter rather than
opening their own. Confirmed dynamically in the offline harness: one session
instance served 1 POST and all GETs.

**T12.3** instrumented live Yoshi's-only run
(`.venv/bin/python tests/live/instrument_yoshis.py`, writing to a scratch DB):

```
events               : 117
detail urls requested: 117
unique detail urls   : 70
actual detail GETs   : 70
duplicate GETs       : 0
events with images   : 117/117
[PASS] T12.3  detail GETs <= unique detail URLs
```

70 GETs for 117 events against 70 unique URLs, zero duplicates — the per-URL
cache of C10 is real, and the count matches the spec's "<= 70 for 118 events"
expectation.

### T13 — failure degradation (C12) — PASS

Run offline: `aiohttp.ClientSession` is replaced inside the `yoshis_scraper`
namespace by an in-memory fake serving a 3-event / 2-unique-URL calendar
payload, so no socket is opened.

- Baseline, detail fetching disabled: 3 events, all `image_url is None`.
- **`fetch_detail_images` monkeypatched to raise on every call:** `scrape_events()`
  returns the same 3 events, every `image_url is None`, **no exception
  propagates**.
- Per-URL `fetch_detail_image` monkeypatched to raise: same result.
- Detail pages returning HTTP 503: same result.
- Happy path through the same harness: all 3 events carry the extracted image
  (C9), and `ticket_url` stays the etix URL for both shows while the `Sold Out`
  status survives (C13 end-to-end).

---

## Failure hypothesis

**Why T10.2 failed.** The frozen test plan states T10.2 without venue
qualification — "No event has an `image_url` starting with `data:`" — in
deliberate contrast to T10.3 and T10.4, which are explicitly scoped to Yoshi's
and Mr. Tipple's. Read as written, it is a whole-corpus hygiene gate over
`data/events.json`.

But 27 rows already violated that gate **before cycle 2 began**. They are all
Keys Jazz Bistro, and they are byte-identical in the pre-cycle baseline
(`88b55aa:data/events.json`, committed 2026-08-26 before cycle 2 opened),
in Execution's export, and in this attempt's fresh scrape. They come from
`scraper/keysjazz_scraper.py` capturing the WordPress lazy-load placeholder
SVG (`data:image/svg+xml,…`) instead of the real `src`.

Cycle 2 owns neither the adapter nor those rows:

- Spec §4.5 — "**No changes to the other four venues' adapters** (SFJAZZ, Black
  Cat, Dawn Club, Keys Jazz Bistro). They are at 100% image coverage; they are
  regression surface only."
- C2/C4 constrain `normalize_image_url` and the **two in-scope adapters**;
  `keysjazz_scraper.py` never calls it and was never asked to.
- C21–C23 bound the DB cleanup to exactly the 13 Mr. Tipple's entity rows.

The gate was never satisfiable by anything cycle 2 committed to. It went
unnoticed at specification time because §2's ground-truth table counts a
non-empty `image_url` as "has an image", so Keys Jazz Bistro's 2 upcoming
placeholder SVGs were tallied as images (46/46) and the `data:` values were
never separated out.

**This is a defect in the frozen test plan's scope, not in the
implementation.** Per the frozen-test rules the test was not weakened, skipped
or modified — it is reported as-is, and it fails.

## What must change

Neither available resolution is something the next Execution pass may do on its
own authority; both require Wayne.

- **Option A (recommended, minimal) — amend T10.2 to match the cycle's actual
  reach.** Add to `.loopzai/spec-amendments.md` an approved amendment scoping
  T10.2 to Yoshi's and Mr. Tipple's, matching T10.3/T10.4 and the reach of
  C2/C4, and (optionally) recording the 27 pre-existing Keys Jazz Bistro
  `data:` rows as known, accepted, out-of-scope debt for a later cycle. No code
  changes. Under this amendment the cycle's commitments are met as they stand:
  every other frozen check is already green.
- **Option B (wider) — bring Keys Jazz Bistro into scope.** Route
  `keysjazz_scraper.py`'s image through `normalize_image_url` (which already
  rejects `data:` per C2, so this is a small wiring change), and extend the
  one-shot cleanup to null out the 27 existing placeholder rows. This
  contradicts spec §4.5 and widens C21–C23 beyond their stated 13 rows, so it
  needs an approved amendment **expanding scope**, and would put the cycle's
  T7.5 Keys Jazz Bistro image-coverage floor (95%) at risk — nulling 2 upcoming
  placeholders takes Keys from 45/45 to 43/45 = 95.6%, which still clears, but
  only just.

An Execution retry that silently edits `keysjazz_scraper.py` without an
amendment would breach C24–C26 scope integrity and must be failed by the next
grader.

## Expected outcome of the retry

- **Under Option A:** no code changes. The next Verification attempt re-runs the
  frozen suite from commit `667f93a` unchanged, adds the amendment-scoped T10.2
  variant, and should observe 95/95 unit assertions and 24/24 live checks green
  — a clean pass. The 27 Keys Jazz Bistro rows remain, documented.
- **Under Option B:** `tests/scraper/` stays frozen and still passes 95/95; the
  live layer should then show 0 `data:` offenders corpus-wide, Keys Jazz Bistro
  upcoming image coverage at 43/45 = 95.6% (still ≥ 95%, T7.5 marginal — flag
  it), and every other check unchanged. New unit coverage for the widened
  cleanup would be **added** to the frozen suite, never substituted for it.

## Observations for the human gate

1. **The implementation itself is sound.** Every commitment C1–C26 that this
   attempt could test independently holds. The two headline outcomes are met
   and then some: Yoshi's went 0% → 100% of the live feed (117/117 fetched
   with images; 98.9% of upcoming rows once one stale pre-cycle orphan is
   excluded), and Mr. Tipple's went 2/16 → 13/13 upcoming. The §0 last-wins
   dedup bug is closed and guarded in both input orders by T5.2.
2. **Spec §5 Layer 2 asks that a large threshold-to-expectation gap be
   surfaced, not silently passed** (risk R8). Both live yield thresholds are far
   below what was measured: T8's floor is 70% against 98.9% observed, T9's is
   50% against 100%. Nothing is wrong, but the floors would not catch a
   substantial partial regression, and Wayne may want them raised for future
   cycles.
3. **Protocol note on the T2 fixtures.** Spec §8 rejects "write the tests as
   part of Execution", yet the two HTML fixtures named in §5 were captured and
   committed by Execution (entry-0003 / `771bc09`). They are input data rather
   than assertions and the spec names them explicitly, so this is not scored as
   a violation — but they were not taken on trust: two added tests assert all
   four §5-required elements mechanically, and the URL T2.1 expects matches the
   value the Specification phase independently recorded from the live page.
4. **Execution log audited against git.** All seven `commitSha` values in
   `execution-log.md` resolve, and the `filesTouched` lists match the actual
   commit contents exactly (verified per-commit with `git show --name-only`).
   Entry-0007's `commitSha` `6492cc9` is the commit that carries that entry,
   and the follow-up correction it describes is carried by the trailing commit
   `fe2c352` — as the entry itself states.
5. **Working tree.** `data/events.json` was rewritten by this attempt's T7 run
   and has been **restored to its HEAD state** (md5 verified identical) — this
   attempt does not alter project data. The fresh export was analysed from a
   copy. `.loopzai/state.json` remains modified (`attempt 0 → 1`); it is
   coordinator-owned and Verification is forbidden to touch or commit it.
6. **Cost/budget.** Well inside the spec §6 estimate (50–85 min for
   Verification). No budget breach; the attempt cap is not exhausted — this is
   attempt 1 of 3.

## Recommendation

The cycle's engineering work looks complete and correct. The blocker is a
scope mismatch in the frozen test plan, which Verification may not resolve
unilaterally. **Wayne's call is needed to approve Option A or Option B before
attempt 2 can be graded**, since a retry with no amendment would re-run the
same unsatisfiable gate and fail identically. Final close-out remains Wayne's
gate regardless.

LOOPZAI_VERDICT: {"result":"fail","hypothesis":"Frozen test T10.2 (unqualified: no event of any venue may have a data: image_url) fails on 27 pre-existing Keys Jazz Bistro lazy-load placeholder SVG rows that are byte-identical in the pre-cycle baseline; the Keys adapter is explicitly out of scope per spec 4.5 and no cycle-2 commitment covers it, so the gate was never satisfiable and resolution needs an approved spec amendment (scope T10.2 to the two in-scope venues, or widen scope to include keysjazz_scraper.py) rather than an Execution code fix."}
