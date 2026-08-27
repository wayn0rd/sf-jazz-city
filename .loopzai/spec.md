<!-- spec.md — Specification phase output for cycle 2. Frozen at spec-approval gate. -->

# Cycle 2 Specification — Scraper image extraction: Yoshi's + Mr. Tipple's

**Status:** awaiting spec-approval gate
**Input:** `.loopzai/ideation.md` (frozen)
**Milestones:** 3 (M1, M2, M3) — below the split threshold; one cycle is appropriate.

---

## 0. Executive summary — read this before the estimate

The Specification phase ran the live probe that `ideation.md` (D-i2) required.
It **falsified two of ideation's technical assumptions**, and the result makes
this cycle materially cheaper and more certain than ideation projected:

| | Ideation assumed | Probe found (2026-08-26) |
|---|---|---|
| **Yoshi's** | Detail pages carry `og:image`-style tags | **No `og:image`, no JSON-LD, no meta tags at all.** But every detail page carries `<img class="event-img" src="/userfiles/events/images/...">` — **70/70 = 100% yield** |
| **Mr. Tipple's** | JSON-LD rarely carries images; detail-page fetching is "the likely fix" | **JSON-LD carries images on 73/83 events (88%).** The images are extracted correctly and then **destroyed by a last-wins dedup bug.** No detail fetching needed at all |

Mr. Tipple's is therefore **not a scraping-capability problem — it is a
data-loss bug in code that already works.** The adapter extracts 73 images and
then throws away 70 of them. Evidence, reproduced live:

```
SCHEMA path: 83 events, with image: 73     <- images extracted correctly
DOM path:    83 events, with image:  0     <- selector matches, finds no <img>
AFTER DEDUP: 45 events, with image:  3     <- 70 images destroyed here
```

Cause: `mrtipples_scraper.py:321` is
`list({(e.title, e.date): e for e in events}.values())`, and `events` is
`schema_events + calendar_events`. A dict comprehension is **last-wins**, so
each DOM event (`image_url=None`) overwrites its schema twin (`image_url=<url>`).
The only 3 survivors are events whose JSON-LD titles contain undecoded HTML
entities (`&#8217;`), so their keys never collide.

Applying the two fixes below and re-running live yields **14/14 = 100%** of
Mr. Tipple's upcoming events with images.

**Net effect on the plan:** ideation's D-i2 (per-event detail-page fetching)
is exercised for **Yoshi's only**. Mr. Tipple's adds **zero** new HTTP
requests. See D-s2.

---

## 1. Decisions made in this phase (each independently vetoable)

- **D-s1 — Yoshi's uses the detail-page path, selector `img.event-img`.**
  The calendar JSON exposes exactly six keys
  (`className`, `end`, `eventOrder`, `start`, `title`, `url`) and no image
  field, so the cheap path D-i2 asked us to prefer **does not exist**. The
  detail-page path is taken, per D-i2's fallback. Extraction targets the
  `<img>` whose class list contains `event-img` — *not* `og:image`, which the
  pages do not serve.
  *Measured cost:* 70 unique detail URLs for 118 events, fetched at
  concurrency 4 in **8.7 s**, 100% hit rate, no rate-limiting observed.

