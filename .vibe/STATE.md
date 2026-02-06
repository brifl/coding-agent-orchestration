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
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

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

- 2026-02-06: Implemented 20.2 follow-up — fixed chunk-level incremental diffing and malformed FTS query handling; acceptance probes now pass; moved to IN_REVIEW.
- 2026-02-06: Review FAIL — 20.2 unmet: one-line edit re-indexed all chunks for a changed file; opened ISSUE-012 and returned status to IN_PROGRESS.
- 2026-02-06: Consolidation — pruned work log from 32 to 10 entries; archived older entries to HISTORY.md.
- 2026-02-06: Process improvement — work log bloat now routes to consolidation (not improvements); split _consolidation_trigger_reason; all 40 tests pass.
- 2026-02-06: Process improvement — added concrete work-log cap (10 entries) to consolidation prompt; added WORK_LOG_CONSOLIDATION_CAP constant and validation warning; all 25 tests pass.
- 2026-02-05: Review PASS — 20.1 acceptance met; auto-advanced to 20.2; status set to NOT_STARTED.
- 2026-02-05: Implemented 20.1 — chunker.py with Python/Markdown/Generic/Fallback strategies; all 5 acceptance criteria pass.
- 2026-02-05: Resolved ISSUE-011 — added installable `vibe-one-loop` and `vibe-run` skills.
- 2026-02-05: Resolved ISSUE-010 — added manifest front matter to `vibe-loop`; verified cross-repo/global discovery.
- 2026-02-05: Mitigated ISSUE-009 in local tooling by normalizing `CODEX_HOME`/`AGENT_HOME` paths.

## Workflow state

(none)

## Evidence

- 2026-02-06 implementation evidence (checkpoint 20.2):
  - Build baseline: `python3 .codex/skills/rag-index/indexer.py build --manifest /tmp/vibe-impl-20-2/manifest1.json --output /tmp/vibe-impl-20-2/index.db` -> `2 files processed ... 5 chunks indexed ... 0 errors`.
  - Rebuild unchanged: same command with same manifest -> `0 files processed ... 0 chunks indexed`.
  - One-line change probe: after editing one line in `main.py`, build with `manifest2.json` -> `1 files processed ... 1 chunks indexed ... 3 chunks skipped ... 1 chunks removed`.
  - Delete-file probe: after deleting `util.py`, build with `manifest3_deleted.json` -> `1 files removed ... 1 chunks removed`.
  - Search output probe: `python3 .codex/skills/rag-index/indexer.py search "parse_gitignore" --index /tmp/vibe-impl-20-2/index.db --top-k 3` returned JSON including `start_line` and `end_line`.
  - Migration probe (v1 -> v2): build against synthetic v1 DB printed warning `Dropping and rebuilding for v2.`.
  - Adversarial boundary probe: `python3 .codex/skills/rag-index/indexer.py search '"' --index /tmp/vibe-impl-20-2/index.db --top-k 3` exits cleanly with `ERROR: invalid FTS query: unterminated string` (no traceback).

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
