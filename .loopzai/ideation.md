<!-- ideation.md — Ideation phase output; durable input to the Specification phase. -->

# Cycle 2 — Scraper image extraction: Yoshi's + Mr. Tipple's

## Problem (observed live, 2026-08-26)
Event cards on the site show fallback placeholder images for two venues:

- **Yoshi's: 0/205 rows all-time carry an `image_url`** — the adapter
  (`/home/waynehoy/Projects/sf-jazz-city/scraper/yoshis_scraper.py`) contains zero
  image-extraction code. Never implemented, not a regression.
- **Mr. Tipple's: 12/146 rows all-time** — extraction code exists (JSON-LD
  block + DOM `img` fallback) but yields rarely.

Healthy venues for contrast: SFJAZZ 82/82 upcoming-with-image, Dawn Club
31/31, Black Cat 5/5, Keys Jazz Bistro 44/46. The frontend hotlinks
`image_url` and falls back to a fixed Unsplash placeholder, so missing data
surfaces as "all placeholder graphics" on those venues' cards and pages.

## Scope (Wayne-approved decisions, 2026-08-26)
- **D-i1 — Both venues in scope.** Yoshi's (implement from scratch) and
  Mr. Tipple's (raise yield) get image extraction this cycle.
- **D-i2 — Per-event detail-page fetching is acceptable if needed.** The
  spec phase must first probe whether the data each adapter already consumes
  carries image fields (cheap path). If not, each adapter may fetch the
  event's detail page and take its primary artist image (e.g. `og:image`),
  politely (bounded concurrency, no parallelism beyond existing patterns).
- **D-i3 — Frontend unchanged.** The site, `/api/events`, `transformEvent`,
  and the placeholder fallback are untouched. This cycle changes scraper
  data capture only; the UI picks images up automatically through the normal
  scrape→merge→export pipeline.
- **D-i4 — No local-image wiring.** The `--images` downloader/
  `scraper/images/` pipeline stays as-is (unused by the frontend). Serving
  local images is out of scope.
- **D-i5 — No backfill ceremony.** Past rows stay as-is; upcoming events
  heal on the first post-fix scrape via the normal insert/update merge.

## Technical context for the Specification worker (verified today)
- Yoshi's adapter (143 lines) parses a structured listing feed
  (`_parse_event(item: dict)`) and never visits detail pages. Its detail
  URLs exist per event (`/events/.../detail`); detail pages carry standard
  metadata (the site serves og-style tags). The listing feed may or may not
  carry image fields — spec must probe and choose cheap-vs-detail path per
  venue, recording the choice as a decision.
- Mr. Tipple's adapter has two paths (JSON-LD primary, DOM `img` fallback);
  the low yield suggests the JSON-LD rarely carries images. The detail-page
  path of D-i2 is the likely fix here too.
- Monthly run today: Yoshi's 118 events found, Mr. Tipple's 45. Detail-page
  fetching roughly doubles request counts for these venues — acceptable per
  D-i2, but the scraper should remain a good citizen (sequential or small
  concurrency, existing retry/backoff patterns).
- Scraper writes land in `/home/waynehoy/Projects/sf-jazz-city/scraper/events.db`
  and export to `data/events.json` (deduped merge, safe to re-run).

## Verification shape (decided in ideation, to be refined in spec)
Two layers:
1. **Fixture-based parser unit tests** — committed sample markup/JSON per
   venue; deterministic tests proving image fields are extracted, SVG/data-URI
   placeholders are rejected, and missing images degrade to `null` (not
   garbage strings).
2. **ONE bounded live-smoke assertion at verification time** — a fresh
   full-venue scrape yields ≥70% of Yoshi's upcoming events and ≥50% of
   Mr. Tipple's upcoming events with real (non-placeholder) `image_url`s.
   These are targets verified live against the moving site, with the human
   gate as final arbiter — not CI-style blocking thresholds.

## Testable surface area (input to Verification plan)
- Fixture tests: Yoshi's parser extracts image from fixture; Mr. Tipple's
  parser extracts image from both JSON-LD and DOM-fallback fixtures
- Rejection: placeholder/data-URI/broken values never enter `image_url`
- Regression: full 6-venue scrape still succeeds end-to-end; per-venue event
  counts within normal variance of today's (no venue count collapses)
- Live-smoke: the two yield assertions above on a fresh scrape
- `data/events.json` post-run shows Yoshi's upcoming events carrying real
  image URLs (human eyeball via site or jq)