- **D-s2 — Mr. Tipple's does NOT fetch detail pages.** The cheap path already
  works; the bug is downstream. This is a deliberate narrowing of D-i2 and the
  single largest cost reduction in this spec. Vetoing this decision (i.e.
  insisting on detail fetching for Mr. Tipple's) would add ~45 browser page
  loads per run for no measured gain.

- **D-s3 — HTML entities in titles are decoded (`html.unescape`).** This is
  *required* for D-s2 to work: without it the schema row (`Patrick Wolff&#8217;s`)
  and the DOM row (`Patrick Wolff's`) never collide, so the merge cannot pair
  them and each event still emits one image-less duplicate card. This is
  in-scope because it is load-bearing for the image outcome, not a general
  data-quality excursion.

- **D-s4 — A bounded, lossless cleanup of 13 stale duplicate rows.** This
  *extends* D-i5 ("no backfill ceremony") and is called out separately so it
  can be vetoed alone. Exactly 13 Mr. Tipple's rows carry entity titles, and
  **all 13 already have a decoded twin row** in the DB. Once D-s3 lands, those
  13 will never be updated again and will render as permanent duplicate cards.
  The cleanup copies each entity row's `image_url` onto its twin when the twin
  lacks one, then deletes the entity row. It touches 13 rows, no other venue,
  and cannot lose an image. *If vetoed:* the site shows ~2 upcoming duplicate
  cards and 11 past ones; nothing else in this spec is affected.

- **D-s5 — Tests are pytest, sync, and pure.** All extraction and merge logic
  is exposed as **synchronous, side-effect-free, importable functions** so
  fixture tests need no browser, no network, and no `pytest-asyncio`.
  `pytest 9.1.1` is present in `.venv`; `pytest>=8` is added to
  `scraper/requirements.txt` to keep a rebuilt venv working.

- **D-s6 — No new runtime dependencies.** Implementation uses only the stdlib
  (`html`, `re`, `urllib.parse`, `asyncio`) plus the already-vendored `aiohttp`
  and `playwright`. `bs4` is **not** available in the venv and must not be
  introduced.

---

## 2. Ground truth measured this phase (2026-08-26)

Baseline from committed `data/events.json`, cutoff `date >= 2026-08-26`:

| Venue | total rows | upcoming | upcoming w/ image |
|---|---|---|---|
| Black Cat SF | 40 | 5 | 5 |
| Dawn Club | 188 | 31 | 31 |
| Keys Jazz Bistro | 171 | 46 | 46 |
| SFJAZZ Center | 160 | 82 | 82 |
| **Mr. Tipple's** | 146 | 16 | **2** |
| **Yoshi's** | 205 | 88 | **0** |

Live probe results:

- Yoshi's calendar feed: 118 raw items → 118 unique `(title, date, time)`
  events → **70 unique detail URLs** (a show with 7:30 and 9:30 sets shares one
  detail page, so caching by URL nearly halves fetches).
- Yoshi's detail pages: **70/70** carry `img.event-img`. All `src` values are
  **relative** (`/userfiles/events/images/...`). Extensions observed:
  51 `.jpeg`, 11 `.jpg`, 8 `.png`. Zero `.svg`, zero data URIs.
- Mr. Tipple's calendar: 2 JSON-LD blocks, 83 `Event` items, 73 with `image`.
  DOM selector `.type-tribe_events` matches 166 elements containing **zero**
  `<img>` elements.
- Mr. Tipple's with both fixes applied, live: **42 events, 37 with images (88%);
  14/14 upcoming (100%); 0 entity titles remaining.** Event count drops 45 → 42
  because 3 duplicate pairs correctly merge — this is the intended behavior and
  must not be scored as a count collapse (see T7).

---

## 3. Commitments

Each commitment is a falsifiable statement about the code after this cycle.

### 3.1 Shared module

- **C1.** A new module `scraper/image_utils.py` exists and exports a
  synchronous, pure function:
  `normalize_image_url(raw: Optional[str], base_url: str) -> Optional[str]`
- **C2.** `normalize_image_url` returns `None` for every one of: `None`; the
  empty string; a whitespace-only string; any value whose lowercased form
  starts with `data:`; any value whose path component (query string and
  fragment ignored) ends in `.svg` (case-insensitive).
- **C3.** For any value it does not reject, `normalize_image_url` returns an
  **absolute** URL: a relative path is joined to `base_url`; a
  protocol-relative `//host/path` is given the `https:` scheme; an already
  absolute `http://`/`https://` URL is returned unchanged. The returned string
  always starts with `http://` or `https://`.
- **C4.** No `image_url` written to the database by either adapter is ever the
  empty string. It is either `None` or a value satisfying C3.

### 3.2 Yoshi's (`scraper/yoshis_scraper.py`)

- **C5.** A synchronous, pure function
  `extract_image_url(html_text: str) -> Optional[str]` exists. It returns the
  absolute URL (C3-normalized against `https://yoshis.com`) of the `<img>`
  element whose **class list contains the token `event-img`**, or `None` if no
  such element exists.
- **C6.** `extract_image_url` is robust to the markup Yoshi's actually serves:
  attributes in any order (`src` before or after `class`), arbitrary
  whitespace **including newlines inside the tag** (the live pages break lines
  mid-tag), and multi-token class attributes (`class="lazy event-img rounded"`).
- **C7.** `extract_image_url` never returns the site logo
  (`/images/yoshi-logo.png`) or the Facebook tracking pixel
  (`facebook.com/tr?...`), both of which appear as `<img>` elements on every
  detail page.
- **C8.** A synchronous, pure function
  `detail_url_from_item(item: dict) -> Optional[str]` exists, returning the
  item's `url` field absolutized against `https://yoshis.com`, or `None` when
  absent/empty.
- **C9.** `scrape_events()` populates `Event.image_url` for Yoshi's events by
  fetching each event's detail page.
- **C10.** Detail pages are fetched **at most once per unique detail URL** per
  run (results cached/keyed by URL), reusing a single `aiohttp.ClientSession`
  with the module's existing `HEADERS`.
- **C11.** Detail fetching is bounded by an `asyncio.Semaphore` with a limit of
  **4 or fewer** concurrent requests, and each request carries a timeout of 30 s
  or less.
- **C12.** A failed, timed-out, non-200, or image-less detail fetch yields
  `image_url = None` for the affected events, is logged, and **never raises out
  of `scrape_events()`**. A detail-page outage degrades Yoshi's to today's
  behavior; it must not fail the venue or the run.
- **C13. `ticket_url` semantics are unchanged.** `_parse_event` continues to
  prefer the embedded etix URL over the detail URL. Extracting the detail URL
  for image fetching must not alter `ticket_url` for any event.
- **C14.** Parsing of `title`, `date`, `time`, `artists`, `status`, and the
  `(title, date, time)` dedup key is unchanged.

### 3.3 Mr. Tipple's (`scraper/mrtipples_scraper.py`)

- **C15.** A synchronous, pure function
  `merge_events(events: list[Event]) -> list[Event]` exists. It collapses
  events sharing a `(title, date)` key into one, and for each of
  `image_url`, `time`, `price`, `ticket_url`, `description` takes the **first
  non-empty** value across the group. `None` and `""` both count as empty.
- **C16. Order independence.** `merge_events` produces the same field values
  regardless of input order. Specifically, given an image-bearing event and an
  image-less event with the same `(title, date)`, the merged result carries the
  image **whether the image-bearing event appears first or last**. This is the
  direct regression guard for the bug in §0.
- **C17.** `scrape_events()` uses `merge_events` in place of the
  `list({(e.title, e.date): e for e in events}.values())` last-wins
  comprehension at `mrtipples_scraper.py:321`.
- **C18.** Event titles from **both** the JSON-LD path and the DOM path are
  HTML-unescaped (`html.unescape`) and stripped before being used as data or as
  a merge key. No `Event.title` produced by this adapter contains a `&#NNNN;`
  or `&amp;`-style entity.
- **C19.** `_parse_schema_event` routes its `image` value (already handling the
  `str` / `list` / `dict` shapes) through `normalize_image_url` with base
  `https://mrtipplessf.com`, so C2–C4 hold for this venue.
- **C20.** The Mr. Tipple's adapter issues **no additional network requests**:
  no per-event detail-page fetches are added.

### 3.4 Bounded cleanup (D-s4)

- **C21.** A one-shot, idempotent maintenance routine is run against
  `scraper/events.db` that, for every row with `venue = "Mr. Tipple's"` whose
  `title` contains `&#`: copies its `image_url` onto the row whose
  `(title, date)` equals `(html.unescape(title), date)` **if and only if** that
  twin's `image_url` is null/empty, then deletes the entity row.
- **C22.** The cleanup deletes a row **only when its decoded twin exists**. If
  a twin is missing, the row is left untouched and the fact is logged.
- **C23.** The cleanup touches no venue other than Mr. Tipple's and no rows
  without `&#` in the title.

### 3.5 Scope integrity

- **C24.** No file under `app/` is modified. `transformEvent`, the
  `FALLBACK_IMAGE` constant, `isValidImageUrl`, `/api/events`, and all
  components are untouched (D-i3).
- **C25.** `scraper/image_downloader.py`, the `--images` flag, and
  `scraper/images/` are unmodified (D-i4).
- **C26.** No new entry is added to `scraper/requirements.txt` other than
  `pytest>=8` (D-s6).

---

## 4. Out of scope — this cycle will NOT do these

Explicitly deferred, including things `ideation.md` raises:

1. **No frontend change of any kind** — no local image serving, no
   `next/image`, no placeholder redesign, no lazy-loading (D-i3, D-i4).
2. **No general backfill of past rows.** Only the 13 rows in C21 are touched;
   the other ~1,000 historical rows keep whatever `image_url` they have (D-i5).
   Past Yoshi's events stay image-less forever.
3. **No image download / local hosting / CDN.** `image_url` remains a hotlink.
4. **No image validation by fetching.** The scraper never HEAD/GETs an
   `image_url` to confirm it resolves; validity is structural only (C2/C3).
   A URL that 404s at the CDN will still be written.
5. **No changes to the other four venues'** adapters (SFJAZZ, Black Cat, Dawn
   Club, Keys Jazz Bistro). They are at 100% image coverage; they are
   regression surface only.
