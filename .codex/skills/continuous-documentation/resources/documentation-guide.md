# Documentation Guide

> Advisory guidance for the `continuous-documentation` workflow. Used by
> `prompt.docs_gap_analysis`, `prompt.docs_gap_fix`, `prompt.docs_refactor_analysis`,
> and `prompt.docs_refactor_fix` to inform gap selection, fix scoping, and severity
> tagging. These are heuristics — not hard rules.

---

# Documentation refactoring guide (from first principles)

## Core premise

Documentation is part of the system’s **public interface**. It reduces the cost of change by making **contracts, invariants, and decisions** visible outside the code.

A good doc set makes these tasks cheap:

* Understand **what exists** and **why it exists**
* Change behavior **without breaking hidden assumptions**
* Operate the system **under stress** (debug, deploy, recover)
* Onboard new contributors **without tribal knowledge**

A bad doc set does the opposite: it increases entropy by being incomplete, outdated, duplicated, or aspirational.

---

## What should be documented (the minimum set that scales)

Think in layers: **Intent → Contracts → Decisions → Operation → Reference**.

### 1) Intent and boundaries

Document the “shape” of the system and where responsibilities live.

* **Project overview** (what it is, what it is not)
* **Primary flows** (1–3 key workflows end to end)
* **Module boundaries** (what each module owns, what it must not do)
* **Non goals and constraints** (performance, security, compliance, platform)

### 2) Contracts and invariants

Document the things that must stay true even when code changes.

* API contracts (inputs, outputs, errors, auth, rate limits)
* Data contracts (schemas, validation rules, meaning of fields, units/time zones)
* Domain invariants (what cannot happen, required sequences, state transitions)
* Error taxonomy (what failure types exist and what callers should do)

### 3) Decisions and rationale

Document “why this way,” not just “how it works.”

* ADRs (architecture decision records): alternatives considered, tradeoffs, consequences
* Technology choices and constraints
* “Sharp edges” and known caveats with recommended patterns

### 4) Operation and recovery

Docs for the future you at 2am.

* Deployment and configuration (what changes where)
* Runbooks: common failures, diagnostics, recovery steps, rollbacks
* Observability: what to look at first (logs/metrics/traces), correlation IDs
* Security operations: secret rotation, access changes, incident handling

### 5) Reference

Only after the above.

* CLI commands, config keys, environment variables, feature flags
* Module/API reference generated from source where possible

---

## How to find what needs documenting (systematic discovery)

### A) Follow the “questions people ask”

If someone must ask it twice, it probably needs documentation.

* PR review comments that repeat
* Onboarding questions
* Support/ops tickets
* “I forgot how to…” tribal knowledge

Technique: keep a running “FAQ backlog” and convert high-frequency items into docs.

### B) Look for “fragility hotspots” in the codebase

Areas that should have written contracts and invariants:

* High change rate files (git history)
* Complex modules (deep nesting, state machines, lots of branching)
* Cross-cutting concerns (auth, caching, retries, time handling)
* Boundary points (APIs, DB, queues, third-party integrations)

### C) Harvest from artifacts you already trust

* Tests: what behaviors are asserted that docs never mention?
* Incidents/postmortems: what would have prevented this?
* Config files and deployment scripts: what is required but undocumented?
* Logging/metrics: what signals exist but no one knows to check?

### D) Perform “doc drills”

Pick a scenario and attempt it using only docs:

* “New dev: run locally”
* “Ops: roll back”
* “User: integrate API”
* “Engineer: change X without breaking Y”

Everything that forces code spelunking becomes a doc task.

---

## Documentation smells (and what to do)

### 1) **Untrusted docs**

**Smell:** readers assume docs are wrong.
**Fix:** add a **verification mechanism**:

* “Last verified” date and version
* CI checks (links, snippets, build steps)
* Generated reference from source (where feasible)
* Delete or mark deprecated rather than letting rot accumulate

### 2) **Duplication and divergence**

**Smell:** same topic described in multiple places with subtle differences.
**Fix:** pick one canonical doc; replace others with links and short summaries.

### 3) **Aspirational docs**

**Smell:** describes how the system “should” work, not how it does.
**Fix:** move aspirational content to:

