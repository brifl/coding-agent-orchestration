# Refactoring Guide

> Advisory guidance for the `continuous-refactor` workflow. Used by `prompt.refactor_scan` to
> inform candidate selection and impact tagging. These are heuristics — not hard rules.

---

# Refactoring Guidance Table

| Smell                                          | Threshold                                                                                | Concepts                                                       | Strategies                                                                         |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Change ripple across modules                   | A “local” change touches 3plus modules or 2plus layers more than twice per sprint        | Coupling Surface; Dependency Graph Control                     | Split Module; Introduce Port (Protocol); Add Composition Root                      |
| Cyclic imports / module cycles                 | Any import cycle; or import order changes behavior                                       | Dependency Graph Control; Codebase Hygiene                     | Split Module; Introduce Adapter; Add Composition Root                              |
| Shared mutable globals / singletons            | 2plus write sites; or any test order dependence                                          | Coupling Surface; State and Invariants; Concurrency Discipline | Parameterize Dependency; Side Effect Gate; Delete Dead Code                        |
| Hidden IO in getters / constructors            | Any IO in property access, `__init__`, `__repr__`, `__str__`, equality                   | Side Effect Containment; Robustness (Explicit Errors)          | Functional Core Shell; Side Effect Gate; Extract Function                          |
| Flag parameter controls behavior               | Any boolean or enum flag with 2plus branches that represent distinct workflows           | Cohesion Focus; Capability Abstractions                        | Remove Flag Parameter; Extract Function; Replace Conditionals with Dispatch        |
| Wide interface used inconsistently             | 2plus consumers use disjoint subsets; or “god” interface with 10plus members             | Capability Abstractions; Cohesion Focus                        | Introduce Port (Protocol); Split Module; Narrow DTO / Parameter Object             |
| Passing whole objects for a few fields         | Callee uses 30 percent or less of fields or attributes                                   | Coupling Surface; Domain Type Safety                           | Narrow DTO / Parameter Object; Move Behavior to Data; Value Object Types           |
| Domain code imports vendor or framework types  | Any domain or core module imports requests, ORM models, web framework request objects    | Boundary Translation; Dependency Graph Control                 | Introduce Adapter; Boundary Validation (Schema); Introduce Port (Protocol)         |
| “Utils” or “common” junk drawer                | Module grows every sprint; or 5plus unrelated functions/classes                          | Cohesion Focus; Codebase Hygiene                               | Split Module; Extract Class; Ubiquitous Language naming pass                       |
| Long function with phase comments              | 50plus LOC or 3plus distinct phases (validate transform persist notify)                  | Cohesion Focus; Side Effect Containment                        | Extract Function; Functional Core Shell; Side Effect Gate                          |
| Deep nesting / complex branching               | Nesting depth 4plus or cyclomatic complexity 15plus                                      | Complexity Budget; Intent Fidelity                             | Extract Function; Replace Conditionals with Dispatch; Make State Machine           |
| “Magic” implicit assumptions                   | Depends on default timezone, locale, dict order, implicit global config                  | Temporal Semantics; Configuration Governance                   | Clock Injection (UTC); Config Schema; Boundary Validation (Schema)                 |
| Swallowed exceptions / silent failures         | Any bare `except` or exceptions logged then ignored in non optional paths                | Explicit Errors; Observability First                           | Exception Taxonomy; Result Object; Structured Logging                              |
| Blanket catch and rethrow generic              | `except Exception` mapping to boolean or `None` in core logic                            | Explicit Errors; Intent Fidelity                               | Exception Taxonomy; Result Object; Contract Tests                                  |
| Sentinel values for error states               | `None`, `-1`, empty object used to signal multiple failure modes                         | Explicit Errors; Domain Type Safety                            | Result Object; Value Object Types; Contract Tests                                  |
| Side effects mixed with computation            | Function both computes and performs IO or mutation beyond its parameters                 | Side Effect Containment; Cohesion Focus                        | Functional Core Shell; Side Effect Gate; Parameterize Dependency                   |
| Temporal coupling in workflows                 | Correctness depends on calling A then B then C with no enforcement                       | State and Invariants; Temporal Semantics                       | Make State Machine; Extract Class; Contract Tests                                  |
| Invalid states representable                   | Multiple optional fields that must co exist; inconsistent enums; partial objects allowed | Domain Type Safety; State and Invariants                       | Value Object Types; Constrained Constructors; Boundary Validation (Schema)         |
| Primitive obsession for key concepts           | IDs, money, units, status are strings or ints in 10plus places                           | Domain Type Safety; Ubiquitous Language                        | Value Object Types; Introduce Parameter Object; Replace Conditionals with Dispatch |
| Duplicate business rules                       | Same rule appears 2plus times and is edited independently                                | Duplication Control; Contract Stability                        | Extract Function; Canonical Rule Module; Contract Tests                            |
| Shared helper becomes leaky abstraction        | Helper needs flags or special cases for each caller                                      | Cohesion Focus; Capability Abstractions                        | Split Module; Introduce Port (Protocol); Remove Flag Parameter                     |
| Tests absent for boundary behavior             | No tests for invalid input, timeouts, partial failures, auth                             | Verification Safety Net; Security Hardening                    | Contract Tests; Characterization Tests; Boundary Validation (Schema)               |
| Brittle tests assert implementation            | Tests fail after safe refactor; heavy mocking of internals                               | Verification Safety Net; Cohesion Focus                        | Contract Tests; Property Tests; Refactor to seams (Introduce Port)                 |
| Flaky tests due to time/random/shared state    | Any nondeterministic failures or order dependence                                        | Temporal Semantics; Concurrency Discipline                     | Clock Injection (UTC); Parameterize Dependency; Isolation fixtures                 |
| N plus 1 queries or calls                      | Per item IO in loop; p95 latency grows linearly with list size                           | Performance Shape; Boundary Translation                        | Batch and Cache; Reduce Chatty Calls; Metrics at Boundaries                        |
| Unbounded work from inputs                     | Unbounded payload size, regex on arbitrary input, full table scans                       | Performance Shape; Security Hardening                          | Bound Work (limits); Streaming iteration; Boundary Validation (Schema)             |
| Cache without sizing / invalidation            | Cache grows unbounded or hit rate unknown; stale data bugs appear                        | Performance Shape; State and Invariants                        | Cache Boundary; Metrics at Boundaries; Explicit invalidation policy                |
| Lock contention / shared hot mutable state     | Throughput drops with concurrency; lock held around IO                                   | Concurrency Discipline; Performance Shape                      | Encapsulate Synchronization; Backpressure and Pools; Reduce Shared State           |
| Ad hoc async or background tasks               | Background threads/tasks started in many places with no owner                            | Lifecycle Ownership; Concurrency Discipline                    | Add Composition Root; Resource Context Managers; Backpressure and Pools            |
| Resource leaks (files, sockets, connections)   | Open handles grow; missing `close`; no clear ownership                                   | Lifecycle Ownership; Robustness                                | Resource Context Managers; Add Composition Root; Exception Taxonomy                |
| Feature flags never removed                    | Flags older than 2 releases; flag logic pervades core                                    | Configuration Governance; Codebase Hygiene                     | Feature Flag Lifecycle; Remove Flag Parameter; Delete Dead Code                    |
| Config scattered and unvalidated               | Environment lookups throughout; invalid config fails late                                | Configuration Governance; Boundary Translation                 | Config Schema; Add Composition Root; Boundary Validation (Schema)                  |
| Dependency bloat / unused deps                 | Dependency graph grows; 10plus unused transitive deps; security alerts frequent          | Codebase Hygiene; Security Hardening                           | Prune Dependencies; Reproducible Build Pins; Delete Dead Code                      |
| Insecure string concatenation for SQL or shell | Any user influenced string building for SQL, shell, paths                                | Security Hardening; Boundary Translation                       | Parameterized Queries; Boundary Validation (Schema); Least Privilege Capabilities  |
| Authz checks sprinkled inconsistently          | More than one style of auth check; missing checks found in reviews                       | Security Hardening; Dependency Graph Control                   | Centralize Authz Guard; Add Composition Root; Contract Tests                       |
| Secrets in logs or wide scope                  | Any secret printed; secrets accessible outside boundary modules                          | Security Hardening; Observability First                        | Structured Logging with Redaction; Least Privilege Capabilities; Config Schema     |
| Missing correlation and trace context          | Cannot follow a request across logs; debugging relies on guessing                        | Observability First; Robustness                                | Correlation Context; Structured Logging; Metrics at Boundaries                     |
| API changes break consumers                    | Breaking changes without deprecation; frequent coordination                              | Contract Stability; Dependency Graph Control                   | API Versioning and Deprecation; Contract Tests; Introduce Adapter                  |
| Build not reproducible                         | “Works on my machine”; unpinned deps; CI drift                                           | Build Reproducibility; Codebase Hygiene                        | Reproducible Build Pins; Prune Dependencies; Add Composition Root                  |
| Dead code and abandoned paths                  | Code has no callers; feature unused for 1plus release                                    | Codebase Hygiene; Complexity Budget                            | Delete Dead Code; Characterization Tests; Prune Dependencies                       |
| Vendor model leaks into persistence or domain  | ORM entities used as domain objects; migrations break business logic                     | Boundary Translation; Domain Type Safety                       | Introduce Adapter; Split Models (read vs write); Value Object Types                |
| Overloaded “save” methods with side effects    | Persist also emits events, sends email, updates cache                                    | Intent Fidelity; Side Effect Containment                       | Functional Core Shell; Side Effect Gate; Extract Function                          |
| Naming contradicts behavior                    | Method name implies query but performs mutation; “validate” mutates                      | Intent Fidelity; Ubiquitous Language                           | Rename plus refactor; Extract Function; Contract Tests                             |
| Complex retry behavior everywhere              | Mixed retry policies per call site; duplicate side effects occur                         | Robustness; Performance Shape                                  | Decorate Dependency (wrappers); Idempotency key pattern; Exception Taxonomy        |
| Missing rate limits / budgets                  | Under load, system collapses or cascades failures                                        | Performance Shape; Security Hardening                          | Bound Work (limits); Backpressure and Pools; Circuit breaker wrapper               |