6. **No repair of Mr. Tipple's dead DOM path.** The `.type-tribe_events`
   selector currently yields 0 images; after C15–C17 it is harmless. Making it
   productive again is not attempted.
7. **No schema/migration work.** The `events` table is unchanged; `image_url`
   already exists.
8. **No scheduling/automation** of the scrape.
9. **No `og:image` support for Yoshi's** — the pages do not serve it (D-s1).
10. **No dedup-key change** for either adapter beyond the entity-decoding in
    C18. Yoshi's stays `(title, date, time)`; Mr. Tipple's stays `(title, date)`.

---

## 5. Test plan (FROZEN at approval)

Verification implements these from this document alone. Verification may **add**
checks; it may never remove or weaken one below.

**Toolchain.** Python tests live under `tests/scraper/` and run with:

```
cd /home/waynehoy/Projects/sf-jazz-city && .venv/bin/python -m pytest tests/scraper -q
```

**Pass criterion for the whole unit layer: exit code 0, zero failures, zero
errors.** Tests must be synchronous and must not open a browser or a socket.
Vitest's default include glob does not match `.py`/`.html`, so these files
cannot disturb `npm test`.

**Fixtures.** Committed under `tests/fixtures/scraper/`. The two Yoshi's HTML
fixtures may be trimmed for size (the live page is 166 KB; CSS/JS blocks may be
removed) but **must retain**: the `img.event-img` element, the
`/images/yoshi-logo.png` logo `<img>`, the `facebook.com/tr` pixel `<img>`, and
at least one tag with a newline inside it.

