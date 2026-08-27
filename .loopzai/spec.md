<!-- spec.md — the frozen specification, once approved at the Specification gate. -->

# Cycle 1 Specification — Venues: Complete the Incomplete

**Status:** awaiting spec-approval gate
**Input:** `.loopzai/ideation.md` (frozen, Option C approved by Wayne 2026-08-26)
**Repo:** `sf-jazz-city` — Next.js 15.1.11 App Router, React 18, TypeScript, Tailwind 3

---

## 0. Read this first — one decision needs your veto or your nod

Ideation commits to two things that **cannot both be true**:

> "`/venues` — venue index page: one card per venue (**all 6 current venues**)"
> "Slug map derived from the **live payload** (distinct venue names), NOT hardcoded."

`/api/events` filters `event.date >= today` before returning. Measured against the
committed `data/events.json` on **2026-08-26**:

| Venue | events in file | events in live payload | last event date |
|---|---|---|---|
| Black Cat SF | 35 | **0** | 2026-08-07 |
| Dawn Club | 154 | 4 | 2026-08-29 |
| Keys Jazz Bistro | 135 | 13 | 2027-05-19 |
| Mr. Tipple's | 140 | 10 | 2026-09-06 |
| SFJAZZ Center | 81 | 3 | 2026-08-29 |
| Yoshi's | 181 | 64 | 2026-10-30 |

The live payload today contains **5 venues, not 6**. Black Cat SF has already aged
out. Dawn Club and SFJAZZ Center age out on 2026-08-30. The number is a function of
the wall clock and the staleness of the last scrape — it is not a fact about the
product.

**This spec resolves the conflict in favour of "derived from the live payload"** and
**drops the "all 6" count as a commitment.** The index renders exactly the set of
distinct venue names present in the payload, whatever that set is. See §C2.

