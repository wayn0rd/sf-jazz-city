<!-- ideation.md — Ideation phase output; durable input to the Specification phase. -->

# Cycle 1 — Venues: Complete the Incomplete (Option C)

## Background / current state
The header nav has a **"Venues" link** pointing at `href="#venues"`, but no element on
the page carries that id — the link is dead. Each event card displays the venue
name as **plain text in a `<span>`**, not a link — clicking does nothing. Both are
unfinished work, not unbuilt features; Cycle 1 finishes them properly.

## Chosen shape: full venue pages (Option C of ideation discussion)
- **`/venues`** — venue index page: one card per venue (all 6 current venues),
  ordered deterministically (alphabetical), each card linking to its venue page.
- **`/venues/[slug]`** — one page per venue: venue name, plus the list of upcoming
  events at that venue (filtered from the same `/api/events` data source).
- Header "Venues" link → `/venues` (a real route, no dead anchor).
- Venue names on event cards → linked to the venue's `/venues/[slug]` page.

## Scope guardrails (what's NOT in this cycle)
- No editorial content (photos, vibe notes, neighborhood descriptions) — deferred
  to a future cycle's ideation (was Option D in discussion).
- No scraper changes.
- No changes to event data shape (`app/types/event.ts` unchanged — venue slug is
  derived from venue name at usage time).
- No new data pipelines; `/venues/[slug]` filters the existing `/api/events` payload.

## Why this shape (recorded from ideation discussion)
Options A (anchor fix only) and B (in-page section + anchor links) would technically
close the "dead link" bug but leave the feature hollow. Option C uses data we already
have (per-venue event lists via filter), is fully testable, and gives venue pages a
real reason to exist. Wayne approved Option C in chat 2026-08-26.

## Decisions already made in the ideation discussion (Wayne-approved)
The Specification worker should treat these as fixed inputs, not open questions:
- Real routes, no anchors: `/venues` index + `/venues/[slug]` detail; header
  "Venues" href changes from `#venues` to `/venues`.
- Data source: existing `/api/events` route only, filtered client-side. No new
  endpoints, no Convex, no scraper/data changes.
- Venue slug = pure deterministic function of the name: lowercase, any run of
  non-alphanumeric chars → single `-`, strip leading/trailing `-`. Fixtures:
  `SFJAZZ Center` → `sfjazz-center`; `Black Cat SF` → `black-cat-sf`;
  `Dawn Club` → `dawn-club`; `Keys Jazz Bistro` → `keys-jazz-bistro`;
  `Mr. Tipple's` → `mr-tipple-s`; `Yoshi's` → `yoshi-s`. Slug map derived
  from the live payload (distinct venue names), NOT hardcoded.
- `/venues` index: one card per venue, alphabetical by name, showing event
  count, linking to `/venues/<slug>`; reuse existing card visual language.
- `/venues/[slug]`: venue name h1 + that venue's events in the homepage
  event-card markup, sorted date asc then time asc (null time last). NO
  "upcoming only" date filter — the payload is already the scrape window,
  and a today-cutoff would silently empty pages after a stale scrape.
- Unknown slug → explicit not-found state with a link back to `/venues`
  (no blank page, no crash).
- Venue names on ALL event cards (homepage Tonight, homepage Browse, venue
  pages) become `<Link>`s to the venue's page.
- Header + footer extracted into shared components used by `/`, `/venues`,
  `/venues/[slug]`; Tonight/Upcoming nav links become `/#tonight`,
  `/#upcoming` so they work from any page.

## Testable surface area (input to Verification plan)
- `/venues` renders all 6 venues, each linking to `/venues/<slug>`
- `/venues/<slug>` renders venue name + its events (subset of `/api/events`),
  sorted date/time ascending
- Header "Venues" link resolves to `/venues`
- Card venue names link to `/venues/<slug>` (incl. venue-page self-links)
- Unknown slug → explicit not-found state
- Existing homepage behavior unchanged (search/date-filter regressions)
- Slug unit tests covering the six fixtures above + punctuation edge cases
