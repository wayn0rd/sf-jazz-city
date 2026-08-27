<!-- assumptions.md — provisional assumption record; never ground truth until reviewed. -->

### assumption-0001
**Undecided:** spec.md C10 requires "a setup file importing `@testing-library/jest-dom`" but §1's file manifest does not name it or give it a path.
**Chosen:** `vitest.setup.ts` at the repo root, referenced from `vitest.config.ts` via `setupFiles`.
**Why:** Keeps the setup file out of `tests/`, which §6.0 reserves for Verification's own files, so Verification can create, move, or clear that directory without breaking the runner.
**Wrong if:** Verification (or a later reviewer) expects the setup file at `tests/setup.ts` and overwrites `vitest.config.ts`, or a convention emerges that repo-root config files must be limited to §1's manifest exactly.

### assumption-0002
**Undecided:** which entry point of `@testing-library/jest-dom` the setup file imports. C10 names the bare package.
**Chosen:** `import '@testing-library/jest-dom/vitest'`.
**Why:** The installed version is 7.0.1, whose Vitest entry point is the one that registers matchers on Vitest's `expect` *and* augments Vitest's matcher types; the bare import types the Jest namespace instead, which would make `expect(x).toBeInTheDocument()` fail `npx tsc --noEmit` (gate T-B-7). Verified: a throwaway test using that matcher passed both `npm test` and `tsc --noEmit`.
**Wrong if:** a grader reads C10 as requiring the literal specifier `@testing-library/jest-dom`, or jest-dom drops the `/vitest` subpath export.

### assumption-0003
**Undecided:** C10 lists six dev dependencies; two more are needed for that set to actually install and typecheck.
**Chosen:** additionally installed `@testing-library/dom` (required peer of `@testing-library/react@16`) and `@types/react-dom@^18` (pinned to ^18; the floating `@types/react-dom@19` conflicts with the repo's `@types/react@^18`).
**Why:** Without `@testing-library/dom` the RTL peer graph is unsatisfied; without `@types/react-dom` a React DOM import in a test file fails `tsc --noEmit`. Neither adds runtime surface — both are dev-only.
**Wrong if:** the project later upgrades to React 19, at which point the `^18` pin on `@types/react-dom` becomes the wrong constraint.

### assumption-0004
**Undecided:** `vitest.config.ts` `test.include` — §6.0 says tests live under `tests/`, so a `tests/**` glob would be defensible.
**Chosen:** left at Vitest's default include glob rather than narrowing it to `tests/**`.
**Why:** A narrowed glob fails silently — a Verification test file written outside `tests/` would be skipped and `vitest run` would still exit 0 under `passWithNoTests`, reporting a green run that tested nothing. The default glob is strictly more permissive and still satisfies C10.
**Wrong if:** stray `*.test.ts` files elsewhere in the repo (or in a future vendored directory) get picked up and fail the suite.

### assumption-0005
**Undecided:** `npx tsc --noEmit` (gate T-B-7) writes `tsconfig.tsbuildinfo` because `tsconfig.json` sets `"incremental": true`; the spec does not say whether that artifact is committed.
**Chosen:** added `*.tsbuildinfo` to `.gitignore` rather than committing it.
**Why:** It is a machine-local incremental-build cache, not a source artifact, and committing it would churn the diff on every typecheck. `.gitignore` is not on the untouchable list and no commitment covers it.
**Wrong if:** the project wants a fully reproducible committed build cache, or a reviewer scores any file outside spec §1's manifest as out-of-scope.

### assumption-0006
**Undecided:** spec.md C11 requires `npm run lint` to exit 0, but the repo has no ESLint config file, so `next lint` opens an interactive "How would you like to configure ESLint?" prompt and exits 1. The spec's §1 manifest does not list an ESLint config.
**Chosen:** added `.eslintrc.json` extending `next/core-web-vitals`, with `ignorePatterns` for `node_modules/`, `.next/`, `scraper/`, `data/`.
**Why:** C11 is unsatisfiable without one; `next/core-web-vitals` is the option `next lint`'s own prompt marks "(recommended)", so it is the least-invented choice. The ignore patterns keep the linter off the Python scraper and the data files, both of which §3 puts out of scope.
**Wrong if:** the project prefers flat config (`eslint.config.mjs`), or wants the "Base" preset — `core-web-vitals` emits two `@next/next/no-img-element` warnings for the raw `<img>` tags that §3 explicitly preserves. They are warnings, not errors, so lint still exits 0; verified before and after the refactor.

### assumption-0007
**Undecided:** C7 says each venue card "is (or contains) a `<Link>`", leaving the choice open.
**Chosen:** the `venue-card` element is a `<div>` that *contains* the `<Link>`, rather than being the anchor itself.
**Why:** T-C7-4 reads "Each card contains an `<a>` whose href is ...". If the card element were itself the anchor, the natural query (`within(card).getByRole('link')` / `card.querySelector('a')`) would find nothing and the test would fail on a technicality. Containing the link satisfies both readings.
**Wrong if:** a reviewer wants the entire card to be one anchor for a larger click target, in which case the wrapper div should be dropped and T-C7-4 read as "the card *is* the `<a>`".

### assumption-0008
**Undecided:** C8 requires `venue-not-found` to be "present" with "visible text `Venue not found`", and also requires a sibling back-link. It does not say whether the testid goes on a container holding both, or on the text element alone.
**Chosen:** `data-testid="venue-not-found"` sits on the `<h1>` whose text is exactly `Venue not found`; the back link is a sibling, not a child. The same pattern is used for `venues-loading`, `venues-error`, `venues-empty` and `venue-loading`.
**Why:** §6.0 rule 5 makes text assertions exact-match on trimmed `textContent`. Had the testid been on a container wrapping the link too, its trimmed text would be `Venue not foundBack to all venues` and an exact-match assertion would fail.
**Wrong if:** Verification asserts with `toHaveTextContent` (substring) and separately expects the back link to be a descendant of `venue-not-found`.

### assumption-0009
**Undecided:** C4 puts `<h1>SF Jazz City</h1>` in the shared header while C7 and C8 each require a page-level `<h1>`, so every venue page renders two `<h1>` elements. The spec does not reconcile this.
**Chosen:** implemented both as written — header `<h1>` plus page `<h1>` — rather than demoting either to `<h2>`.
**Why:** Both are explicit spec commitments; silently downgrading one to satisfy a document-outline preference would be substituting my design for a spec commitment. Flagging it because it is a trap: an unnamed `getByRole('heading', { level: 1 })` query will throw "multiple elements". Query by `data-testid`, or by accessible name (`{ level: 1, name: 'Venues' }`), which is what I verified against.
**Wrong if:** a single top-level heading per page is a hard requirement, in which case C4's header heading should become a `<p>` or `<h2>` via a spec amendment.
