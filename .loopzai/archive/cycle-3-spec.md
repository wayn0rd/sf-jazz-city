<!-- spec.md — Specification phase output for cycle 3. Frozen at spec-approval gate. -->

# Cycle 3 Specification — SF Jazz History editorial page

**Status:** awaiting spec-approval gate
**Input:** `.loopzai/ideation.md` (frozen, commit `9d8f671`)
**Milestones:** 3 (M1, M2, M3) — well below the split threshold; one cycle is correct.

---

## 0. Executive summary — read this before the estimate

This is a small, low-risk, purely additive frontend cycle. During Specification
I built the **entire feature end-to-end in a throwaway scratch copy** of the repo
(hardlinked `node_modules`, outside the working tree; deleted afterward — the repo
source was never modified). It worked on the first attempt. Every number in the
test plan below is a **measured observation, not a projection**.

What the probe established:

| Question | Answer (measured 2026-08-30) |
|---|---|
| Does `react-markdown` render this essay correctly? | **Yes.** 1 `<h1>`, 8 `<h2>`, 33 `<p>`, 5 `<em>` |
| Can React Testing Library render an `fs`-reading server component? | **Yes — if the component is synchronous.** See D-s2 |
| Does `next build` succeed? | **Yes.** `/history` prerenders as **○ Static, 172 B** |
| Does the markdown ship to the browser? | **No.** Rendered at build time; `.next/server/app/history.html` contains the full essay |
| Does adding a 4th nav link break cycle-2's frozen tests? | **No.** No existing test asserts a nav link count |
| Baseline suites | **59 vitest tests (5 files) + 95 pytest tests, all green** |
| Dependency cost of `react-markdown@10.1.0` | **77 transitive packages** |

Two findings materially shaped the test plan and would have caused problems if
discovered later:

1. **The rendered document contains two `<h1>` elements** — `SiteHeader`'s brand
   ("SF Jazz City") and the essay title. A natural test written as
   `getByRole('heading', { level: 1 })` throws on ambiguity. Every heading
   assertion in §6 is therefore **scoped to the essay container**, never to
   `document`.
2. **The essay contains italic markup my first content scan missed** — five
   album/record titles wrapped in `*...*` (e.g. `*Thelonious Alone in San
   Francisco*`). A components map covering only `h1`/`h2`/`p` still renders
   these correctly via react-markdown's defaults, but the test plan now pins
   them so a future "simplify the renderer" change cannot silently flatten
   album titles into plain text.

**The essay already exists.** `app/history/essay.md` (83 lines, 2,031 words,
sha256 `8787ac29…`) was committed by the Ideation phase in `9d8f671`. Writing or
editing prose is **not** part of this cycle — C6 forbids touching the file.

---

## 1. Decisions made in this phase (each independently vetoable)

- **D-s1 — Use `react-markdown@^10` as ideation specified.** Frozen by ideation;
  I verified it works. See §8 for the cheaper alternative I rejected and why you
  might still prefer it.
- **D-s2 — `app/history/page.tsx` must be a *synchronous* (non-`async`) server
  component.** This is the single most important implementation constraint in
  this spec. An `async` server component cannot be rendered by React Testing
  Library, which would make the entire §6 test plan unimplementable. A
  synchronous component using `fs.readFileSync` renders fine in jsdom. Not a
  style preference — a testability requirement.
- **D-s3 — The essay is read via `path.join(process.cwd(), 'app/history/essay.md')`.**
  Verified working under both `vitest` (cwd = repo root) and `next build`.
- **D-s4 — The page includes `SiteFooter`.** Ideation is silent on the footer;
  every other page in the site has one. Veto this line alone if you want the
  essay to end without it.
- **D-s5 — Style assertions test *class tokens*, not full class strings.** Tests
  assert `classList.contains('text-amber-400')`, never
  `className === '...exact string...'`. This pins the commitments ideation made
  while leaving Execution free to add spacing/responsive utilities.
- **D-s6 — Exact structural counts (1/8/33/5) are frozen as assertions.** These
  are legitimate because C6 forbids modifying `essay.md`; together with the
  sha256 check (T5) they prove the essay rendered *completely and unaltered*,
  which a "title appears" smoke test would not.
- **D-s7 — No changes to `layout.tsx`.** Page-level `metadata` export is
  sufficient for the title; the root layout stays untouched.