* ADRs (future direction)
* Roadmaps
* “Planned changes” section clearly labeled

### 4) **How-to without contracts**

**Smell:** steps exist, but no stated assumptions or failure modes.
**Fix:** add:

* Preconditions
* Expected outputs
* Common errors and recovery

### 5) **Reference without narrative**

**Smell:** lots of generated API pages, but no “what to do with it.”
**Fix:** add “primary flows” docs with examples; keep reference as supporting material.

### 6) **Wall of text**

**Smell:** long docs without structure; hard to skim.
**Fix:** enforce a doc structure template (below), add headings, and extract sub-docs.

### 7) **Orphan docs**

**Smell:** no owner, no update path, no link from index.
**Fix:** add ownership and ensure every doc is reachable from a top-level index.

---

## Organizing docs (information architecture that stays sane)

A practical, scalable layout:

* `README.md`
  What it is, quickstart, links to everything else.
* `docs/00-index.md`
  Navigation hub (the “table of contents”).
* `docs/10-architecture/`
  System overview, diagrams, boundaries, key flows.
* `docs/20-dev/`
  Local dev, testing, linting, contribution workflow.
* `docs/30-ops/`
  Deploy, config, runbooks, incident response.
* `docs/40-reference/`
  Config keys, CLI, API reference links (generated or curated).
* `docs/50-decisions/`
  ADRs: one file per decision, dated, short.
* `docs/60-security/`
  Threat model notes, auth model, secret handling.
* `docs/70-performance/`
  SLOs, critical paths, performance playbook.

Rules that prevent doc sprawl:

* Every doc has a **single primary purpose**.
* Every doc is linked from **exactly one** index section.
* Prefer many short docs over one mega-doc, but avoid fragmentation: each directory has a `README.md` or index.

---

## How to structure a doc well (template)

Use this default structure for most docs:

1. **Title**
2. **Purpose and audience** (1–2 lines)
3. **Status**: Draft / Stable / Deprecated
   Optional: “Last verified: YYYY-MM-DD”
4. **Quick start / TLDR** (the 5 lines most people need)
5. **Conceptual model** (what it is, boundaries, invariants)
6. **How to** (steps with expected outputs)
7. **Examples** (copy/paste friendly, minimal)
8. **Edge cases and failure modes** (what breaks, what to do)
9. **Links** (related docs, code pointers)
10. **Ownership** (who maintains it, where to ask)

For ADRs, keep it even tighter:

* Context → Decision → Alternatives → Consequences.

---

## Writing and formatting rules that keep docs effective

* Prefer **claims with evidence**: link to code, tests, configs, or ADRs.
* Use **stable terminology** (ubiquitous language). Avoid “thing,” “stuff,” “basically.”
* Separate **policy** (“must/should”) from **mechanism** (“how we do it today”).
* Every procedure includes:

  * Preconditions
  * Commands
  * Expected output
  * What to do if it fails
* Prefer tables for reference (config keys, env vars, error codes).
* Use diagrams sparingly but intentionally:

  * Boundary diagram (modules and dependency direction)
  * One sequence diagram per key flow (happy path + failure path if relevant)

---

## Maintenance workflow (docs as code)

* Add “**doc impact**” to PR review: does this change contracts, invariants, config, ops?
* Require docs updates for:

  * New public APIs
  * New config keys or behavior-changing flags
  * New failure modes or operational procedures
* Run CI checks:

  * Link checker
  * Snippet execution (where practical)
  * Build docs generation (if using Sphinx/MkDocs)

---

## Practical Python-oriented doc sources (high ROI)

* **Docstrings**: module/class/function intent and contracts (especially error modes).
* **Type hints**: communicate shape; reduce doc burden for basic usage.
* **Generated reference**: Sphinx autodoc or MkDocs + mkdocstrings.
* **Schemas**: pydantic models as living contracts (and can emit JSON schema).
* **Examples as tests**: doctest or pytest-based “example tests” for critical docs.

---

## A lightweight “documentation refactor loop”

1. Identify a recurring question or recurring failure.
2. Write a short doc that answers it with contracts + procedure + recovery.
3. Link it from the index and from the closest code boundary.
4. Add a verification hook (test, CI snippet, or “last verified” ritual).
5. Delete competing docs or replace with links.
