# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 20
- Checkpoint: 20.3
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Upgrade retrieve.py to produce high-quality, budget-aware, diverse context for agent prompts.

## Deliverables (current checkpoint)

- Upgrade `retrieve.py` to consume chunk-level search results
- Output format: provenance header (`rel_path:start-end`) + fenced code blocks with language tags
- Add `--max-context-chars` (default 8000) as a hard output budget
- Add `--max-per-file` (default 3) diversity cap
- Add `--mode {lex}` with `sem`/`hybrid` stubs that warn and fall back to `lex`
- Keep library API: `retrieve(query, index_path, ...) -> str`

## Acceptance (current checkpoint)

- Output includes provenance headers with file path + line range
- Output uses fenced code blocks with correct language tags
- With `--max-per-file 2`, no file appears more than twice in results
- Total output respects `--max-context-chars` budget

## Work log (current session)

- 2026-02-06: Review PASS — 20.2 acceptance met with adversarial probes; auto-advanced to 20.3; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.2 follow-up — fixed chunk-level incremental diffing and malformed FTS query handling; acceptance probes now pass; moved to IN_REVIEW.
- 2026-02-06: Review FAIL — 20.2 unmet: one-line edit re-indexed all chunks for a changed file; opened ISSUE-012 and returned status to IN_PROGRESS.
- 2026-02-06: Consolidation — pruned work log from 32 to 10 entries; archived older entries to HISTORY.md.
- 2026-02-06: Process improvement — work log bloat now routes to consolidation (not improvements); split _consolidation_trigger_reason; all 40 tests pass.
- 2026-02-06: Process improvement — added concrete work-log cap (10 entries) to consolidation prompt; added WORK_LOG_CONSOLIDATION_CAP constant and validation warning; all 25 tests pass.
- 2026-02-05: Review PASS — 20.1 acceptance met; auto-advanced to 20.2; status set to NOT_STARTED.
- 2026-02-05: Implemented 20.1 — chunker.py with Python/Markdown/Generic/Fallback strategies; all 5 acceptance criteria pass.
- 2026-02-05: Resolved ISSUE-011 — added installable `vibe-one-loop` and `vibe-run` skills.
- 2026-02-05: Resolved ISSUE-010 — added manifest front matter to `vibe-loop`; verified cross-repo/global discovery.

## Workflow state

(none)

## Evidence

(Checkpoint 20.3 — not yet started)

## Active issues

- [ ] ISSUE-009: Skills fail to load outside current repo (vendor_imports clone collision)
  - Impact: MINOR
  - Status: OPEN
  - Owner: agent
  - Unblock Condition: Confirm Codex recommended-skill clone/update behavior no longer fails when vendor_imports target already exists.
  - Evidence Needed: Successful recommended-skills load in Codex app (or product-side fix/confirmation) without manual cleanup.
  - Notes: External error seen in Codex app: "Unable to load recommended skills: git clone failed: fatal: destination path '\\wsl.localhost\\Ubuntu\\home\\brifl\\.codex\\vendor_imports\\skills' already exists and is not an empty directory." Local tooling now normalizes UNC-style `CODEX_HOME` paths and cross-repo discovery is verified. Remaining work is product-side behavior for recommended skill vendor clone/update handling. Docs for reference: https://developers.openai.com/codex/skills/

## Decisions

(No decisions)