Consequence you are approving: after a stale scrape, `/venues` may show fewer than 6
venues, or none. This is the same failure mode the homepage already has, made
visible. The alternative — reading `data/events.json` directly to get all 6 — needs a
new data path that ideation explicitly forbids ("no new endpoints… existing
`/api/events` route only").

**Veto target if you disagree:** §C2 and test T-C2-1. Everything else stands.

Two smaller deviations, same treatment — flagged so a veto can be aimed:

- **§C4 — brand links home.** Ideation didn't mention it. On a multi-page site the
  "SF Jazz City" wordmark linking to `/` is expected. Added as a testable
  commitment. Veto target: §C4, T-C4-4.
- **§C6 — venue pages use the *compact* card, not the *featured* one.** Ideation
  says "the homepage event-card markup"; the homepage has **two** card markups. The
  compact (Browse) variant shows the event date, which venue pages need because they
  span many dates. The featured (Tonight) variant omits the date. Veto target: §C6.

---

## 1. What ships

Six new/changed surfaces, one shared library, one test toolchain. Nothing else.

```
app/lib/venue-slug.ts        NEW   slug function
app/lib/event-order.ts       NEW   time parse + event comparator
app/lib/venues.ts            NEW   venue derivation from an event list
app/lib/format.ts            NEW   date formatters (moved verbatim from page.tsx)
app/components/SiteHeader.tsx NEW  shared header
app/components/SiteFooter.tsx NEW  shared footer
app/components/EventCard.tsx  NEW  shared event card, two variants
app/venues/page.tsx          NEW   /venues index
app/venues/[slug]/page.tsx   NEW   /venues/<slug> detail
app/page.tsx                 EDIT  consumes the shared components
package.json                 EDIT  test toolchain + "test" script
vitest.config.ts             NEW   test config
```

Unchanged, and Execution must not touch: `app/types/event.ts`,
`app/api/events/route.ts`, `data/`, `scraper/`, `app/layout.tsx`, `app/globals.css`,
`next.config.js`, `tailwind.config.js`.

---

## 2. Commitments

Each is falsifiable. Each has at least one test in §6.

### C1 — Slug function

`app/lib/venue-slug.ts` exports:

```ts
export function venueSlug(name: string): string
```

Algorithm, exactly and in this order:

1. `name.toLowerCase()`
2. `.replace(/[^a-z0-9]+/g, '-')` — any run of one or more characters outside
   `a-z0-9` collapses to a single `-`. This includes spaces, punctuation, and
   non-ASCII letters (`é` → separator, not `e`).
3. `.replace(/^-+|-+$/g, '')` — strip leading and trailing `-`.

Frozen input→output pairs (all verified against the live data on 2026-08-26):

| input | output |
|---|---|
| `"SFJAZZ Center"` | `"sfjazz-center"` |
| `"Black Cat SF"` | `"black-cat-sf"` |
| `"Dawn Club"` | `"dawn-club"` |
| `"Keys Jazz Bistro"` | `"keys-jazz-bistro"` |
| `"Mr. Tipple's"` | `"mr-tipple-s"` |
| `"Yoshi's"` | `"yoshi-s"` |
| `""` | `""` |
| `"!!!"` | `""` |
| `"---"` | `""` |
| `"  SFJAZZ   Center  "` | `"sfjazz-center"` |
| `"Café Du Nord"` | `"caf-du-nord"` |
| `"A & B"` | `"a-b"` |
| `"123"` | `"123"` |

The function is pure: no I/O, no clock, no module-level state. No venue list is
hardcoded anywhere in the codebase.

### C2 — Venue derivation

`app/lib/venues.ts` exports:

```ts
export interface VenueSummary { name: string; slug: string; eventCount: number }
export function venuesFromEvents(events: DisplayEvent[]): VenueSummary[]
export function eventsForSlug(events: DisplayEvent[], slug: string): DisplayEvent[]
```

- `venuesFromEvents` groups by the **exact** `event.venue` string. One entry per
  distinct name. `slug` is `venueSlug(name)`. `eventCount` is the number of events
  with that name. Result sorted ascending by `name.localeCompare(b.name, 'en')`.
- `eventsForSlug` returns `events.filter(e => venueSlug(e.venue) === slug)` sorted
  by the §C3 comparator.
- **Slug collision** (two distinct names, same slug): they remain **separate**
  entries in `venuesFromEvents` (keyed by name), and `eventsForSlug` returns the
  union of their events. No collision exists in current data; this rule exists so
  behavior is total rather than undefined.
- Both are pure: no I/O, no clock, no module-level state.
- **The venue set is whatever is in the passed `events` array.** No hardcoded list,
  no minimum count, no "all 6".

### C3 — Deterministic event ordering

`app/lib/event-order.ts` exports:

```ts
export function timeToMinutes(time: string): number | null
export function compareEvents(a: DisplayEvent, b: DisplayEvent): number
```

`timeToMinutes` matches `/^\s*(\d{1,2}):(\d{2})\s*(AM|PM)\s*$/i`. If no match →
`null`. If matched but hour `< 1` or `> 12`, or minute `> 59` → `null`. Otherwise
returns minutes since midnight: `12 AM` → `0`, `12 PM` → `720`, `PM` otherwise adds
`720`. Case-insensitive.

The `\s` class is load-bearing: **the real data contains U+202F NARROW NO-BREAK
SPACE** between minutes and meridiem (154 of 726 events). JS `\s` matches U+202F,
U+00A0 and U+0020, so `"8:00\u202fPM"`, `"8:00\u00a0PM"`, `"8:00 PM"` and
`"8:00PM"` all return `1200`. `"TBA"` returns `null` — note `transformEvent` already
maps a null DB time to the string `"TBA"`, so `DisplayEvent.time` is never null.

`compareEvents(a, b)` returns, in order:

1. `a.date.localeCompare(b.date)` if non-zero (`YYYY-MM-DD` sorts chronologically).
2. Then by time: let `ta = timeToMinutes(a.time)`, `tb = timeToMinutes(b.time)`.
   Both non-null → `ta - tb`. `ta` null and `tb` non-null → `1` (**unparseable time
   sorts last**). `ta` non-null and `tb` null → `-1`. Both null → fall through.
3. Then `a.id.localeCompare(b.id)`.

Step 3 makes the order **total** — no ties, so a hostile grader and a hopeful
implementer read the same expected array.

### C4 — Shared header

`app/components/SiteHeader.tsx` default-exports a component taking no required
props, containing no React hooks (so it renders in any context). Visual markup is
carried over from the current `app/page.tsx` header (lines 75–92): sticky, brand
lockup with the `Music` icon, `<h1>SF Jazz City</h1>`, tagline, and a nav.

Nav is three `next/link` `<Link>` elements, in this order, with these exact hrefs
and visible texts:

| testid | text | href |
|---|---|---|
| `nav-tonight` | `Tonight` | `/#tonight` |
| `nav-upcoming` | `Upcoming` | `/#upcoming` |
| `nav-venues` | `Venues` | `/venues` |

The brand lockup is wrapped in `<Link href="/" data-testid="brand-home">`.
Root element carries `data-testid="site-header"`.

**No element anywhere in the app has `href="#venues"` after this cycle.**

### C5 — Shared footer

`app/components/SiteFooter.tsx` default-exports a hook-free component reproducing
the current footer markup (`app/page.tsx` lines 238–245), including both existing
paragraphs verbatim. Root element carries `data-testid="site-footer"`.

### C6 — Shared event card, venue name linked

`app/components/EventCard.tsx` default-exports:

```ts
export default function EventCard(props: {
  event: DisplayEvent;
  variant?: 'featured' | 'compact';
}): JSX.Element
```

Default `variant` is `'compact'`.

- `'featured'` reproduces the Tonight card (`app/page.tsx` lines 119–148): `h-48`
  image, `p-6` body, `<h4>` title, venue row, `{time} · {price}` row, optional
  description, "Get Tickets" link.
- `'compact'` reproduces the Browse card (`app/page.tsx` lines 197–226): `h-40`
  image, `p-5` body, `<h4>` title, venue row, `{formatDate(date)} · {time}` row,
  price row, "Get Tickets" link.

In **both** variants the venue name element carries
`data-testid="event-card-venue"` and:

- if `venueSlug(event.venue) !== ''` → it is a `<Link href={'/venues/' + venueSlug(event.venue)}>`
  whose visible text is exactly `event.venue`;
- if `venueSlug(event.venue) === ''` → it is a plain `<span>` with text
  `event.venue` and **no** `href` (prevents a link to `/venues/`).

Root element carries `data-testid="event-card"`. Title element carries
`data-testid="event-card-title"`.

### C7 — `/venues` index

`app/venues/page.tsx` — a `"use client"` component that fetches `/api/events` in
`useEffect`, reads `data.events || []`, and derives its list via `venuesFromEvents`.

`SiteHeader` renders **immediately, before and during loading** (unlike the homepage,
whose loading screen has no header). `SiteFooter` renders once loading completes.

States, mutually exclusive:

| condition | testid present | required content |
|---|---|---|
| fetch in flight | `venues-loading` | text `Loading venues...` |
| fetch rejected or non-OK | `venues-error` | text `Could not load venues.` |
| loaded, 0 venues | `venues-empty` | text `No venues found.` |
| loaded, ≥1 venue | `venue-index` | one card per venue |

Each card: `data-testid="venue-card"`, is (or contains) a `<Link>` to
`/venues/<slug>`, and contains

- `data-testid="venue-card-name"` — visible text exactly the venue name;
- `data-testid="venue-card-count"` — visible text exactly `N upcoming event` when
  `N === 1`, otherwise `N upcoming events`.

Cards appear in DOM order matching `venuesFromEvents` order (alphabetical by name).
Page has an `<h1>` with text `Venues`.

### C8 — `/venues/[slug]` detail

`app/venues/[slug]/page.tsx` — a `"use client"` component reading the slug from
`useParams()` and fetching `/api/events` as in C7. `SiteHeader` renders immediately;
`SiteFooter` renders once loading completes.

- **Loading:** `data-testid="venue-loading"`, text `Loading events...`
- **Error:** `data-testid="venues-error"`, text `Could not load venues.`
- **Slug matches ≥1 event** (i.e. `eventsForSlug(events, slug).length > 0`):
  - `<h1 data-testid="venue-name">` with text exactly the venue name — the **actual
    name from the data**, not the slug. On collision, the alphabetically-first
    (`localeCompare(…, 'en')`) matching name.
  - `data-testid="venue-event-list"` containing one `EventCard` per event, `variant`
    `'compact'`, in `eventsForSlug` order.
  - A `<Link href="/venues" data-testid="venue-back-link">` with text `All venues`.
  - **No date filtering.** Every event the payload has for that venue is rendered.
- **Slug matches 0 events** (unknown, or a venue that aged out):
  - `data-testid="venue-not-found"` present; `venue-name` and `venue-event-list`
    absent.
  - Visible text `Venue not found`.
  - A `<Link href="/venues" data-testid="venue-not-found-back">` with text
    `Back to all venues`.
  - The page renders — no crash, no blank body, no Next.js error overlay.

### C9 — Homepage refactor with no behavior change

`app/page.tsx` renders `SiteHeader`, `SiteFooter`, and `EventCard`
(`variant="featured"` in Tonight, `variant="compact"` in Browse) instead of inline
markup. `formatDate` / `formatFullDate` move verbatim to `app/lib/format.ts` and are
imported — including `formatDate('all') === 'All Dates'`.

Preserved exactly:

- `<section id="tonight">` and `<section id="upcoming">` keep those ids.
- Search input filters on `artist` **or** `venue`, case-insensitive substring —
  same predicate as today.
- Date `<select>` options are `['all', ...sorted distinct dates]`, labelled by
  `formatDate`; selecting a date filters to `event.date === selectedDate`.
- Empty-results message `No shows found. Try adjusting your filters.`
- Tonight empty message `No shows scheduled for tonight. Check out upcoming events below!`
- The full-screen loading state (`Loading jazz events...`, no header) is
  **unchanged** — do not add a header to it.
- Headings `Playing Tonight` and `Browse All Shows`.

Homepage must not import from `app/venues/**`.

### C10 — Test toolchain exists and is Verification's to use

**Execution installs the runner and writes zero tests.** Execution must:

- add dev dependencies `vitest`, `@vitejs/plugin-react`, `jsdom`,
  `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`;
- add `"test": "vitest run"` to `package.json` scripts;
- add `vitest.config.ts` with `environment: 'jsdom'`, the React plugin, `globals: true`,
  a setup file importing `@testing-library/jest-dom`, and resolve alias `@` → repo
  root (matching `tsconfig.json` `paths`);
- ensure `npm test` exits **0** with no test files present (`vitest run
  --passWithNoTests` semantics — set `passWithNoTests: true` in the config).

Verification adds files under `tests/` and runs `npm test`.

### C11 — Build and lint stay green

`npm run build` exits 0. `npm run lint` exits 0. Build output lists routes `/`,
`/venues`, and `/venues/[slug]`.

---

## 3. Scope boundary — what this cycle will NOT do

Carried from ideation:

- **No editorial content** — no venue photos, addresses, neighborhood copy, vibe
  notes, capacity, links to venue websites. Deferred (was Option D).
- **No scraper changes.** `scraper/` is not read or written.
- **No event data-shape changes.** `app/types/event.ts` is byte-identical after this
  cycle. Slug is derived at usage time, never persisted.
- **No new API routes, no Convex, no database.** `/venues` and `/venues/[slug]` read
  `/api/events` and nothing else.

Added by this spec:

- **No change to `/api/events`** — the `date >= today` filter stays as-is, including
  its consequence that venues age out of the index (see §0).
- **No SSR/SSG for venue pages.** They are client components; no
  `generateStaticParams`, no `generateMetadata`, no per-page `<title>`.
- **No redirect or alias for the old `#venues` anchor.** The href simply changes.
- **No mobile nav.** The nav keeps its existing `hidden md:flex` — it remains
  invisible below the `md` breakpoint, exactly as today. Tests query the DOM, which
  is unaffected by the Tailwind class.
- **No visual redesign.** Tailwind classes are carried over; no new colors, no new
  spacing scale, no dark/light toggle.
- **No accessibility remediation** beyond what the extracted markup already has
  (e.g. the existing raw `<img>` tags stay raw `<img>`; no `next/image` migration).
- **No search or filtering on `/venues` or `/venues/[slug]`.**
- **No pagination.** Yoshi's currently has 64 upcoming events; they all render.
- **No E2E/browser tests.** Component-level (jsdom) only — see §6.0.

---

## 4. Risks

| # | Risk | Mitigation / accepted |
|---|---|---|
| R1 | Venue count is clock-dependent; a test asserting "6 venues" would rot within days. | Every test uses a fixed fixture and a mocked `fetch` (§6.0). No test reads `data/events.json` or the live route. |
| R2 | Extracting header/footer/card from a 248-line file silently drops a Tailwind class or a string. | C9 freezes the strings and ids; T-C9-* asserts them. Visual fidelity beyond that is **not** tested — accepted risk. |
| R3 | U+202F in times is invisible in diffs; a naive `\s`-free regex would return `null` for 154 events and sort them all last. | C3 makes the whitespace class explicit; T-C3-2 uses a `\u202f` escape in the fixture. |
| R4 | Naive string sort on `"12:00 AM"` vs `"7:30 PM"` looks right for some inputs and is wrong for others. | C3 mandates minutes-since-midnight; T-C3-1 includes midnight and 11 AM. |
| R5 | `node_modules` is not installed in the repo. First command must be `npm install` or everything fails confusingly. | Called out in §5 and §6.0. Registry reachability verified 2026-08-26. |
| R6 | Next 15 `useParams()` in a client component under a dynamic route — if Execution reaches for the async `params` prop instead, it will fight the App Router. | C8 names `useParams()` explicitly. |
| R7 | Verification could write tests that assert on Tailwind class strings, which Execution may legitimately vary. | §6.0 forbids asserting on `className`. |
| R8 | A card rendered with `variant` defaulting differently than specified would silently pass venue-page tests while breaking the homepage. | C6 fixes the default to `'compact'`; T-C6-1 asserts it. |

---

## 5. Rejected alternatives

- **Hardcode the six venue names** so `/venues` always shows 6 — rejected: ideation
  explicitly forbids a hardcoded slug map, and it would show venues with zero events
  and no page content.
- **Read `data/events.json` directly from the venue pages** (bypassing the date
  filter, restoring all 6) — rejected: ideation restricts the data source to
  `/api/events`. Worth a future cycle as an `?all=1` param on the route.
- **Add an "upcoming only" filter on `/venues/[slug]`** — rejected in ideation: the
  payload is already the scrape window, and a second cutoff would silently empty
  pages after a stale scrape.
- **Server components + `generateStaticParams`** for venue pages — rejected: the
  homepage is a client component fetching `/api/events`; matching that pattern keeps
  one data path and one mental model. Costs SEO, which is out of scope.
- **Playwright E2E** instead of jsdom component tests — rejected: browser download
  plus a dev server roughly doubles the verification cost for behavior that renders
  fully in jsdom. Route existence is covered by the `npm run build` route listing.
- **Persist `slug` onto `DisplayEvent`** — rejected: ideation freezes
  `app/types/event.ts`.
- **A single card component with no variants**, unifying the two homepage cards —
  rejected: it changes homepage visuals, which C9 forbids.

---

## 6. Test plan (freezes with this spec)

Verification implements these from this document alone. Verification **may add**
checks; it **may not remove or weaken** anything below.

### 6.0 Ground rules

1. `npm install` first — `node_modules` is absent from the repo.
2. Runner: `npm test` (`vitest run`, jsdom). Tests live under `tests/`.
3. **No test may read `data/events.json`, hit `/api/events`, or depend on the
   current date.** Component tests mock `global.fetch` to resolve
   `{ ok: true, json: async () => ({ events: FIXTURE }) }`.
4. **No test may assert on `className` / Tailwind classes.** Query by
   `data-testid`, role, text, `href`, or tag name only.
5. Text assertions are exact-match on trimmed `textContent` unless stated otherwise.
6. `next/link` renders an `<a>` in jsdom; assert `href` on the rendered anchor.
7. Async component tests must `await` React Testing Library's `findBy*` /
   `waitFor` — the fetch resolves on a microtask.

### 6.1 The fixture — `FIXTURE`

All component tests use exactly this array as the `events` payload. Note `e4`'s `time`
contains a **U+202F narrow no-break space**, written here as the JS escape
`\u202f`. Verification MUST write it as that escape in the test source — a literal
pasted U+202F is invisible in review and silently degrades to a plain space when
copied through some editors, which would defeat the entire purpose of T-C3-2.

```js
const FIXTURE = [
  { id: "e1", artist: "Trio One",    venue: "Yoshi's",       date: "2026-09-02", time: "9:30 PM",      price: "$30",        description: "",       ticketUrl: "https://example.com/1", image: "https://example.com/1.jpg" },
  { id: "e2", artist: "Quartet Two", venue: "SFJAZZ Center", date: "2026-09-01", time: "7:30 PM",      price: "$45",        description: "A show", ticketUrl: "https://example.com/2", image: "https://example.com/2.jpg" },
  { id: "e3", artist: "Solo Three",  venue: "Yoshi's",       date: "2026-09-01", time: "TBA",          price: "See venue",  description: "",       ticketUrl: "#",                     image: "https://example.com/3.jpg" },
  { id: "e4", artist: "Combo Four",  venue: "Yoshi's",       date: "2026-09-01", time: "8:00\u202fPM", price: "$25",        description: "",       ticketUrl: "https://example.com/4", image: "https://example.com/4.jpg" },
  { id: "e5", artist: "Duo Five",    venue: "Mr. Tipple's",  date: "2026-09-03", time: "11:00 AM",     price: "$20",        description: "",       ticketUrl: "https://example.com/5", image: "https://example.com/5.jpg" },
  { id: "e6", artist: "Big Six",     venue: "Yoshi's",       date: "2026-09-01", time: "12:00 AM",     price: "$15",        description: "",       ticketUrl: "https://example.com/6", image: "https://example.com/6.jpg" },
  { id: "e0", artist: "Zero Seven",  venue: "Yoshi's",       date: "2026-09-01", time: "12:00 AM",     price: "$15",        description: "",       ticketUrl: "https://example.com/0", image: "https://example.com/0.jpg" }
];
```

Derived expectations, computed and verified 2026-08-26:

- Distinct venues: `Mr. Tipple's` (1), `SFJAZZ Center` (1), `Yoshi's` (5).
- `venuesFromEvents(FIXTURE)` ===
  `[{name:"Mr. Tipple's",slug:"mr-tipple-s",eventCount:1},{name:"SFJAZZ Center",slug:"sfjazz-center",eventCount:1},{name:"Yoshi's",slug:"yoshi-s",eventCount:5}]`
- `eventsForSlug(FIXTURE, "yoshi-s").map(e => e.id)` === `["e0","e6","e4","e3","e1"]`
  — `e0`/`e6` both 12:00 AM (0 min), broken by id; then 8 PM (1200, narrow-nbsp);
  then `TBA` last on 09-01; then 09-02.
- `eventsForSlug(FIXTURE, "black-cat-sf")` === `[]`

### 6.2 Unit tests

| ID | Target | Input → expected | Pass criteria |
|---|---|---|---|
| **T-C1-1** | `venueSlug` | All 13 rows of the §C1 table | Every row exact-equal. |
| **T-C1-2** | `venueSlug` | `"Yoshi's"` called twice; `"SFJAZZ Center"` | Idempotent (`venueSlug(venueSlug(x)) === venueSlug(x)` for all 13 inputs). |
| **T-C1-3** | codebase | `grep -rn "sfjazz-center\|black-cat-sf\|dawn-club\|keys-jazz-bistro\|mr-tipple-s\|yoshi-s" app/` | **0 matches** — no hardcoded slug list in `app/`. |
| **T-C3-1** | `timeToMinutes` | `"12:00 AM"`→`0`; `"11:00 AM"`→`660`; `"12:00 PM"`→`720`; `"7:30 PM"`→`1170`; `"8:00 PM"`→`1200`; `"9:30 PM"`→`1290`; `"4:30 pm"`→`990` | All exact. |
| **T-C3-2** | `timeToMinutes` | `"8:00\u202fPM"`→`1200`; `"8:00\u00a0PM"`→`1200`; `"8:00PM"`→`1200` | All `1200`. Narrow-nbsp case is mandatory. |
| **T-C3-3** | `timeToMinutes` | `"TBA"`, `""`, `"25:00 PM"`, `"0:30 AM"`, `"7:70 PM"`, `"doors 8"` | All `null`. |
| **T-C3-4** | `compareEvents` | `[...FIXTURE].sort(compareEvents).map(e=>e.id)` | `["e0","e6","e2","e4","e3","e1","e5"]` — 09-01 group is `e0`,`e6` (both 0 min, tie broken by id), `e2` (1170), `e4` (1200), `e3` (null, last); then 09-02 `e1`; then 09-03 `e5`. **Verification must recompute this array from the §C3 rules rather than trusting this cell**, and assert its computed value; the rules, not this string, are normative. |
| **T-C3-5** | `compareEvents` | Two events, same date, one `"TBA"`, one `"9:30 PM"` | The `"TBA"` event sorts **after**, in both argument orders. |
| **T-C2-1** | `venuesFromEvents` | `FIXTURE` | Deep-equals the §6.1 array — 3 entries, that order, those counts. **No assertion anywhere that the count is 6.** |
| **T-C2-2** | `venuesFromEvents` | `[]` | `[]`. |
| **T-C2-3** | `eventsForSlug` | `(FIXTURE, "yoshi-s")` | ids `["e0","e6","e4","e3","e1"]`. |
| **T-C2-4** | `eventsForSlug` | `(FIXTURE, "black-cat-sf")`, `(FIXTURE, "")`, `(FIXTURE, "nope")` | `[]` each. |
| **T-C2-5** | `venuesFromEvents` / `eventsForSlug` | Two distinct names slugging alike, e.g. `"The Spot"` and `"The  Spot!"` (both → `the-spot`) | `venuesFromEvents` yields **2** entries; `eventsForSlug(…, "the-spot")` returns **both** events. |
| **T-C9-1** | `formatDate` | `'all'` | `'All Dates'`. |

### 6.3 Component tests

| ID | Target | Setup | Pass criteria |
|---|---|---|---|
| **T-C4-1** | `SiteHeader` | render bare | `nav-venues` anchor `href === "/venues"`, text `Venues`. |
| **T-C4-2** | `SiteHeader` | render bare | `nav-tonight` href `/#tonight` text `Tonight`; `nav-upcoming` href `/#upcoming` text `Upcoming`. |
| **T-C4-3** | app source | `grep -rn 'href="#venues"' app/` and `grep -rn '"#tonight"\|"#upcoming"' app/` | **0 matches for all three** — no bare-anchor navs remain. |
| **T-C4-4** | `SiteHeader` | render bare | `brand-home` anchor `href === "/"`. |
| **T-C4-5** | `SiteHeader` | render bare | Renders without throwing when no fetch is mocked (proves hook-free). |
| **T-C5-1** | `SiteFooter` | render bare | `site-footer` present; contains the substring `SF Jazz City. Your guide to live jazz in San Francisco.` and `Always verify details with venues.` |
| **T-C6-1** | `EventCard` | `<EventCard event={FIXTURE[0]} />`, no `variant` | Renders; `event-card-title` text `Trio One`. Also render with `variant="compact"` and assert the two outputs' `innerHTML` are identical (proves the default). |
| **T-C6-2** | `EventCard` | `variant="compact"`, `event = FIXTURE[0]` (`Yoshi's`) | `event-card-venue` is an `<a>` (`tagName === 'A'`), `href === "/venues/yoshi-s"`, text `Yoshi's`. |
| **T-C6-3** | `EventCard` | `variant="featured"`, same event | Same three assertions as T-C6-2. |
| **T-C6-4** | `EventCard` | event with `venue: "!!!"` | `event-card-venue` `tagName === 'SPAN'`, has no `href` attribute, text `!!!`. |
| **T-C6-5** | `EventCard` | `variant="featured"` vs `"compact"`, `FIXTURE[1]` (has a description) | Featured renders the description text `A show`; compact does not. |
| **T-C7-1** | `/venues` page | fetch mocked → `FIXTURE` | Exactly **3** `venue-card` elements. |
| **T-C7-2** | `/venues` page | same | `venue-card-name` texts, in DOM order: `["Mr. Tipple's","SFJAZZ Center","Yoshi's"]`. |
| **T-C7-3** | `/venues` page | same | `venue-card-count` texts, in DOM order: `["1 upcoming event","1 upcoming event","5 upcoming events"]` — singular/plural exact. |
| **T-C7-4** | `/venues` page | same | Each card contains an `<a>` whose `href` is `/venues/mr-tipple-s`, `/venues/sfjazz-center`, `/venues/yoshi-s` respectively. |
| **T-C7-5** | `/venues` page | fetch never resolves | `venues-loading` present with text `Loading venues...`; `site-header` present **at the same time**. |
| **T-C7-6** | `/venues` page | fetch rejects | `venues-error` present, text `Could not load venues.`; no unhandled rejection. |
| **T-C7-7** | `/venues` page | fetch → `{ events: [] }` | `venues-empty` present, text `No venues found.`; **0** `venue-card` elements. |
| **T-C7-8** | `/venues` page | fetch → `FIXTURE` | An `<h1>` with text `Venues` is present. |
| **T-C8-1** | `/venues/[slug]` | `useParams` → `{slug:"yoshi-s"}`, fetch → `FIXTURE` | `venue-name` is an `<h1>` with text exactly `Yoshi's` (not `yoshi-s`). |
| **T-C8-2** | same | same | `venue-event-list` contains exactly **5** `event-card` elements; their `event-card-title` texts in DOM order are `["Zero Seven","Big Six","Combo Four","Solo Three","Trio One"]` (= ids `e0,e6,e4,e3,e1`). |
| **T-C8-3** | same | same | Every rendered `event-card-venue` is an `<a>` with `href === "/venues/yoshi-s"` — self-links present, 5 of them. |
| **T-C8-4** | same | `slug:"sfjazz-center"` | Exactly **1** `event-card`; `venue-name` text `SFJAZZ Center`; the Yoshi's and Mr. Tipple's events are **absent** (assert no `event-card-title` with text `Trio One` or `Duo Five`). |
| **T-C8-5** | same | `slug:"black-cat-sf"` (valid slug, zero events) | `venue-not-found` present; `venue-name` and `venue-event-list` **absent**; visible text `Venue not found`. |
| **T-C8-6** | same | `slug:"totally-made-up"` | Same as T-C8-5, plus `venue-not-found-back` is an `<a>` with `href === "/venues"` and text `Back to all venues`. |
| **T-C8-7** | same | `slug:"yoshi-s"` | `venue-back-link` is an `<a>`, `href === "/venues"`, text `All venues`. |
| **T-C8-8** | same | fetch never resolves | `venue-loading` present, text `Loading events...`; `site-header` present simultaneously. |
| **T-C8-9** | same | `slug:"yoshi-s"`, fetch → `FIXTURE` | Renders **all 5** Yoshi's events including `e1` on `2026-09-02` — proves no second date cutoff was applied. |
| **T-C8-10** | same | `slug:"mr-tipple-s"` | Renders; `venue-name` text `Mr. Tipple's` — apostrophe round-trips through the slug lookup. |

### 6.4 Homepage regression tests

Fetch mocked → `FIXTURE` for all of these.

| ID | Pass criteria |
|---|---|
| **T-C9-2** | After load, `site-header` and `site-footer` are both present. |
| **T-C9-3** | `document.getElementById('tonight')` and `document.getElementById('upcoming')` are both non-null. |
| **T-C9-4** | Headings `Playing Tonight` and `Browse All Shows` are present. |
| **T-C9-5** | Browse section renders **7** `event-card` elements (whole fixture, no filter). |
| **T-C9-6** | Typing `yoshi` into the search input (placeholder `Search artists or venues...`) narrows Browse to **5** cards — proves venue-name search still works. |
| **T-C9-7** | Typing `trio` narrows Browse to **1** card, title `Trio One` — artist search still works. |
| **T-C9-8** | Typing `zzzznomatch` shows text `No shows found. Try adjusting your filters.` |
| **T-C9-9** | The date `<select>` has **4** options: `All Dates` plus one per distinct date (`2026-09-01`, `2026-09-02`, `2026-09-03`), first option value `all`. |
| **T-C9-10** | Selecting the option with value `2026-09-03` narrows Browse to **1** card, title `Duo Five`. |
| **T-C9-11** | Every Browse `event-card-venue` for a `Yoshi's` event is an `<a>` with `href === "/venues/yoshi-s"`. |
| **T-C9-12** | With fetch pending, text `Loading jazz events...` is shown and `site-header` is **absent** (homepage loading state deliberately unchanged — C9). |
| **T-C9-13** | Mock the system date to a fixture date so a Tonight event exists (e.g. `vi.setSystemTime(new Date('2026-09-01T12:00:00'))` before render); Tonight section renders `featured` cards for the 09-01 events (**5**) and each has a linked venue name. Restore real timers after. |
| **T-C9-14** | `grep -rn "venues" app/page.tsx` shows no `import` from `app/venues/` — homepage does not import venue pages. |

### 6.5 Build / integration gates

| ID | Command | Pass criteria |
|---|---|---|
| **T-B-1** | `npm install` | Exit 0. |
| **T-B-2** | `npm test` | Exit 0; **every** test above present and passing; 0 skipped, 0 todo. |
| **T-B-3** | `npm run build` | Exit 0. |
| **T-B-4** | `npm run build` output | Route table lists `/`, `/venues`, and `/venues/[slug]`. |
| **T-B-5** | `npm run lint` | Exit 0. |
| **T-B-6** | `git diff --stat app/types/event.ts app/api/events/route.ts app/layout.tsx app/globals.css next.config.js tailwind.config.js data/ scraper/` | **Empty** — none of these changed. |
| **T-B-7** | `npx tsc --noEmit` | Exit 0. |

### 6.6 Explicitly NOT tested

Named so nobody scores their absence as a failure: visual/pixel fidelity, Tailwind
class equivalence, responsive breakpoints, real-browser navigation, SEO/metadata,
performance, `data/events.json` contents, scraper behavior, and the live venue count.

---

## 7. Cost / time estimate — veto on sight

**Expected total spend: US $24.** Breach threshold at 1.5× = **$36**.
**Expected wall-clock: 3 hours.**

| Phase | Driver | Est. |
|---|---|---|
| Execution | `npm install`; 9 new files (~450 LOC) + a 248-line rewrite; build/lint loop | $11 · 1.3 h |
| Verification | Toolchain wiring + ~60 assertions across ~8 test files; 2 full `npm test` + `npm run build` cycles | $9 · 1.2 h |
| Retry buffer | One partial re-execution (assume ~1 of the 3 allowed verification attempts fails) | $4 · 0.5 h |

**What drives the uncertainty, ranked:**

1. **Verification attempts.** The estimate assumes **2** attempts. Each additional
   full attempt adds roughly **$5 and 35 min**. Three attempts land near $29 —
   inside the threshold; a third failure escalates on the attempt cap before it
   escalates on budget.
2. **`npm install` on a cold tree.** No `node_modules` today; the vitest + RTL set
   is ~7 new dev deps. Registry reachability confirmed 2026-08-26 (PONG 119 ms). A
   resolution conflict with `eslint-config-next@15.1.0` is the plausible snag —
   ~$2 and 20 min if it bites.
3. **The `page.tsx` extraction.** 248 lines, two near-duplicate card markups. If
   Execution "improves" them into one shared markup, T-C6-5 and the homepage
   regressions fail and force a retry. C6 and C9 are written to head this off.
4. **jsdom + Next `useParams`/`<Link>` mocking.** Standard but fiddly; the first
   test file usually costs more than the rest combined.

**Milestone count: 5** — under the "handful" line, so **no cycle split is
proposed.**

| # | Milestone | Done when |
|---|---|---|
| M1 | Pure lib | `venue-slug.ts`, `event-order.ts`, `venues.ts`, `format.ts` exist with the C1–C3 signatures |
| M2 | Toolchain | `npm test` exits 0 with no tests present (C10) |
| M3 | Shared components | `SiteHeader`, `SiteFooter`, `EventCard` exist per C4–C6 |
| M4 | Routes | `/venues` and `/venues/[slug]` exist per C7–C8 |
| M5 | Homepage refactor green | C9 satisfied; `npm run build` and `npm run lint` exit 0 |

---

## 8. Definition of done

Every commitment C1–C11 holds, every test in §6 is implemented and passing, §3 is
respected, and T-B-6 shows the untouchable files untouched.