### Layer 1 — pure unit tests (deterministic, offline)

**T1 — `normalize_image_url` (C1–C3).** Table test; each row asserts exact
equality.

| input `raw` | `base_url` | expected |
|---|---|---|
| `/userfiles/events/images/2866/keikomatsui2-copy.jpeg` | `https://yoshis.com` | `https://yoshis.com/userfiles/events/images/2866/keikomatsui2-copy.jpeg` |
| `https://mrtipplessf.com/wp-content/uploads/Sam-Bevin-.jpg` | `https://mrtipplessf.com` | unchanged (identical string) |
| `//cdn.example.com/a.jpg` | `https://yoshis.com` | `https://cdn.example.com/a.jpg` |
| `None` | any | `None` |
| `""` | any | `None` |
| `"   "` | any | `None` |
| `data:image/svg+xml;base64,PHN2Zz4=` | any | `None` |
| `data:image/png;base64,iVBORw0KGgo=` | any | `None` |
| `/assets/placeholder.svg` | `https://yoshis.com` | `None` |
| `/assets/placeholder.SVG?v=2` | `https://yoshis.com` | `None` |

Plus a property assertion: for every input in the table, the result is either
`None` or a `str` starting with `http://` or `https://`.

**T2 — Yoshi's `extract_image_url` (C5–C7).**
1. Fixture `yoshis_detail_with_image.html` (captured from
   `https://yoshis.com/events/sold-out/keiko-matsui-14/detail`) →
   exactly `https://yoshis.com/userfiles/events/images/2866/keikomatsui2-copy.jpeg`.
2. Fixture `yoshis_detail_no_image.html` (same page with the `event-img`
   element removed) → `None`.
