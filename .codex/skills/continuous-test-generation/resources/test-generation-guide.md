# Test Generation Guide

> Advisory guidance for the `continuous-test-generation` workflow. Used by
> `prompt.test_gap_analysis` and `prompt.test_generation` to inform gap selection,
> test design, and impact tagging. These are heuristics — not hard rules.

---

## What should be tested (high value vs low value)

### The mental model: test *risk*, not code

A high value test reduces one of these risks:

1. **Behavioral risk:** a core rule changes accidentally.
2. **Integration risk:** components disagree at boundaries.
3. **Operational risk:** failures under real conditions (timeouts, retries, partial failure).
4. **Regression risk:** a bug you fixed comes back.
5. **Evolution risk:** refactors become unsafe because intent is not pinned.

If a test does not materially reduce one of these, it is usually low value.

---

## High value test targets

### 1) Domain invariants and business rules

Test the rules that define correctness.

* Invariants that must always hold (state validity, totals, permissions, ordering).
* Edge cases where rules flip (thresholds, rounding, “first item,” “empty,” “end of month”).
* Idempotency rules (“running it twice does not double apply”).
* State transitions (allowed vs forbidden, and their effects).

**Why high value:** small changes here cause high impact bugs.

---

### 2) Boundary contracts (ports, APIs, adapters)

Test what crosses boundaries, especially where types or trust change.

* Input validation and normalization.
* Error surfaces and mapping (what errors exist, how they are represented).
* Authz rules (who can do what).
* Semantic compatibility (versioning, deprecation behavior).
* Encoding/decoding and round trips (serialization, schema evolution).

**Why high value:** boundaries are where coupling, security, and integration failures concentrate.

---

### 3) Negative paths and failure modes

Test what happens when things go wrong.

* Timeouts, transient failures, retries.
* Partial failure handling (some operations succeed, some fail).
* Resource limits (payload too large, rate limited).
* External dependency misbehavior (bad data, slow responses).

**Why high value:** systems fail at the edges, not the happy path.

---

### 4) Bug regression tests (surgical)

For each meaningful bug, add a test that fails for the old behavior and passes for the fix.

**Why high value:** prevents reintroduction, documents intent, and improves confidence.

---

### 5) Metamorphic and property tests where oracles are expensive

Use invariants instead of enumerating examples.

Examples:

* Sorting: output is ordered; same multiset as input.
* Parsers: parse(serialize(x)) round trips.
* Pricing: monotonicity, non-negativity, conservation rules.
* Workflows: state machine invariants across random action sequences.

**Why high value:** wide coverage with fewer tests and fewer brittle fixtures.

---

### 6) A small number of integration “wiring proofs”

Pick a few tests that prove critical wiring:

* ORM mapping + migrations for one representative aggregate.
* One test per external service integration verifying auth + serialization + error mapping.
* A smoke test for the job runner / message consumer.

**Why high value:** catches “everything compiles but nothing works” errors.

---

## Low value test targets (or tests to rewrite)

### 1) Tests that mirror implementation details

* Asserting internal method calls, exact call order, or private helper behavior.
* Over-mocking: the test proves your mocks, not your system.

**Symptom:** harmless refactor breaks many tests.

---

### 2) Redundant happy-path examples

* Dozens of near-identical tests that cover the same rule with slightly different inputs, without targeting a boundary/edge/invariant.

Prefer one representative example plus property tests or targeted edge cases.

---

### 3) Snapshot tests of unstable output

* Snapshots of full HTML/JSON/log output where small formatting changes are common.

If snapshots are used, constrain them to stable contracts or normalize the output before snapshotting.

---

### 4) UI tests for logic that belongs below the UI

* End-to-end tests that validate business rules that could be unit/contract tested.

E2E should prove wiring and critical paths, not carry the weight of logic coverage.

---

### 5) Tests that hit real networks or shared environments by default

* “Integration tests” that depend on live services without hermetic control.

These produce noise and slow feedback; keep them quarantined and few.

---

## A practical prioritization rubric (quick scoring)

Score a proposed test 0–2 on each axis:

* **Impact:** how bad if this breaks?
* **Likelihood:** how likely it is to break during change?
* **Detectability:** would we notice without this test?
* **Isolation:** can it be fast and deterministic?
* **Contractness:** does it pin an important external or internal contract?

High value tests tend to score high on the first four, and at least medium on isolation.

---

## Coverage guidance that aligns with value

* Most tests should cover **invariants and contracts**.
* Fewer tests should cover **examples**.
* Very few should cover **full end-to-end**.
* Treat **flakiness and slowness** as test failures; low-noise suites win over large suites.

If you describe the system shape (library, API service, data pipeline, desktop app) I can propose a prioritized “test inventory” list: top 10 contracts/invariants to pin first.

## Concepts (the underlying “why”)

### Signal over ceremony

A test suite is a **change detector**. Its job is to produce **high signal** (real regressions) with **low noise** (flakiness, brittle assertions).

### Executable contracts

Tests are **executable specifications** of contracts: inputs, outputs, error modes, side effects, and invariants. If a behavior matters, it should exist somewhere as a contract.

### The oracle problem

Many systems lack a perfect “expected result.” Good testing mitigates this with:

* **Invariants** (must always hold)
* **Metamorphic relations** (if input changes in a known way, output changes predictably)
* **Round trips** (encode/decode, serialize/deserialize)
* **Differential checks** (two implementations agree)

### Local reasoning

Good tests preserve local reasoning: a developer can change a module and understand which tests should fail and why.

### Isolation is a design property

Testability is mostly about architecture:

* **Determinism** (time, randomness, concurrency controlled)
* **Seams** (dependencies substitutable)
* **Bounded side effects** (IO lives at edges)