# Concepts

Each concept is a “why” lens: what quality is being protected, and what failure mode it prevents.

## Cohesion Focus

A unit (function, class, module) should exist for **one purpose**. High cohesion means its parts collaborate toward a single responsibility and share a small set of invariants.

## Coupling Surface

Coupling is the **strength and breadth of interdependence** between units. Reduce coupling by minimizing shared assumptions, shared mutable state, and knowledge of internals.

## Dependency Graph Control

The dependency graph should have a **clear direction** and be **acyclic by design**. Dependency choices and wiring belong in explicit composition points rather than scattered throughout the code.

## Capability Abstractions

Dependencies should be expressed as **meaningful capabilities** (what you can do), not as concrete implementations or vendor shaped APIs. A good abstraction hides invariants and enables substitution.

## Boundary Translation

At trust and technology boundaries, translate external representations into **internal domain concepts**. Prevent framework and vendor types from leaking into core logic.

## Side Effect Containment

Separate “compute” from “effect.” Side effects (IO, mutation outside local scope, time, randomness) should be concentrated in explicit places with observable contracts.

## Explicit Errors

Failures should be **first class and distinguishable**. Avoid collapsing many failure modes into `None`, booleans, or generic exceptions that destroy decision making signal.

## Intent Fidelity

Names, contracts, and behavior should align. Code that “works for the wrong reasons” is fragile because future changes will break hidden assumptions.

