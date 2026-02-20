# Documentation Guide

> Advisory guidance for the `continuous-documentation` workflow. Used by
> `prompt.docs_gap_analysis`, `prompt.docs_gap_fix`, `prompt.docs_refactor_analysis`,
> and `prompt.docs_refactor_fix` to inform gap selection, fix scoping, and severity
> tagging. These are heuristics — not hard rules.

---

## Severity Tag Definitions

Every finding must carry exactly one severity level:

| Severity | Meaning |
|----------|---------|
| `MAJOR` | Missing or wrong docs that cause failed setup, unsafe behavior, or broken workflows |
| `MODERATE` | Docs that are usable but incomplete or stale in ways that slow correct usage |
| `MINOR` | Polish issues with low risk to successful usage |

The authoritative rubric with deterministic triggers is in
`docs/documentation_severity_rubric.md`.

---

## Gap Phase — What to Prioritize

### MAJOR gaps

- **Missing install or setup docs** — any required step not documented is a blocker for
  new users.
- **Missing runbook for a production operation** — undocumented operational procedures
  cause incidents.
- **Broken or removed commands still documented** — users following stale instructions
  will fail.

### MODERATE gaps

- **Missing explanatory section for a non-trivial feature** — users can proceed but will
  repeatedly rediscover the same information.
- **No example for a configuration block or schema** — schemas without examples are
  significantly harder to use correctly.
- **Undocumented error messages** — if users encounter an error with no doc, they cannot
  self-serve.

### MINOR gaps

- **Missing optional background/context section** — useful but not required for operation.
- **No cross-reference where one would help** — navigation aid, not correctness.

---

## Refactor Phase — What to Prioritize

### MAJOR refactors

- **Inaccurate instructions with likely operational impact** — wrong flag, wrong path,
  wrong API — users following the doc will fail.
- **Conflicting guidance across two docs** — readers cannot know which is correct.

### MODERATE refactors

- **Bloated or duplicated docs causing ambiguity** — two copies with minor drift create
  confusion about the authoritative source.
- **Stub or placeholder doc listed as authoritative** — empty stubs in the index mislead
  navigators.
- **Severely incomplete navigation index** — an index that omits most docs fails its
  primary purpose.

### MINOR refactors

- **Stage-specific knowledge silos** — docs that capture per-stage history but are not
  integrated into reference material.
- **Heading hierarchy or formatting inconsistency** — no correctness impact.
- **Redundant preamble** — repeated intro paragraphs across related docs.

---

## Gap Analysis Checklist

1. **Setup path** — Can a new user install, configure, and run the system using only
   the existing docs?
2. **Error surface** — Are error messages, failure modes, and recovery steps documented?
3. **Schema coverage** — Does every config key and schema field have a doc entry and
   example?
4. **Command accuracy** — Are all documented commands tested against the current codebase?
5. **Index completeness** — Does the navigation index cover all files in `docs/`?
6. **Cross-references** — When a concept is defined in one doc, are related docs linked?

---

## Fix Scoping Rules

- Every fix must trace back to exactly one `finding_id`.
- Prefer editing existing files over creating new ones.
- When creating a new doc, add it to `docs/index.md` in the same change.
- Wiki migrations produce file artifacts under `docs/wiki-export/` plus a
  `docs/wiki-export/map.json` entry — no direct external writes.
- Do not edit unrelated docs or code while applying a fix.

---

## Effort / Risk Reference

| Effort | Description |
|--------|-------------|
| S | Edit one section; <20 lines changed |
| M | New doc or significant section rewrite; <100 lines |
| L | Structural reorganization or multi-doc migration |

| Risk | Description |
|------|-------------|
| low | Additive; no existing content removed or changed |
| med | Replaces or restructures existing content; check for broken links |
| high | Deletes or merges docs; verify all inbound references are updated |

---

## Anti-Patterns to Avoid

- **Do not** create docs that duplicate what the code already makes obvious.
- **Do not** fix style or formatting when MAJOR/MODERATE gaps remain.
- **Do not** batch multiple findings into one fix — keep changes traceable.
- **Do not** leave stubs or "TODO: fill in later" placeholders; write minimal but
  complete content instead.
- **Do not** migrate content to wiki without producing the `docs/wiki-export/` artifact.

---

## Candidate Generation Strategy

To avoid anchoring on the first gap, scan across at least 3 lenses:

- **User journey** — follow the setup → usage → troubleshooting path and note every
  missing or wrong step.
- **Code-to-doc parity** — for every public function, flag, and config key, is there a
  doc entry?
- **Index audit** — list all files in `docs/` and compare against the navigation index.

Then rank by severity and fix the highest-impact gap that can be addressed in a single
bounded loop.