3. The result for fixture 1 does **not** contain the substring `yoshi-logo`.
4. The result for fixture 1 does **not** contain the substring `facebook.com/tr`.
5. Inline string `<img src="/a/b.jpg" class="event-img" />` →
   `https://yoshis.com/a/b.jpg`.
6. Inline string `<img class="event-img" src="/a/b.jpg" />` →
   `https://yoshis.com/a/b.jpg` (attribute order).
7. Inline string `<img\n  src="/a/b.jpg"\n  class="event-img" />` →
   `https://yoshis.com/a/b.jpg` (newline inside tag).
8. Inline string `<img src="/a/b.jpg" class="lazy event-img rounded" />` →
   `https://yoshis.com/a/b.jpg` (multi-token class).
9. Inline string `<img src="/a/b.jpg" class="event-image-wrapper" />` →
   `None` (substring `event-img` must not match the token test).
10. Inline string `<img src="data:image/svg+xml;base64,PHN2Zz4=" class="event-img" />`
    → `None` (C2 applies after extraction).

**T3 — Yoshi's `detail_url_from_item` + `ticket_url` non-regression (C8, C13).**
Using this exact item, which is verbatim live data:

```json
{
  "title": "7:30PM KEIKO MATSUI<br/><a href=\"https://www.etix.com/ticket/p/69261880/keiko-matsui-wed82626-oakland-yoshis\" target='_blank' class='calendarBuyTickets'>Buy Tickets</a>",
  "start": "2026-08-26 19:30:00",
  "end": "2026-08-26",
  "eventOrder": 1,
  "className": "Buy Tickets",
  "url": "https://yoshis.com/events/sold-out/keiko-matsui-14/detail"
}
```

1. `detail_url_from_item(item)` == `https://yoshis.com/events/sold-out/keiko-matsui-14/detail`.
2. `_parse_event(item).ticket_url` ==
   `https://www.etix.com/ticket/p/69261880/keiko-matsui-wed82626-oakland-yoshis`
   — i.e. still the etix URL, **not** the detail URL.
3. `_parse_event(item).title` == `KEIKO MATSUI`.
4. `_parse_event(item).date` == `2026-08-26`; `.time` == `7:30 PM`.
5. `detail_url_from_item({})` is `None`; `detail_url_from_item({"url": ""})` is `None`.
6. `detail_url_from_item({"url": "/events/x/detail"})` ==
   `https://yoshis.com/events/x/detail`.
7. An item with `className` containing `Sold Out` still yields
   `.status == "Sold Out"`.

**T4 — Mr. Tipple's `_parse_schema_event` (C18, C19).**
1. `{"@type":"Event","name":"A","startDate":"2026-09-04T18:15:00-08:00","image":"https://mrtipplessf.com/wp-content/uploads/a.jpg"}`
   → `image_url == "https://mrtipplessf.com/wp-content/uploads/a.jpg"`.
2. `image` as a list `["https://mrtipplessf.com/a.jpg","https://mrtipplessf.com/b.jpg"]`
   → `image_url` is the **first** element.
3. `image` as a dict `{"url":"https://mrtipplessf.com/a.jpg"}` → that URL.
4. `image` absent → `image_url is None`.
5. `image` == `""` → `image_url is None` (**not** `""`).
6. `image` == `"data:image/svg+xml;base64,PHN2Zz4="` → `image_url is None`.
7. `image` == `"/wp-content/uploads/a.jpg"` →
   `"https://mrtipplessf.com/wp-content/uploads/a.jpg"`.
8. **Entity decoding:** `name` ==
   `"Patrick Wolff&#8217;s &#8220;Swinging Organ&#8221; Quartet"` →
   `.title` == `"Patrick Wolff’s “Swinging Organ” Quartet"`
   (U+2019, U+201C, U+201D as literal characters).
9. `name` == `"Carla Helmbrecht &#038; The Brad Leali Quartet"` →
   `.title` == `"Carla Helmbrecht & The Brad Leali Quartet"`.
10. For every case above, `"&#" not in event.title`.