## State and Invariants

Model state so that **illegal states are hard or impossible** to represent. Make state transitions explicit and enforce invariants at the edges of transitions.

## Domain Type Safety

Prefer strong domain types over primitives and ambiguous structures. Clear data models reduce interpretation errors and prevent semantic drift.

## Complexity Budget

Complexity is a liability that compounds. Limit branching, nesting, and cleverness so that reasoning remains local and changes remain safe.

## Duplication Control

Duplication creates divergence. Extract shared rules when the abstraction is stable; otherwise prefer local duplication to avoid leaky generalization.

## Verification Safety Net

Refactoring is safe when there is a fast, reliable feedback system: unit and contract tests dominate, integration tests prove wiring, end to end tests validate flows.

## Observability First

Systems must be diagnosable. Ensure structured logs, correlation context, meaningful metrics, and error taxonomy so failures become visible and attributable.

## Performance Shape

Optimize the **shape of work**: fewer remote calls, less data movement, bounded work, batching, caching, streaming. Algorithm and IO patterns dominate micro optimizations.

## Concurrency Discipline

Concurrency must be explicit and bounded. Prefer ownership, immutability, message passing, and backpressure over shared mutable state and ad hoc async.

## Temporal Semantics

Time is a domain with sharp edges. Standardize representation (typically UTC instants), centralize “now,” make ordering and timing assumptions explicit.

