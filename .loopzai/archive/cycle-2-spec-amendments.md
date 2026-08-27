<!-- spec-amendments.md — human-approved deltas to the frozen spec; live for the current cycle. -->

## Cycle 2 — amendment-0001 (mid-cycle, post-freeze, 2026-08-27)

**Trigger:** Verification attempt 1 returned FAIL on frozen gate **T10.2**
("no event of *any* venue carries a `data:` image URL") because 27
pre-existing `data:` image URLs exist in Keys Jazz Bistro rows scraped
2026-05-08 — rows no cycle-2 commitment covers (`keysjazz_scraper.py` is
explicitly out of scope per spec §4.5, and removing the data would violate
§4.2 no-backfill and C23). T10.2, written unqualified, was **never
satisfiable by anything this cycle promised** — it slipped through
Specification because §2's ground-truth table counted any non-empty
`image_url` (including the 2 upcoming Keys placeholders) as an image.
Execution flagged this pre-cycle-close as **assumption-0004**; Verification
correctly refused to weaken the frozen test and escalated the choice.

**Decision (Wayne, 2026-08-27):** Option A — scope the gate.

**Amendment:** T10.2's prohibition on `data:` image URLs applies to events
of the **cycle-2 in-scope venues — Yoshi's and Mr. Tipple's — only**, matching
the venue-scoped formulation of T10.3/T10.4. The 27 legacy Keys Jazz Bistro
placeholder rows are documented pre-existing data, explicitly out of scope
for this cycle; cleaning them up (routing Keys through `normalize_image_url`
+ a one-shot cleanup) is deferred as future-cycle / quick-task material.

**Effect on the frozen suite:** the T10.2 implementation reads the amendment
as its authority (per the spec-amendment mechanism) and asserts the
prohibition over Yoshi's + Mr. Tipple's events only. No other test changes;
no code changes required. Verification attempt 2 is expected to pass clean
with all other §6 checks already green.

**Effect on assumptions:** resolves **assumption-0004** as accepted-decided
(this amendment is the decision). assumption-0001–0003 remain queued for the
close-out review as normal.

## Amendment — assumption assumption-0001 approved (cycle 2, 2026-08-27T16:19:36.529Z)

**Undecided:** spec.md §5 names two Yoshi's HTML fixtures under `tests/fixtures/scraper/` and the live URL they come from, but does not say whether Execution or Verification captures them.
**Chosen:** Execution captures both now, byte-verbatim from the live page (no trimming, no hand-editing), and derives `yoshis_detail_no_image.html` by the single mechanical deletion the spec describes (remove the `event-img` element, change nothing else). All assertions and test code are left entirely to Verification.
**Why:** The source page is a *past* show (2026-08-26, i.e. yesterday); it still returns HTTP 200 today but is liable to 404 once Yoshi's prunes it, which would make the frozen T2 unimplementable in a later session. Capturing raw HTML preserves the artifact without authoring any test or shaping any expected value.
**Wrong if:** the Loop protocol counts fixture data as part of the test artifact that a fresh Verification session must produce independently — in which case Verification should delete and re-capture these two files (they are inputs only, so nothing else depends on them). Also wrong if a reviewer wants the 166 KB pages trimmed before commit; spec §5 permits trimming but does not require it, and trimming is the step most likely to accidentally shape the fixture.

## Amendment — assumption assumption-0002 approved (cycle 2, 2026-08-27T16:19:36.529Z)

**Undecided:** spec.md C21 requires "a one-shot, idempotent maintenance routine" but names no module, file or function for it, while T6 must import and run it offline against a temporary DB.
**Chosen:** `scraper/cleanup.py`, exporting `cleanup_entity_titles(db_path: str = "scraper/events.db") -> dict`, also re-exported from `scraper/__init__.py` and runnable as `python -m scraper.cleanup --db <path>`. It returns a stats dict (`examined`, `images_copied`, `deleted`, `orphans`, `foreign_twins`).
**Why:** A standalone module keeps a one-shot migration out of the adapter's hot path, and a `db_path` parameter is what makes T6's temp-DB run possible at all. The package re-export gives Verification an obvious import site.
**Wrong if:** Verification expects the routine inside `scraper/mrtipples_scraper.py` or under a different name and cannot find it (it is a plain rename away), or a reviewer objects to one-shot migrations being importable package API.

