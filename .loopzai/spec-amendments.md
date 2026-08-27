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