## Lifecycle Ownership

Every resource and background activity must have a clear owner and lifecycle: create, use, dispose. Avoid orphaned tasks and implicit long lived state.

## Configuration Governance

Configuration is a boundary. Centralize config loading, validate with a schema, keep flags disciplined, and avoid scattered environment reads inside core logic.

## Security Hardening

Reduce trust, reduce privilege, reduce attack surface. Make authn/authz explicit, validate inputs at boundaries, avoid unsafe composition, and fail closed.

## Contract Stability

Public APIs and internal ports should evolve without breaking consumers. Use versioning, adapters, and contract tests to enable independent change.

## Build Reproducibility

The system should build and run the same way in all environments. Pin dependencies, standardize build entry points, and keep CI and local parity.

## Codebase Hygiene

Remove dead code, prune dependencies, and keep the repository understandable. Less code and fewer dependencies reduce risk surface across all dimensions.

# Refactoring strategies (Python focused)

Each strategy is a “how” move you can apply repeatedly. Names below match the table.

## Split Module

Carve a file/package along responsibility lines. Move cohesive clusters together; keep imports one-directional.

## Extract Function

Turn phases and nested logic into small intention-named functions. Prefer pure transforms when possible.

## Extract Class

Bundle state plus invariants plus behavior that belong together. Use this to eliminate temporal coupling and “parameter soup.”

## Introduce Port (Protocol)

Define a small capability interface at the caller side. In Python: `typing.Protocol` (or ABC) plus structural typing.

## Introduce Adapter

Wrap vendor/framework APIs and translate DTOs and errors into domain types. Keep external types at the boundary.

## Add Composition Root

Centralize wiring in one place per executable (app entrypoint, CLI, worker). No object graph creation in domain code.

## Parameterize Dependency

Pass capabilities explicitly (objects, callables, ports) rather than reaching into globals/singletons.

## Functional Core Shell

Refactor toward pure core logic plus a thin shell that performs IO and mutation. Make the core easy to test.

## Side Effect Gate

Create explicit “effect modules” that own IO, time, randomness, logging, and external interactions. Everything else calls through the gate.

## Remove Flag Parameter

Replace `mode` or boolean branching APIs with separate functions, strategy objects, or dispatch tables.

## Replace Conditionals with Dispatch

Turn `if/elif` ladders into dict dispatch, single-dispatch, pattern matching, or polymorphism.

## Narrow DTO / Parameter Object

Stop passing wide objects. Create small dataclasses/pydantic models for exactly what is needed, or use a cohesive parameter object.

## Move Behavior to Data

Relocate logic that primarily manipulates an entity’s fields onto the entity/value object (or a domain service tightly scoped to that data).

