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

## Testable surface area (input to Verification plan)
- `/venues` renders all 6 venues, each linking to `/venues/<slug>`
- `/venues/<slug>` renders venue name + its upcoming events (subset of `/api/events`)
- Header "Venues" link resolves to `/venues`
- Card venue names link to `/venues/<slug>`
- Zero-event venue → page still renders with explicit empty state
- Existing event list behavior unchanged (search/filter regressions)