### Feedback economics

Fast tests are not “nice to have,” they are the **economic engine** of refactoring. Slow suites increase batch size, which increases defects and merge risk.

---

## Test suite architecture (what to build)

### The verification stack

Use layers with different cost/coverage tradeoffs:

1. **Unit tests (hermetic, fast)**
   Validate pure logic and invariants. No real IO.
2. **Component tests (bounded integration)**
   Verify one component with fakes for remote dependencies.
3. **Contract tests (boundary truth)**
   Verify ports/APIs: behavior, error surfaces, idempotency, auth rules.
4. **Integration tests (real dependencies)**
   DB, queue, filesystem, external service simulators. Small in count, high in value.
5. **End-to-end tests (few, critical paths only)**
   Prove “the system works” but keep count small and assertions coarse.

A mature codebase usually wins by **maximizing (1) and (3)**, keeping (4) and (5) minimal but meaningful.

### Acyclic test boundaries

Tests should mirror your dependency direction:

* Core logic tests do not import infrastructure
* Contracts live at boundaries
* End-to-end sits outside everything

---

## What “good” looks like (suite attributes)

### Deterministic

* No dependence on wall clock time
* No dependence on ordering
* No network unless explicitly an integration test
* No shared mutable global state

### Intention-aligned

* Tests read like domain rules
* Assertions reflect **outcomes and contracts**, not internal calls

### Refactor-friendly

* Low use of mocks of internal functions
* Prefer verifying public surface + observable side effects
* Avoid snapshot testing unless the snapshot is a stable contract

### Fast by default

* Unit tests: typically milliseconds
* Component tests: tens of milliseconds
* Integration: seconds, but few

---

## Strategies (practical moves you repeatedly apply)

### 1) Make the system testable

* **Functional Core, Imperative Shell**: push IO out, keep core pure.
* **Introduce Ports (Protocols)**: `typing.Protocol` for dependencies.
* **Parameterize time/random/uuid**: inject `Clock`, RNG, ID generator.
* **Contain globals**: eliminate shared mutable singletons; pass state explicitly.

### 2) Choose the right test technique

* **Contract tests** for boundaries (ports, APIs, adapters).
* **Property-based tests** (Hypothesis) for invariants and broad input space.
* **Characterization tests** (golden master / approval style) for legacy behavior.
* **State machine tests** for workflows (explicit transitions + invariants).
* **Metamorphic tests** when exact expected values are hard.

### 3) Make tests maintainable

* **Test Data Builders**: factory functions / builders for readable setup.
* **Minimal fixtures**: small, composable fixtures; avoid fixture spaghetti.
* **Custom assertions**: domain-level asserts reduce duplication and noise.
* **Hermetic fakes**: in-memory repositories, fake clocks, fake queues.

### 4) Keep the suite healthy

* **Split test runs**: `unit`, `contract`, `integration`, `e2e` markers.
* **Enforce runtime budgets** per category.
* **Quarantine flakies** aggressively; treat flake rate as a defect.
* **Coverage as a lagging indicator**; prefer contract and invariant coverage.

---

## Python implementation patterns (quick reminders)

### pytest structure

* Use `pytest.mark.unit / contract / integration / e2e`
* Use fixtures for ownership (create/cleanup) and pure builders for data
* Use `monkeypatch` for narrow seams, not for deep internal coupling

### Hypothesis (property testing)

Use it when:

* Inputs are varied, edge cases matter
* You can state invariants (idempotency, monotonicity, commutativity)
* You want to shrink failures to minimal counterexamples

### Time and randomness control

* `freezegun` (or your own `Clock` protocol + fake)
* Inject RNG via `random.Random(seed)` passed in

### Integration dependencies

* Containers for DB/redis via test harness, but keep tests few
* Prefer transactional tests with cleanup guarantees

### CI ergonomics

* Fast default: run unit + contract on every PR
* Integration on PR or nightly depending on cost
* E2E on main merges or release gates

---

## Common testing smells and the refactoring response

### Smell: tests fail after harmless refactor

**Meaning:** tests assert implementation details.
**Fix:** shift to contract/outcome assertions; reduce mocks; add boundary tests.

### Smell: flaky tests

**Meaning:** nondeterminism (time, concurrency, ordering, shared state).
**Fix:** inject clock/RNG; isolate state; remove reliance on global caches; bound concurrency.

### Smell: slow suite

**Meaning:** too many integration/E2E tests or heavy setup per test.
**Fix:** move logic coverage into unit/property tests; reduce E2E count; reuse fixtures carefully; parallelize.

### Smell: tests are hard to write

**Meaning:** code lacks seams; side effects mixed with logic.
**Fix:** functional core; ports/adapters; dependency injection at composition root.

### Smell: high coverage but low confidence

**Meaning:** tests cover lines, not behaviors.
**Fix:** add contract tests for critical boundaries; add invariants/property tests; add negative-path tests.

---

## Metrics and thresholds (pragmatic, adjustable)

* **Flake rate:** target 0; any recurring flake is a priority fix.
* **Runtime budget (PR):** unit + contract ideally under a few minutes.
* **Integration count:** small; each should justify its existence (“proves wiring X”).
* **Coverage:** use thresholds only to prevent backsliding; do not chase 100%.
* **Mutation testing (optional):** useful for critical pure logic; treat as periodic, not every PR.

---

## A workflow for retrofitting tests into legacy code

1. **Characterization harness** for the behavior you must not break.
2. **Create seams** (ports/clock/config) to enable fast tests.
3. **Move logic inward** (functional core).
4. **Replace golden masters** with **contracts + invariants** as understanding improves.
5. Keep a strict boundary: fast tests cover logic; few integrations cover wiring.