## Value Object Types

Introduce small immutable types for domain primitives (`Money`, `UserId`, `Email`, `UtcInstant`). Validate at construction.

## Make State Machine

Make states explicit (enum/sum type) and represent transitions as methods with validation and clear error modes.

## Boundary Validation (Schema)

Validate and normalize inputs at ingress using pydantic, attrs, marshmallow, or manual schema checks. Convert to domain types immediately.

## Exception Taxonomy

Replace generic exceptions with domain-specific errors. Separate transient vs permanent vs programmer errors.

## Result Object

Use explicit `Result[T, E]` style returns where exceptions are too blunt. In Python: dataclass with `ok/value/error`, or `typing.Annotated` conventions.

## Structured Logging

Emit structured events with stable names and fields. Ensure redaction. Avoid logging that changes semantics.

## Metrics at Boundaries

Add latency, error rate, saturation metrics around IO boundaries. Record p50/p95/p99 and queue depths where relevant.

## Correlation Context

Propagate request/job ids via contextvars or explicit parameters. Ensure logs and metrics include correlation ids.

## Batch and Cache

Reduce N+1 by batching; introduce caches with sizing, invalidation rules, and hit-rate visibility.

## Reduce Chatty Calls

Collapse sequences of remote calls into coarse-grained operations, bulk endpoints, or prefetching.

## Bound Work (limits)

Add payload size limits, timeouts, pagination, retry budgets, and bounded queues. Prefer fail-fast to unbounded growth.

## Backpressure and Pools

Use bounded worker pools and queues. Prevent unlimited task creation. Make concurrency a controlled resource.

## Encapsulate Synchronization

Keep locks and concurrency primitives inside one component that owns the shared state. No “lock leaks” to callers.

## Resource Context Managers

Use `with`/`async with` for files, locks, connections, sessions. Centralize start/stop in owners.

## Feature Flag Lifecycle

Treat flags as temporary. Track introduction date and removal plan. Keep flags at routing/composition boundaries.

## Config Schema

Centralize config loading, validation, and defaults (pydantic settings/dataclass). No scattered `os.getenv` in core.

## Delete Dead Code

Remove unused paths and modules, supported by characterization tests and static reference checks.

## Prune Dependencies

Remove unused direct and transitive deps. Pin versions. Split optional extras. Minimize dependency surface per layer.

## Reproducible Build Pins

Lock dependencies and build steps (requirements lock, uv/poetry/pip-tools). Ensure deterministic installs in CI and prod.

## Contract Tests

Verify behavior at module/service boundaries. Consumer-driven if multiple consumers. Assert error surfaces and invariants.

## Characterization Tests

Pin current behavior before refactoring legacy code. Treat as a temporary harness that can be replaced by contract tests.

## Property Tests

Use invariant-based testing (Hypothesis) for idempotency, ordering, round trips, monotonicity, and state machine transitions.

## Canonical Rule Module

Create a single authoritative place for shared business rules, with a stable API and tests; adapt callers rather than duplicating.

## API Versioning and Deprecation

Add explicit versioned surfaces or adapters; deprecate intentionally; maintain compatibility windows.

## Centralize Authz Guard

Create a small set of authorization functions/policies invoked consistently at boundaries or application services.

## Parameterized Queries

Use parameter binding for SQL, safe path joins, safe templating, allowlists for shell and dynamic execution.

## Least Privilege Capabilities

Pass narrowly scoped credentials/capabilities (read vs write, per-tenant) rather than broad clients. Keep secrets and power at edges.

## Decorate Dependency (wrappers)

Wrap ports with retry, caching, tracing, circuit breakers, idempotency, and metrics without changing consumers.

## Idempotency key pattern

Make write operations safely repeatable using idempotency keys and deduplication records where retries exist.

## Split Models (read vs write)

Separate domain models, persistence models, and API models. Prevent ORM entities or transport DTOs from becoming domain objects.
