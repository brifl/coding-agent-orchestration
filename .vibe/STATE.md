# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 20
- Checkpoint: 20.1
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Build a deterministic chunking library that splits files into indexed units suitable for precise retrieval.

## Deliverables (current checkpoint)

- `.codex/skills/rag-index/chunker.py` — chunking engine with strategy dispatch
- Strategies: Python (AST-based), Markdown (heading-based), Generic code (blank-line blocks), Fallback (fixed-size windows)
- Chunk schema with `chunk_id`, `doc_path`, `start_line`, `end_line`, `text`, `token_estimate`, `hash`, `language`
- Library API: `chunk_file(path, language, max_chunk_tokens=500) -> list[dict]`
- CLI: `python chunker.py <file> [--language python] [--max-tokens 500]`

## Acceptance (current checkpoint)

- Chunking the same file twice produces identical output (determinism)
- A Python file with 3 functions produces 3+ chunks (one per function + possible module docstring)
- A Markdown file with 4 headings produces 4 chunks
- No chunk exceeds `max_chunk_tokens * 5` characters (hard cap with forced split)
- Chunks have non-overlapping, contiguous line ranges that cover the entire file

## Work log (current session)

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

- Determinism: chunking scanner.py twice → identical JSON output (PASS)
- Python 3+ function chunks: scanner.py → 9 function/class chunks (PASS)
- Markdown 4-heading file → 4 chunks (PASS)
- Max size cap: largest chunk 2490 chars < 2500 limit (PASS)
- Contiguous coverage: lines 1-383, no gaps or overlaps (PASS)
- Import grouping: 8 imports → 1 chunk (lines 7-18)
- scanner.py: 15 total chunks (docstring, imports, dict, 8 functions, class, 2 force-split pieces, main, guard)
- README.md: 19 heading-level chunks

## Active issues

- [ ] ISSUE-009: Skills fail to load outside current repo (vendor_imports clone collision)
  - Severity: MINOR
  - Status: OPEN
  - Owner: agent
  - Unblock Condition: Confirm Codex recommended-skill clone/update behavior no longer fails when vendor_imports target already exists.
  - Evidence Needed: Successful recommended-skills load in Codex app (or product-side fix/confirmation) without manual cleanup.
  - Notes: External error seen in Codex app: "Unable to load recommended skills: git clone failed: fatal: destination path '\\wsl.localhost\\Ubuntu\\home\\brifl\\.codex\\vendor_imports\\skills' already exists and is not an empty directory." Local tooling now normalizes UNC-style `CODEX_HOME` paths and cross-repo discovery is verified. Remaining work is product-side behavior for recommended skill vendor clone/update handling. Docs for reference: https://developers.openai.com/codex/skills/

## Decisions

(No decisions)
