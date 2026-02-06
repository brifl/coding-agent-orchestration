# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 20
- Checkpoint: 20.2
- Status: NOT_STARTED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Upgrade the indexer to work at chunk granularity with chunk-level incremental updates.

## Deliverables (current checkpoint)

- Upgrade `indexer.py` schema (bump `_SCHEMA_VERSION` to 2): new `chunks` table, FTS5 indexes chunk text
- Upgrade `build` subcommand: chunk via `chunker.py`, incremental at chunk level, remove stale chunks
- Upgrade `search` subcommand: return `start_line`, `end_line`, `snippet`, `chunk_id`
- Migration: if existing v1 DB detected, drop and rebuild (print warning)

## Acceptance (current checkpoint)

- Changing one line in a file only re-indexes affected chunks (verify via stats output)
- Deleting a file removes all its chunks
- Search results include `start_line` and `end_line` (not just file path)
- Re-indexing unchanged files reports 0 indexed

## Work log (current session)

- 2026-02-05: Review PASS — 20.1 acceptance met; all 5 criteria verified with HIGH confidence; auto-advanced to 20.2; status set to NOT_STARTED.
- 2026-02-05: Implemented 20.1 — chunker.py with Python/Markdown/Generic/Fallback strategies; import grouping; all 5 acceptance criteria pass; status set to IN_REVIEW.
- 2026-02-05: Resolved ISSUE-011 — added installable `vibe-one-loop` and `vibe-run` skills; wired bootstrap + skillset + docs to include them.
- 2026-02-05: Resolved ISSUE-010 — added manifest front matter to `vibe-loop`, forced manifest refresh in global installs, and verified cross-repo/global discovery (including UNC-style `CODEX_HOME` normalization).
- 2026-02-05: Mitigated ISSUE-009 in local tooling by normalizing `CODEX_HOME`/`AGENT_HOME` paths across resolver/install scripts; external Codex recommended-skills clone behavior still requires product-side verification.
- 2026-02-05: Logged ISSUE-011 for vibe-run/vibe-one-loop contract drift (documented but not installable); expanded ISSUE-010 with manifest/discovery evidence.
- 2026-02-05: Advanced checkpoint 20.0 → 20.1 (Chunking engine); status set to NOT_STARTED.
- 2026-02-05: Review PASS — 20.0 acceptance met; determinism verified, content_hash correct, --stats working; status set to DONE.
- 2026-02-05: Implemented 20.0 — content_hash, language field, stable ordering, --stats flag; all acceptance tests pass; commit 132496c; status set to IN_REVIEW.
- 2026-02-05: Review PASS — 19A.2 acceptance met; all deliverables verified; Stage 19A complete; advanced to 20.0; status set to NOT_STARTED.
- 2026-02-05: Blocker resolved — working tree is now clean (pre-existing files were committed in 3d6dd49); status set to IN_REVIEW.
- 2026-02-05: Blocked on clean-worktree requirement (repo has pre-existing modified files); need guidance before setting IN_REVIEW.
- 2026-02-05: Implemented retrieve.py with pipeline mode; updated rag-index SKILL.md; ran skillctl install + retrieval demos; status set to IN_REVIEW.
- 2026-02-05: Review PASS — 19A.1 acceptance met; all deliverables verified; advanced to 19A.2; status set to NOT_STARTED.
- 2026-02-05: Implemented indexer.py; tested build, search, incremental skip/update/removal; all acceptance criteria pass; status set to IN_REVIEW.
- 2026-02-05: Advanced checkpoint 19A.0 → 19A.1; status set to NOT_STARTED.
- 2026-02-05: Review PASS — 19A.0 acceptance met; all deliverables verified; status set to DONE.
- 2026-02-04: Implemented scanner.py; tested multi-dir, gitignore, exclusions, include/file-type filters, max-depth; all acceptance criteria pass; status set to IN_REVIEW.
- 2026-02-03: Updated plan to Stage 19A; unblocked and set checkpoint 19A.0 to NOT_STARTED.
- 2026-02-03: Blocked on Stage 20.0 scope/placement; clarification requested.
- 2026-02-03: Consolidated Stage 19; advanced to checkpoint 20.0; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 19.2 acceptance met; status set to DONE.
- 2026-02-03: Added demo/feedback prompts; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 19.1 → 19.2; status set to NOT_STARTED.
- 2026-02-03: Review PASS — 19.1 acceptance met; status set to DONE.
- 2026-02-03: Added test gap/generation/review prompts; ran demo command; status set to IN_REVIEW.
- 2026-02-03: Advanced checkpoint 19.0 → 19.1; status set to NOT_STARTED.
- 2026-02-03: Detected checkpoint headings for 19.1/19.2 not parsed by agentctl; logged ISSUE-007.
- 2026-02-03: Review PASS — 19.0 acceptance met; status set to DONE.
- 2026-02-03: Added refactor scan/execute/verify prompts; ran demo command; status set to IN_REVIEW.

## Workflow state

(none)

## Evidence

(Checkpoint 20.2 — not yet started)

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
