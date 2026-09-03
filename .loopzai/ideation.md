# Cycle 3 Ideation — SF Jazz History page

## Goal

Add a long-form editorial article page to the SF Jazz City site. The page
presents Wayne's essay "The Rhythms of the City: A History of San Francisco
Jazz" as a permanent, readable part of the site — giving it editorial depth
beyond the events calendar.

## What we are building

### Route
`/history` — a new Next.js App Router page at `app/history/page.tsx`.

### Navigation
Add a fourth link — **"SF Jazz History"** — to `SiteHeader`'s existing nav
alongside Tonight, Upcoming, and Venues. Nav is desktop-only (`hidden md:flex`)
and stays that way; mobile nav treatment is deferred to a future cycle.

### Content storage
The essay is stored as a markdown file at `app/history/essay.md`. The page
reads it at build time using `fs.readFileSync` so there is no runtime overhead.
This makes future essay edits a simple file change with no component surgery.

### Rendering
Add `react-markdown` (one new dependency). The page passes the essay string to
`<ReactMarkdown>` with a custom `components` map that applies Tailwind classes
to each element type — no `@tailwindcss/typography` plugin needed.

### Visual design
- Outer wrapper: site's normal `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`
- Reading column: `max-w-2xl mx-auto` — centered, prose-width
- Container card: `bg-black/30 backdrop-blur-md border border-white/10 rounded-xl`
  (same treatment as the header glass)
- H1 (essay title): large, `text-white font-bold`
- H2 section headings: `text-amber-400 font-semibold` — matches site accent color
- Body paragraphs: `text-gray-200 leading-relaxed`
- Paragraph spacing: `mb-4` or equivalent
- No hero image, no byline, no attribution — essay stands on its own
- Page `<title>` / metadata: "SF Jazz History — SF Jazz City"

## What we are NOT building
- Mobile nav treatment (deferred)
- CMS or admin editing surface
- Hero banner or decorative imagery
- Author attribution or byline
- Comments or sharing features

## Open questions / assumptions for Execution
- `react-markdown` latest stable version to be installed; no pinning required
- Essay filename `essay.md` is fixed; path is relative to `app/history/`
- No new Convex schema changes — this is a pure frontend addition
- No new test fixtures required beyond a basic render smoke test confirming the
  page loads, the nav link appears, and the essay title renders

## Specification gate feedback (cycle 3, rejected 2026-09-03T22:15:46.218Z)

§5 states that no other file may be created or modified, but §6 requires creating tests/history.test.tsx. Amend §5 to explicitly allow tests/history.test.tsx. Make no other substantive changes to the specification.