**T5 — `merge_events` (C15, C16). The core regression test.**
Let `A = Event(title="X", date="2026-09-04", image_url="https://h/a.jpg")` and
`B = Event(title="X", date="2026-09-04", image_url=None)`.
1. `merge_events([A, B])` has length 1 and `[0].image_url == "https://h/a.jpg"`.
2. `merge_events([B, A])` has length 1 and `[0].image_url == "https://h/a.jpg"`
   — **order independence; this fails against today's code.**
3. `merge_events([A, Event(title="X", date="2026-09-04", image_url="")])`
   → `image_url == "https://h/a.jpg"` (empty string counts as missing).
4. Field fill-in: merging `Event(title="X",date="D",time=None,price="$20")`
   with `Event(title="X",date="D",time="8:00 PM",price=None)` yields
   `time == "8:00 PM"` **and** `price == "$20"`.
5. Distinct keys are preserved: merging `(title="X",date="D1")` and
   `(title="X",date="D2")` returns 2 events; `(title="Y",date="D1")` and
   `(title="Z",date="D1")` returns 2 events.
6. `merge_events([])` returns `[]`.
7. Idempotence: `merge_events(merge_events(xs)) == merge_events(xs)` by
   `(title, date, image_url)` for a mixed input list.

**T6 — Cleanup routine (C21–C23), offline.** Build a temporary SQLite DB with
the project schema containing at minimum: an entity row
`("Richard Howell&#8217;s Sudden Changes", "2026-05-01", image_url="https://h/r.jpg")`
and its decoded twin `("Richard Howell's Sudden Changes", "2026-05-01", image_url=NULL)`;
an entity row with **no** twin; and a Dawn Club row containing `&#` in the title.
After running the cleanup:
1. The decoded twin's `image_url` == `https://h/r.jpg`.
2. The entity row that had a twin is deleted.
3. The entity row **without** a twin still exists (C22).
4. The Dawn Club row is untouched (C23).
5. Running the cleanup a second time changes nothing (idempotent).
6. Total row count decreased by exactly the number of entity rows that had twins.

### Layer 2 — live smoke (run once, at verification time)

These run against the moving live site. Thresholds below are the **binding**
pass criteria carried over from ideation; the human gate is the final arbiter
(ideation "Verification shape"). Measured spec-phase expectations are given for
context — a result that clears the threshold but falls far short of the
expectation should be flagged to the human, not silently passed.

**T7 — Full 6-venue regression scrape.**
```
cd /home/waynehoy/Projects/sf-jazz-city && .venv/bin/python scraper/run_scraper.py --export
```
1. Exit code 0.
2. `data/events.json` is valid JSON and is a non-empty array.
3. Let `today` = the UTC date of the run. For each venue, compare the count of
   events with `date >= today` in the new `data/events.json` against the same
   count computed from `git show HEAD:data/events.json` **using the same
   `today`** (so both sides shift together as the calendar moves).
   Pass: every venue's new upcoming count is **>= 80%** of its baseline count,
   **except Mr. Tipple's**, whose floor is **>= 70%** (its count legitimately
   drops when entity duplicates merge — 45 → 42 observed).
4. No venue's upcoming count is 0.
5. The four healthy venues do not regress on images: for SFJAZZ Center, Dawn
   Club, Black Cat SF, and Keys Jazz Bistro, **>= 95%** of upcoming events have
   a non-empty `image_url`. (Baseline: all four at 100%.)

**T8 — Yoshi's image yield (the D-i1 headline).** From the same
`data/events.json` produced by T7 (or after
`.venv/bin/python scraper/run_scraper.py --venue yoshis --export`):
Among Yoshi's events with `date >= today`, the fraction whose `image_url`
(a) is non-null and non-empty, (b) starts with `https://yoshis.com/`, and
(c) does not start with `data:`, is **>= 70%**.
*Spec-phase measurement: 70/70 detail pages carried an image (100%). Expect
~100%; below ~90% warrants investigation.*

**T9 — Mr. Tipple's image yield.** Among Mr. Tipple's events with
`date >= today`, the fraction whose `image_url` is non-null, non-empty, starts
with `https://`, and does not start with `data:`, is **>= 50%**.
*Spec-phase measurement with both fixes applied: 14/14 upcoming (100%),
37/42 overall (88%).*

