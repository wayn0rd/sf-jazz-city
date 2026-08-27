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
