# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 19A
- Checkpoint: 19A.2
- Status: BLOCKED  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Close out the Stage 19A prototype with a working end-to-end pipeline: scan → index → retrieve.

## Deliverables (current checkpoint)

- `.codex/skills/rag-index/retrieve.py` — retrieval CLI and library interface
- Update `.codex/skills/rag-index/SKILL.md` — add indexer + retriever to manifest

## Acceptance (current checkpoint)

- `python tools/skillctl.py install rag-index --global` succeeds (manifest validates)
- `retrieve.py` returns formatted snippets with provenance headers
- `retrieve.py pipeline` produces results from raw directories without pre-built index

## Work log (current session)
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
- Name: refactor-cycle
- Last run: 1 step(s)
- Steps: prompt.checkpoint_implementation

## Evidence

- `python3 tools/skillctl.py install rag-index --global`:
```
Installed rag-index to /home/brifl/.gemini/skills/rag-index
```
- `python3 .codex/skills/rag-index/retrieve.py pipeline "scan directories" --dirs .codex/skills/rag-index` (excerpt):
# file: scanner.py
```
#!/usr/bin/env python3
"""Recursive >>>directory<<< scanner for multi->>>directory<<< RAG indexing.
```

## Active issues

- BLOCKER: Repo has pre-existing modified files (git status not clean), so the clean-worktree requirement blocks setting Status to IN_REVIEW. Guidance needed on whether to ignore, stash, or commit those changes.

## Decisions

(No decisions)