---

## 2. Scope boundary — what this cycle will NOT do

Deferred from `ideation.md` (explicitly listed there as out of scope):

- **Mobile navigation.** The nav stays `hidden md:flex`. The "SF Jazz History"
  link will be **invisible on mobile viewports**, exactly like the existing
  three. This is accepted, not overlooked. T3-4 pins it so it cannot drift.
- No CMS or admin editing surface.
- No hero image, banner, or decorative imagery.
- No byline, author attribution, or publication date.
- No comments, sharing, or social-preview (`og:`) tags.

Additionally out of scope (my determinations, not ideation's):

- **No prose changes.** `essay.md` is byte-frozen (C6).
- **No `@tailwindcss/typography`.** Ideation ruled it out; the components map replaces it.
- No table-of-contents, heading anchor links, or in-page navigation.
- No reading-time estimate or progress indicator.
- No changes to `/`, `/venues`, `/venues/[slug]`, `/api/events`, or any scraper code.
- No new Convex schema or backend work — pure frontend addition.
- No refactor of `SiteHeader` beyond inserting one `<Link>`.

---

## 3. Milestones

| ID | Deliverable |
|---|---|
| **M1** | Add `react-markdown` dependency; create `app/history/page.tsx` rendering `essay.md` with the styled components map |
| **M2** | Add the "SF Jazz History" nav link to `SiteHeader` |
| **M3** | Page metadata title; full regression green (vitest + pytest + `next build`) |

---

## 4. Commitments

Each commitment is verified by the correspondingly-numbered tests in §6.

### C1 — The `/history` route exists and renders the essay
`app/history/page.tsx` exports a default **synchronous** React component. It reads
`app/history/essay.md` from disk at render/build time and renders it through
`<ReactMarkdown>`. The route is reachable at `/history`.

### C2 — The essay renders completely and faithfully
Within the essay container, the rendered output contains **exactly**:
- 1 `<h1>` — `The Rhythms of the City: A History of San Francisco Jazz`
- 8 `<h2>`, in this exact document order:
  1. `Terrific Street`
  2. `The Revival at the Dawn Club`
  3. `The Fillmore`
  4. `The Blackhawk and the Jazz Workshop`
  5. `The Beats and the Cool School`
  6. `Survival and Fusion`
  7. `SFJAZZ and the Present`
  8. `Coda`
- 33 `<p>` elements
- 5 `<em>` elements, in this exact document order:
  1. `In Person: Friday and Saturday Nights at the Blackhawk`
  2. `Thelonious Alone in San Francisco`
  3. `Live at the Jazz Workshop`
  4. `A Charlie Brown Christmas`
  5. `Concert of Sacred Music`

No raw markdown syntax leaks into the rendered text.

### C3 — Visual design matches the ideation brief
Expressed as required Tailwind class tokens (D-s5):

| Element | Required class tokens |
|---|---|
| Outer page wrapper | `max-w-7xl`, `mx-auto`, `px-4`, `sm:px-6`, `lg:px-8` |
| Essay container (`data-testid="history-essay"`) | `max-w-2xl`, `mx-auto`, `bg-black/30`, `backdrop-blur-md`, `border`, `border-white/10`, `rounded-xl` |
| Essay `<h1>` | `text-white`, `font-bold` |
| Every `<h2>` | `text-amber-400`, `font-semibold` |
| Every `<p>` | `text-gray-200`, `leading-relaxed`, `mb-4` |

The page also renders `SiteHeader` (`data-testid="site-header"`) and `SiteFooter`
(`data-testid="site-footer"`).

### C4 — Navigation gains a fourth link
`SiteHeader` renders a link with `data-testid="nav-history"`, `href="/history"`,
and exact text `SF Jazz History`, inside the same `<nav>` as the existing three.
The existing three links are unchanged. The nav container retains `hidden` and
`md:flex`.

### C5 — Page title metadata
`app/history/page.tsx` exports `metadata` whose `title` is exactly:

```
SF Jazz History — SF Jazz City
```

The separator is **U+2014 EM DASH**, with one ASCII space on each side.

### C6 — The essay file is not modified
`app/history/essay.md` has sha256
`8787ac29ab84986b4927a66ce649b512feb2396e4cfe7559d911f83a72a993e5`
at the end of the cycle — byte-identical to its state at ideation freeze.

### C7 — Build-time rendering, no client-side markdown
The page is **not** a client component (no `"use client"`), and neither is any
new component it introduces. `next build` prerenders `/history` as static HTML
containing the fully-rendered essay.

### C8 — No regressions
`next build` exits 0. All pre-existing tests still pass: **≥59** vitest tests and
**95** pytest tests. `react-markdown` appears in `dependencies` (not
`devDependencies`) in `package.json`, and `package-lock.json` is updated.

---

## 5. Interfaces

```
app/history/page.tsx     (new)      default export: synchronous React component
                                    named export:   metadata
app/history/essay.md     (existing) READ-ONLY this cycle
app/components/SiteHeader.tsx (modified) +1 <Link>, no other change
package.json             (modified) +react-markdown in dependencies
package-lock.json        (modified) lockfile update
tests/history.test.tsx   (new)      authored by Verification, not Execution —
                                    the executable form of the §6 test plan
```

**Required `data-testid` attributes** (the contract between Execution and
Verification — Verification sees only this spec, so these names are binding):

| testid | Element |
|---|---|
| `history-essay` | The container wrapping the rendered markdown |
| `nav-history` | The new nav link |
| `site-header` / `site-footer` | Existing, unchanged |

**File-creation boundary.** Execution may create or modify only the four files
marked `(new)`/`(modified)` above other than `tests/history.test.tsx`, namely:
`app/history/page.tsx`, `app/components/SiteHeader.tsx`, `package.json`,
`package-lock.json`.

`tests/history.test.tsx` **is expressly permitted and expected** — it is created
by the **Verification** phase as the executable form of the §6 test plan, and is
listed in T7-6's allowed set. Execution does not write it.

No file outside these five may be created or modified.

---

## 6. Test plan (FROZEN)

Verification implements these from this document alone. It may add checks; it may
never remove or weaken one. New JS tests go in `tests/history.test.tsx`.

**Standing conventions** (match the existing suite):
- `import HistoryPage from '@/app/history/page'`, render with
  `@testing-library/react`, `afterEach(cleanup)`.
- **All DOM queries in T1–T2 are scoped to the `history-essay` container**
  (`within(...)` or `container.querySelectorAll`). Never query `document`
  globally for headings — there are two `<h1>`s on the page (see §0).
- Text comparisons use exact `textContent` after `.trim()`.
- **All apostrophes in the essay are ASCII `'` (U+0027); the file contains zero
  U+2019 characters, and react-markdown does not smart-quote.** Every quoted
  string in this test plan is therefore to be typed with plain ASCII quotes and
  apostrophes. The one exception is the em dash in C5/T4, which is U+2014.

### T1 — Essay content (verifies C1, C2)

| ID | Assertion | Pass criterion |
|---|---|---|
| T1-1 | Page renders without throwing; `history-essay` exists | `getByTestId('history-essay')` returns an element |
| T1-2 | Exactly one `<h1>` in container | `container.querySelectorAll('h1').length === 1` |
| T1-3 | `<h1>` text | `=== 'The Rhythms of the City: A History of San Francisco Jazz'` |
| T1-4 | Exactly eight `<h2>` in container | `length === 8` |
| T1-5 | `<h2>` texts in DOM order | deep-equals the 8-item array in C2 |
| T1-6 | Exactly 33 `<p>` in container | `length === 33` |
| T1-7 | First `<p>` opening text | `startsWith("San Francisco's relationship with jazz goes back nearly to the music's beginning.")` |
| T1-8 | Last `<p>` closing text | `endsWith('keep the song moving.')` |
| T1-9 | Exactly five `<em>` in container | `length === 5` |
| T1-10 | `<em>` texts in DOM order | deep-equals the 5-item array in C2 |
| T1-11 | No raw markdown leaks | container `textContent` contains no `'##'` and no `'*'` |

### T2 — Visual design (verifies C3)

| ID | Assertion | Pass criterion |
|---|---|---|
| T2-1 | Essay container classes | `classList` contains each of `max-w-2xl`, `mx-auto`, `bg-black/30`, `backdrop-blur-md`, `border`, `border-white/10`, `rounded-xl` |
| T2-2 | Outer wrapper classes | some ancestor of `history-essay` has `classList` containing all of `max-w-7xl`, `mx-auto`, `px-4`, `sm:px-6`, `lg:px-8` |
| T2-3 | `<h1>` classes | contains `text-white` and `font-bold` |
| T2-4 | **Every** `<h2>` classes | all 8 contain `text-amber-400` and `font-semibold` |
| T2-5 | **Every** `<p>` classes | all 33 contain `text-gray-200`, `leading-relaxed`, `mb-4` |
| T2-6 | Header and footer present | `site-header` and `site-footer` both found |

### T3 — Navigation (verifies C4)

| ID | Assertion | Pass criterion |
|---|---|---|
| T3-1 | `nav-history` link | render `SiteHeader`; element exists, `tagName === 'A'`, `href === '/history'`, text `=== 'SF Jazz History'` |
| T3-2 | Existing links unchanged | `nav-tonight`→`/#tonight`, `nav-upcoming`→`/#upcoming`, `nav-venues`→`/venues`, texts `Tonight`/`Upcoming`/`Venues` |
| T3-3 | Link is inside the nav | `nav-history`'s closest `<nav>` is the same node as `nav-venues`'s closest `<nav>` |
| T3-4 | Nav stays desktop-only | that `<nav>`'s `classList` contains `hidden` and `md:flex` |
| T3-5 | Link reachable from the history page | rendering `HistoryPage` also yields a `nav-history` element |

### T4 — Metadata (verifies C5)

| ID | Assertion | Pass criterion |
|---|---|---|
| T4-1 | Title string | `import { metadata } from '@/app/history/page'`; `metadata.title === 'SF Jazz History — SF Jazz City'` |
| T4-2 | Em dash, not hyphen | `metadata.title.includes('—')` is `true`; `.includes(' - ')` is `false` |

### T5 — Essay integrity (verifies C6)

| ID | Assertion | Pass criterion |
|---|---|---|
| T5-1 | sha256 of `app/history/essay.md` | `=== '8787ac29ab84986b4927a66ce649b512feb2396e4cfe7559d911f83a72a993e5'` (compute in-test with `node:crypto`) |

### T6 — Build & static rendering (verifies C7)

Run once, from the repo root:

```bash
npx next build
```

| ID | Assertion | Pass criterion |
|---|---|---|
| T6-1 | Build succeeds | exit code 0 |
| T6-2 | `/history` prerendered | file `.next/server/app/history.html` exists |
| T6-3 | Essay is in the static HTML | that file contains `The Rhythms of the City` |
| T6-4 | All sections prerendered | that file contains exactly 8 occurrences of `<h2` |
| T6-5 | Not a client component | `grep -r "use client" app/history/` returns no matches |
| T6-6 | Route marked static | the build's route table line for `/history` begins with `○` |

### T7 — Regression (verifies C8)

| ID | Assertion | Pass criterion |
|---|---|---|
| T7-1 | JS suite green | `npx vitest run` exits 0, **0 failures**, total passing ≥ 59 + (new tests) |
| T7-2 | Pre-existing JS files still pass | `tests/components.test.tsx`, `tests/homepage.test.tsx`, `tests/lib.test.ts`, `tests/venue-detail.test.tsx`, `tests/venues-index.test.tsx` all pass |
| T7-3 | Python suite green | `.venv/bin/python -m pytest tests/scraper -q` → exactly **95 passed**, 0 failed |
| T7-4 | Dependency placement | `package.json` `.dependencies['react-markdown']` is a non-empty string; the key is absent from `devDependencies` |
| T7-5 | Lockfile updated | `package-lock.json` contains `node_modules/react-markdown` |
| T7-6 | No stray file changes | `git status --porcelain` lists only: `app/history/page.tsx`, `app/components/SiteHeader.tsx`, `package.json`, `package-lock.json`, `tests/history.test.tsx` (plus `.loopzai/` coordinator files) |

**Total: 34 frozen checks.**

---

## 7. Risks

| # | Risk | Mitigation / status |
|---|---|---|
| R1 | An `async` page component would make T1–T4 unimplementable | **Neutralized by D-s2** — made an explicit, tested commitment |
| R2 | Two `<h1>`s on the page cause ambiguous-query test failures | **Neutralized** — all T1/T2 queries scoped to the container |
| R3 | `react-markdown@10` is ESM-only; could break vitest or Next | **Falsified by probe** — both work unmodified |
| R4 | 77 transitive packages for a 3-element renderer | Real but accepted; see §8 A1 for the veto path |
| R5 | Exact counts (33 `<p>`) are brittle if the essay is edited | Intentional — C6/T5-1 forbid editing it this cycle. A future prose edit will require a spec amendment, which is the correct signal |
| R6 | `process.cwd()` differs under some runners | Verified under both `vitest` and `next build`; no other runner is used |
| R7 | Feature invisible on mobile (`hidden md:flex`) | Accepted and deferred by ideation; T3-4 pins it deliberately |
| R8 | Supply-chain risk from a new dependency tree | Accepted; `react-markdown` is a mainstream, widely-audited package |

---

## 8. Alternatives rejected

- **A1 — Hand-rolled ~30-line markdown renderer instead of `react-markdown`.**
  The essay uses only `#`, `##`, paragraphs, and `*italic*`. A small mapper would
  cover it with zero dependencies and 77 fewer packages. **Rejected because
  ideation froze `react-markdown`** — but this is the most defensible single veto
  in this spec. Vetoing it changes only D-s1/C8/T7-4; §6's other 31 checks stand
  unaltered, because they assert *rendered output*, not the library.
- **A2 — `@tailwindcss/typography` (`prose` classes).** Rejected by ideation;
  would also conflict with the explicit per-element colors in C3.
- **A3 — Essay as a `.tsx` constant or JSX.** Rejected: defeats ideation's goal of
  editing prose as a plain file.
- **A4 — `async` server component with `fs/promises`.** Rejected: untestable via
  RTL (R1). No benefit — the read is ~12 KB at build time.
- **A5 — Import the markdown via a webpack/turbopack loader.** Rejected: needs
  `next.config.js` changes and a type shim for marginal gain.
- **A6 — Fetching the essay at runtime from `/api/`.** Rejected: adds a request
  and a loading state to static content.
- **A7 — Adding mobile nav in this cycle.** Rejected: explicitly deferred by
  ideation; it is a `SiteHeader` redesign touching every page, and belongs in its
  own cycle.

---

## 9. Cost & time estimate

**Basis:** unusually firm. The full implementation was built and run during
Specification, so this estimates *transcription and verification of a known-good
change*, not discovery.

**Scale of the diff:** ~45 new lines (`page.tsx`), ~3 changed lines
(`SiteHeader.tsx`), 2 dependency-file updates. One `npm install` (~7 s observed).
Verification writes ~34 assertions in one new test file.

| Phase | Wall-clock | Spend |
|---|---|---|
| Execution | 15–25 min | $3 – $6 |
| Verification (author + run 34 checks) | 20–35 min | $4 – $8 |
| Coordinator / gate overhead | 5–10 min | $1 – $2 |
| **Cycle total (remaining)** | **40 – 70 min** | **$8 – $16** |

**Point estimate for the breach threshold: $12.**
Budget breach fires at 1.5× → **$18**.

**What drives the uncertainty (in order):**
1. **Verification test-authoring volume** — the largest single line item. 34
   checks across 7 groups, including two that shell out (`next build`, `pytest`).
   Deliberately front-loaded: precision here is the point of the cycle.
2. **`next build` runtime** — ~30–60 s per invocation; a retry loop is the main
   way T6 could inflate.
3. **A verification retry.** One retry (`maxAttempts: 3`) would add roughly
   $3–$5. The estimate above assumes **zero to one** retry. The probe makes a
   retry unlikely but not impossible — the residual risk is an Execution slip on
   D-s2 (`async` component) or a missing `data-testid`, both of which fail loudly
   and are cheap to fix.

**Explicitly *not* in this estimate:** any prose editing, mobile nav, or a
decision to swap out `react-markdown` mid-cycle (A1) — that last one would be a
spec amendment, not a cost overrun.

**Confidence:** high. This is the cheapest cycle of the three so far, and the
main thing that could make it expensive is scope creep, which §2 is written to
prevent.

---

## 10. Definition of done

1. All 34 frozen checks in §6 pass.
2. `npx next build` exits 0 and `/history` is statically prerendered.
3. `npx vitest run` and `pytest tests/scraper` are both green.
4. `git status` shows only the five expected files (T7-6).
5. `app/history/essay.md` is byte-identical to its ideation-freeze state.
