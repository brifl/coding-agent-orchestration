# Test Generation Guide

> Advisory guidance for the `continuous-test-generation` workflow. Used by
> `prompt.test_gap_analysis` and `prompt.test_generation` to inform gap selection,
> test design, and impact tagging. These are heuristics — not hard rules.

---

## Impact Tag Definitions

Every gap candidate must carry exactly one bracketed tag:

| Tag | Meaning |
|-----|---------|
| `[MAJOR]` | High-risk untested path; failure here would be hard to detect or diagnose |
| `[MODERATE]` | Meaningful coverage gap with a clear, bounded test target |
| `[MINOR]` | Low-risk polish; nice to have but unlikely to catch real bugs |

Do not use issue-impact labels (`BLOCKER`, `QUESTION`) for gap candidates.

---

## What to Prioritize

### [MAJOR] — High-risk gaps

- **Untested error paths** — exception handling, timeout recovery, and partial-failure
  branches are the most commonly broken and the least tested.
- **Boundary conditions on inputs** — off-by-one, empty collections, None/null, max-size.
- **Recently changed code with no test update** — regression risk is highest immediately
  after a change.
- **Public API surface** — any function or class that external callers depend on should
  have contract tests.
- **State transitions** — code that moves through explicit states (status fields, workflow
  flags) needs tests for each valid transition and each invalid one.

### [MODERATE] — Meaningful scoped gaps

- **Happy-path coverage for non-trivial logic** — functions with branching that have only
  manual or integration-level verification.
- **Integration seams** — places where two modules interact that are untested end-to-end
  but testable with a simple fixture.
- **Retry and idempotency behavior** — especially for anything that touches external
  systems or writes state.

### [MINOR] — Low-risk polish

- Additional parametrize cases for already-covered logic.
- Doctest examples for pure utility functions.
- Snapshot/characterization tests for stable output formats.

---

## Gap Analysis Checklist

Use as a lightweight scan lens, not an exhaustive checklist:

1. **Recent changes** — What was modified in the last few commits with no test change?
2. **Error branches** — Do `except` blocks, `if error:` paths, and fallbacks have tests?
3. **Boundary inputs** — Empty, None, zero, max, and type-mismatch cases covered?
4. **State machines** — Are illegal transitions tested to be rejected?
5. **Public contracts** — Does every exported function have at least one contract test?
6. **Flakiness signals** — Any tests that pass/fail non-deterministically? Root-cause first.

---

## Test Design Principles

- **One assertion per concept** — tests that assert many things at once are hard to
  diagnose when they fail.
- **Descriptive names** — `test_loop_result_rejects_wrong_workflow` beats `test_lr_2`.
- **Prefer real objects over mocks** for the system under test; mock only at external
  boundaries (network, filesystem, clock).
- **Deterministic** — no time.sleep, no random seeds, no network calls in unit tests.
- **Fast** — unit tests should run in milliseconds; isolate slow tests into a separate
  suite.

---

## Effort / Risk Reference

| Effort | Description |
|--------|-------------|
| S | Single function; <20 lines of test code |
| M | Multiple cases or a fixture; <100 lines |
| L | New test module or significant fixture infrastructure |

| Risk | Description |
|------|-------------|
| low | Pure function; no side effects; easy to assert |
| med | Requires a fixture or mock; behavior has some branching |
| high | Touches shared state, external systems, or concurrency |

---

## Anti-Patterns to Avoid

- **Do not** write tests that only assert the implementation rather than the contract.
- **Do not** mock the system under test itself.
- **Do not** add tests for already-covered happy paths when high-risk gaps remain.
- **Do not** batch multiple independent gaps into a single test function.
- **Do not** change production code to make a test pass unless the production code is
  genuinely wrong — flag as scope creep instead.

---

## Candidate Generation Strategy

To avoid anchoring on the first gap, scan across at least 3 lenses:

- **Risk-first** — what failure would be hardest to detect in production?
- **Change-first** — what code changed recently without a corresponding test change?
- **Contract-first** — what public interfaces lack explicit behavioral assertions?

Then rank by impact and pick the highest-value gap that can be tested in a single
bounded loop.