**T10 — Post-run data hygiene.** Against `data/events.json` from T7:
1. No event of any venue has `image_url == ""` (C4).
2. No event has an `image_url` starting with `data:`.
3. No Yoshi's or Mr. Tipple's event has a **relative** `image_url` (every
   non-null value starts with `http://` or `https://`) — a relative URL would
   resolve against the Next.js host and 404, since the frontend hotlinks
   `image_url` directly and `isValidImageUrl` would not reject it.
4. No Mr. Tipple's event title contains `&#` (C18, C21).

**T11 — Frontend untouched (C24, C25).**
1. `cd /home/waynehoy/Projects/sf-jazz-city && npm test` exits 0.
2. `git diff --name-only HEAD` lists **no** path starting with `app/`.
3. `git diff --name-only HEAD` lists **no** path starting with `scraper/images/`
   and does not include `scraper/image_downloader.py`.

**T12 — Politeness (C10, C11).** Static check on `scraper/yoshis_scraper.py`:
1. The source contains an `asyncio.Semaphore(n)` with `n <= 4` guarding detail
   fetches.
2. A single `aiohttp.ClientSession` is used for the calendar POST and all
   detail GETs within a run.
3. Instrumented check: during a Yoshi's-only run, the number of detail-page GETs
   is **<= the number of unique detail URLs** (proving the per-URL cache of
   C10). With today's feed that is <= 70 for 118 events.

**T13 — Failure degradation (C12).** With the detail-fetch helper monkeypatched
to raise on every call, `scrape_events()` still returns the full set of Yoshi's
events (same count as with fetching disabled), every `image_url` is `None`, and
no exception propagates.

---

## 6. Cost / time estimate

Estimated for the remaining phases of this cycle (Execution + Verification).
**The budget-breach threshold is 1.5× these figures.**

| Phase | Wall clock | Spend |
|---|---|---|
| Execution (M1–M3 implementation) | 50–80 min | $7–12 |
| Verification (write + run T1–T13) | 50–85 min | $7–13 |
| **Total (point estimate)** | **~2.5 h** | **~$20** |

**Breach threshold at 1.5×: ~3.75 h / ~$30.**

Work being estimated:
- `scraper/image_utils.py`: new, ~40 lines.
- `scraper/yoshis_scraper.py`: ~55 lines added/changed (2 pure helpers +
  bounded async fetch layer).
- `scraper/mrtipples_scraper.py`: ~30 lines changed (`merge_events`,
  `html.unescape`, `normalize_image_url` wiring).
- Cleanup routine (C21): ~25 lines.
- Fixture capture + trimming: 3 files.
- Verification test files: ~250 lines across 4–5 files.
- Live runs: at least one full 6-venue scrape.

**What drives the uncertainty (in descending order):**
1. **Full-venue scrape wall clock.** Four of six venues drive a headless Chrome
   session. A full `--export` run is the single longest step and may be
   repeated 2–3 times (regression, then post-fix, then a re-run if a venue
   flakes). This is the largest variance term and is mostly *waiting*, not
   spend.
2. **Mr. Tipple's is Cloudflare-protected** — plain `curl` gets HTTP 403; only
   the Playwright path works. A bot-check escalation on the day would stall T9
   and T7 and could force a retry cycle.
3. **Live sites are moving targets.** All yield figures here were measured on
   2026-08-26. Yoshi's could re-skin its detail template (removing
   `class="event-img"`) between approval and verification, which would fail T8
   through no fault of the implementation.
4. **Fixture trimming.** Reducing a 166 KB page while preserving the four
   required elements (T2) can take a couple of iterations.

**Why this is cheaper than ideation implied:** ideation budgeted detail-page
fetching for both venues. The probe eliminated it for Mr. Tipple's entirely
(D-s2) and measured it at 8.7 s / 70 requests for Yoshi's — so the "roughly
doubles request counts for these venues" concern in ideation applies to one
venue and costs under 10 seconds per run.

---

## 7. Risks

