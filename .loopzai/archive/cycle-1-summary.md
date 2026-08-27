# Cycle 1 Summary — Venues (plain English)

**What we built:** The venues feature the header nav always promised but never
delivered. The site now has a real `/venues` index page (one card per venue,
alphabetical, with show counts) and a real `/venues/[slug]` page for each of the
six venues (SFJAZZ Center, Black Cat SF, Dawn Club, Keys Jazz Bistro,
Mr. Tipple's, Yoshi's), listing that venue's events. Both dead interactions are
fixed: the header "Venues" link goes to a real route instead of a missing
`#venues` anchor, and every venue name on every event card is now a link to that
venue's page. Header and footer were extracted into shared components used by all
three pages. Homepage kept byte-identical frozen strings per the spec.

**Why this shape:** Wayne chose full venue pages (Option C from ideation) over a
minimal anchor fix: the scraper already yields per-venue data, so the pages have
a real reason to exist, and they're fully testable. Editorial content (photos,
neighborhood notes) was explicitly deferred to a future cycle.

**Key judgment calls (all 9 assumptions reviewed and accepted by Wayne):** venue
slugs are derived deterministically from names (`Mr. Tipple's` → `mr-tipple-s`)
rather than hardcoded; venue pages show the venue's whole scrape window (no
"upcoming only" cutoff, so a stale scrape can't silently empty a page); an
ESLint config was added because the spec required `npm run lint` to pass and the
repo had none; venue pages intentionally render two `<h1>` elements (one in the
shared header, one page-level) because both were explicit spec commitments.

**Test results:** Verification attempt 1: **PASS** — 59/59 assertions green in 5
vitest files (committed frozen at `8c5fa6c` before any implementation reading),
all 63 spec test IDs accounted for (56 vitest + 7 shell gates), plus build/lint/
tsc exits 0 on a clean `npm ci`. No amendments were needed. Human checks H1/H2
approved by Wayne at the cycle-close gate.

**Notable meta-point:** this cycle was also a LoopzAI dogfood — spec approval
and verification close-out both happened **in the Inbox UI**, and the Phase 12
reactive projections kept LoopzAI's loop view current throughout.

**What's next:** cycle 2 ideation — candidates discussed include editorial
content for venue pages (the deferred Option D), and whatever dogfooding
surfaces.
