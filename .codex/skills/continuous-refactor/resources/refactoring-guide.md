# Refactoring Guide

> Advisory guidance for the `continuous-refactor` workflow. Used by `prompt.refactor_scan` to
> inform candidate selection and impact tagging. These are heuristics — not hard rules.
> A project-customized copy at `docs/refactoring-guide.md` takes precedence over the
> skill-bundled copy.

---

## Impact Tag Definitions

Every refactor candidate must carry exactly one bracketed tag:

| Tag | Meaning |
|-----|---------|
| `[MAJOR]` | High-leverage change with broad quality payoff across multiple concerns |
| `[MODERATE]` | Meaningful, scoped improvement with clear before/after |
| `[MINOR]` | Localized cleanup; low risk, low reward |

Do not use issue-impact labels (`BLOCKER`, `QUESTION`) for refactor candidates.

---

## What to Prioritize

### [MAJOR] — High-leverage targets

- **IO mixed with business logic** — functions that fetch data *and* transform it are hard to
  test in isolation and tightly couple transport concerns to domain logic.
- **Hidden global state / shared mutable singletons** — increases blast radius of changes and
  makes tests order-dependent.
- **Missing tests around high-churn or recently changed code** — highest risk; recommend
  adding targeted tests *before* the refactor, not after.
- **High cyclomatic complexity** — functions with >10 branches or deeply nested conditionals.
  Prefer early-return flattening or decomposition into named sub-steps.
- **Duplicated logic at 3+ call sites** — a single latent bug will exist in all copies.

### [MODERATE] — Meaningful scoped improvements

- **Unclear module/class boundaries** — a module doing two unrelated things is a split candidate.
- **Error-handling inconsistency** — mixing exceptions with error-code returns in the same layer
  confuses callers about the contract.
- **Long parameter lists (>5 args)** — usually signals a missing value-object or config struct.
- **Misleading names** — when a name contradicts what code actually does, it erodes trust faster
  than most other issues.
- **Dead code / unused exports** — removed once confirmed unused; do not wrap in flags.

### [MINOR] — Localized cleanup

- Trivial duplication (2 call sites, small helpers).
- Style/naming inconsistencies within a single file.
- Inline comments that restate what the code already says clearly.

---

## Scan Checklist

Use this as a lightweight scan lens, not an exhaustive checklist:

1. **Test coverage gaps** — What changed recently with no test? Mark as `[MAJOR]` risk if untested.
2. **IO / logic separation** — Does this function touch the network/DB *and* do computation?
3. **Cohesion** — Does each module/class have one clear responsibility?
4. **Coupling** — How many modules does this import from? How many import it?
5. **Complexity hotspots** — Long functions, deep nesting, many early returns.
6. **Error-handling contract** — Consistent within a layer?
7. **Global/shared state** — Thread-safety issues, hidden dependencies?

---

## Effort / Risk Reference

| Effort | Description |
|--------|-------------|
| S | Single function or file; <50 lines changed |
| M | Multiple files, clear bounded scope; <200 lines |
| L | Multiple modules or significant structural change |

| Risk | Description |
|------|-------------|
| low | Well-tested path; change is purely cosmetic or additive |
| med | Behavioral equivalence must be verified; tests exist but don't fully cover the change |
| high | Touches untested paths, shared state, or public/external API surface |

---

## Anti-Patterns to Avoid

- **Do not** propose a cross-cutting rewrite unless explicitly requested.
- **Do not** refactor code that lacks a test to prove equivalence — add the test first.
- **Do not** create abstractions (base classes, helpers, protocols) used by only one caller.
- **Do not** batch multiple independent refactors into a single checkpoint.
- **Do not** change observable behavior as part of a refactor without flagging it as scope creep.

---

## Candidate Generation Strategy

To avoid anchoring on the first idea, generate candidates across at least 3 strategy families:

- **Maintainability-first** — naming, cohesion, documentation, dead-code removal
- **Testability-first** — IO separation, dependency injection, seam introduction
- **Risk-reduction-first** — missing tests, error-handling consistency, shared-state elimination
- **Performance-first** — only when a profiling signal or obvious O(n²) pattern exists

Then cluster by root cause and deduplicate before ranking.