| # | Risk | Mitigation / blast radius |
|---|---|---|
| R1 | Yoshi's changes its detail template and drops `class="event-img"` | T8 fails loudly. C12 guarantees graceful degradation to today's behavior (no images) rather than a crashed venue. Fix is a one-line selector change. |
| R2 | Yoshi's rate-limits or blocks 70 sequential detail GETs | Probe saw 70/70 at concurrency 4 in 8.7 s with no throttling. C11 caps concurrency at 4; C12 makes any 429/403 degrade to `image_url=None`. |
| R3 | Mr. Tipple's Cloudflare check hardens and blocks Playwright | Pre-existing risk for this venue, not introduced here. Blocks T9/T7 and would need a separate cycle. |
| R4 | `html.unescape` changes the `(title, date)` DB unique key, orphaning existing rows | Quantified: exactly 13 rows, all with decoded twins. C21–C23 resolve them losslessly. If D-s4 is vetoed, blast radius is ~2 visible duplicate upcoming cards. |
| R5 | `merge_events` merges two genuinely distinct same-night shows that share a title and date | Mr. Tipple's already dedups on `(title, date)`; this changes *which field values survive*, not *which events collapse*. Event count is unchanged except for the 3 intended entity merges. T5.5 guards distinct keys. |
| R6 | Yoshi's detail-fetch layer accidentally overwrites `ticket_url` with the detail URL | Directly guarded by C13 and T3.2 — the most likely silent regression in this cycle. |
| R7 | A committed 166 KB HTML fixture bloats the repo | Fixture trimming is explicitly permitted; required elements enumerated in §5. |
| R8 | Live thresholds (70%/50%) are so far below measured yield (100%) that a real partial regression passes | Deliberate: the thresholds are Wayne-approved from ideation and are not raised unilaterally. §5 Layer 2 instructs flagging a large gap between threshold and expectation to the human gate. |

---

## 8. Alternatives rejected

- **Fetch Yoshi's detail pages with Playwright** (as Mr. Tipple's does).
  Rejected: the pages are plain server-rendered HTML — `curl` returns the full
  markup with the image. `aiohttp` costs 8.7 s for 70 pages; a browser would
  cost minutes.
- **Use `og:image` / JSON-LD for Yoshi's** (ideation's stated assumption).
  Rejected: the detail pages serve exactly three meta tags — `description`,
  `google-site-verification`, `viewport` — and zero JSON-LD blocks. Measured.
- **Fetch Mr. Tipple's detail pages** (ideation's D-i2 "likely fix").
  Rejected: the JSON-LD already carries 73/83 images; the loss is a dedup bug.
  Detail fetching would add ~45 browser navigations and mask the real defect.
- **Repair the dead DOM path** so it also yields images. Rejected: it currently
  contributes 0 images and 0 unique events; after C15–C17 it is inert. Out of
  scope (§4.6).
- **Change Mr. Tipple's dedup key to include `time`** (matching Yoshi's).
  Rejected: would split legitimately-merged rows and change event counts,
  breaking T7's count comparison for no image benefit.
- **Drop the DOM path entirely** from Mr. Tipple's. Rejected: it is the
  documented fallback if the JSON-LD block ever disappears; C15's merge makes
  it harmless to retain.
- **Backfill all historical rows** with images. Rejected by D-i5; only the 13
  rows of C21 are touched, and only because D-s3 would otherwise strand them.
- **Validate `image_url` by fetching it.** Rejected: doubles request volume,
  introduces flakiness into unit tests, and the frontend already degrades to a
  placeholder on a broken image.
- **Write the tests as part of Execution.** Rejected: the Loop protocol
  requires a fresh Verification session to implement them from this spec alone.
- **Use BeautifulSoup for HTML extraction.** Rejected: `bs4` is not installed in
  `.venv` and D-s6 forbids new runtime dependencies. Stdlib `re`/`html.parser`
  suffices; T2.5–T2.9 pin the robustness requirements a regex must meet.

---

## 9. Milestones

- **M1 — Shared + Yoshi's.** `scraper/image_utils.py` (C1–C4);
  `extract_image_url`, `detail_url_from_item`, bounded detail-fetch layer
  (C5–C14). Largest milestone.
- **M2 — Mr. Tipple's + cleanup.** `merge_events`, entity decoding, image
  normalization (C15–C20); one-shot cleanup (C21–C23).
- **M3 — Live run + export.** Full 6-venue scrape, `data/events.json` refresh,
  scope-integrity check (C24–C26).

Three milestones is within the single-cycle threshold; no split is proposed.
