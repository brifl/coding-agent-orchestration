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
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

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

- 2026-02-06: Implemented 20.3 — retrieve.py now emits provenance headings + language fences, enforces max-per-file and max-context-chars, and supports mode fallback (`sem`/`hybrid` -> `lex`); moved to IN_REVIEW.
- 2026-02-06: Review PASS — 20.2 acceptance met with adversarial probes; auto-advanced to 20.3; status set to NOT_STARTED.
- 2026-02-06: Implemented 20.2 follow-up — fixed chunk-level incremental diffing and malformed FTS query handling; acceptance probes now pass; moved to IN_REVIEW.
- 2026-02-06: Review FAIL — 20.2 unmet: one-line edit re-indexed all chunks for a changed file; opened ISSUE-012 and returned status to IN_PROGRESS.
- 2026-02-06: Consolidation — pruned work log from 32 to 10 entries; archived older entries to HISTORY.md.
- 2026-02-06: Process improvement — work log bloat now routes to consolidation (not improvements); split _consolidation_trigger_reason; all 40 tests pass.
- 2026-02-06: Process improvement — added concrete work-log cap (10 entries) to consolidation prompt; added WORK_LOG_CONSOLIDATION_CAP constant and validation warning; all 25 tests pass.
- 2026-02-05: Review PASS — 20.1 acceptance met; auto-advanced to 20.2; status set to NOT_STARTED.
- 2026-02-05: Implemented 20.1 — chunker.py with Python/Markdown/Generic/Fallback strategies; all 5 acceptance criteria pass.
- 2026-02-05: Resolved ISSUE-011 — added installable `vibe-one-loop` and `vibe-run` skills.

## Workflow state

(none)

## Evidence

- 2026-02-06 implementation evidence (checkpoint 20.3):
  - Build index fixture: `python3 .codex/skills/rag-index/scanner.py /tmp/vibe-20-3-verify --file-types .py --output /tmp/vibe-20-3-verify/manifest.json` and `python3 .codex/skills/rag-index/indexer.py build --manifest /tmp/vibe-20-3-verify/manifest.json --output /tmp/vibe-20-3-verify/index.db`.
  - Provenance + language formatting: `python3 .codex/skills/rag-index/retrieve.py "parse" --index /tmp/vibe-20-3-verify/index.db --top-k 10 --max-per-file 2` output starts with `<!-- RAG context for: "parse" -->`, contains `### scanner_like.py:<start>-<end>` headings, and includes fenced ` ```python ` blocks.
  - Diversity cap: parsed headings from the same command show counts `{'scanner_like.py': 2, 'other.py': 1}` (no file > 2 with `--max-per-file 2`).
  - Budget cap: `python3 .codex/skills/rag-index/retrieve.py "parse" --index /tmp/vibe-20-3-verify/index.db --top-k 10 --max-context-chars 260` produced output length `233` (<= 260).
  - Mode fallback: `--mode sem` and `--mode hybrid` both exit 0 and print warning `falling back to 'lex'`.

## Active issues

(None)

## Decisions

(No decisions)