## Amendment — assumption assumption-0003 approved (cycle 2, 2026-08-27T16:19:36.529Z)

**Undecided:** how to resolve a conflict between spec.md C21 and spec.md T6 over what counts as the "decoded twin" of an entity title. C21 defines the twin as the row whose title equals `html.unescape(title)`, which for `&#8217;` is U+2019 (`’`). T6's illustrative fixture instead spells the twin `"Richard Howell's Sudden Changes"` with an **ASCII apostrophe** (U+0027), which `html.unescape` never produces.
**Chosen:** implemented C21 literally — the twin lookup is an exact match on `html.unescape(title)`. No ASCII-apostrophe fallback was added. A row whose only candidate twin differs by apostrophe character is therefore treated as having no twin and is left in place under C22.
**Why:** C21 is a commitment; T6's fixture string is an illustration, and the live data agrees with C21 — all 13 real entity rows in `scraper/events.db` matched a U+2019 twin and the cleanup collapsed them cleanly (13 examined, 12 images copied, 13 deleted, 0 orphans). Adding a fuzzy apostrophe fallback to satisfy a probable transcription artifact would widen the deletion rule beyond what was approved.
**Wrong if:** the ASCII apostrophe in T6 was deliberate, in which case the cleanup needs an explicit apostrophe-normalization step and C21 needs amending to say so. **Verification should be aware:** a T6 fixture that copies the spec's twin string byte-for-byte will see the entity row left in place (T6.1/T6.2 fail) — that is this spec conflict surfacing, not a defect in the routine. Building the fixture's twin as `html.unescape(entity_title)` exercises C21 as written.

## Amendment — assumption assumption-0004 approved (cycle 2, 2026-08-27T16:19:36.529Z)

**Undecided:** spec.md T10.2 asserts that in the exported `data/events.json` **no event of any venue** has an `image_url` starting with `data:`, but spec.md §4.2 forbids backfilling past rows, §4.5 forbids touching the other four venues' adapters, and C23 confines the cleanup to Mr. Tipple's. The post-run export contains 27 such rows.
**Chosen:** left them untouched and did not widen the cleanup. All 27 are **Keys Jazz Bistro** rows (25 past, 2 upcoming) carrying an inline `data:image/svg+xml,...` placeholder, all with `scraped_at = 2026-05-08`. They are stale DB rows: the Keys adapter's current run updated 42 events and did not rewrite any of them, and the identical 27 rows are present in the committed baseline `data/events.json` at HEAD. Neither adapter changed this cycle emits a `data:` URL — Yoshi's and Mr. Tipple's are both at zero (C2/C4 hold).
**Why:** Removing them would mean either editing another venue's rows (violating C23 and §4.5) or backfilling history (violating §4.2). The commitment that this cycle actually makes about `data:` URLs is C2/C4, which is scoped to the two adapters in play, and that is satisfied.
**Wrong if:** T10.2 was meant literally and globally, in which case this cycle cannot satisfy it without an amendment widening the cleanup to null out Keys Jazz Bistro's 27 placeholder `image_url`s (a ~3-line change, but out of the approved scope). **Verification should expect T10.2 to fail as written on pre-existing Keys Jazz Bistro data** and route it to the human gate as a spec conflict rather than an implementation defect.

## Amendment — assumption assumption-0005 approved (cycle 2, 2026-08-27T16:19:36.529Z)

**Undecided:** Whether this post-amendment Execution pass must re-run milestone M3's full 6-venue live scrape and refresh `data/events.json`, or may close against the export already committed at `ea6c9ec` (entry-0006).
**Chosen:** No re-scrape. `data/events.json` is left exactly as committed by entry-0006; this pass changes no project data.
**Why:** amendment-0001 resolves a test-scope mismatch and states "no code changes required", so nothing this pass touches could change scraper output; re-scraping would churn ~900 rows of committed data and re-expose the run to the live-site and Cloudflare risks in spec §7 (R1-R3) for no commitment-related gain. Verification's own attempt-1 T7 run already produced a fresh export from this code and found it green before restoring HEAD.
**Wrong if:** Verification attempt 2 re-runs T7 and finds a venue's upcoming count or image yield materially different from the committed export, indicating the committed data no longer reflects what this code produces — or if the close-out gate expects the shipped `data/events.json` to be dated at cycle close rather than at M3.
