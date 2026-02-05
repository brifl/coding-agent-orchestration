# STATE

**Important** There are multiple instances of files with the same name as this one in this repo. The others are for templating, bootstrapping, or simple examples. This is a real one. This is left to provide a real example of what these look like in use. Use it to actually guide the coding agent. If you _are_ a coding agent, this one's for you!

## Session read order

1) `AGENTS.md`
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 19A
- Checkpoint: 19A.1
- Status: IN_REVIEW  <!-- NOT_STARTED | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE -->

## Objective (current checkpoint)

Build a searchable index from scanned files.

## Deliverables (current checkpoint)

- `.codex/skills/rag-index/indexer.py` — builds embeddings/keyword index
- Supports: full-text search, semantic search (with embeddings)
- Storage: local SQLite or JSON for portability

## Acceptance (current checkpoint)

- Index is persistent and incremental (only re-index changed files)
- Search returns ranked results

## Work log (current session)
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

### Index build (demo command)

```
$ python .codex/skills/rag-index/indexer.py build --manifest manifest.json --output index.db
Index built: 13 indexed, 0 skipped (unchanged), 0 removed, 0 errors.
```

### Search with ranked results (demo command)

```
$ python .codex/skills/rag-index/indexer.py search "directory scan" --index index.db --top-k 3
[
  {"rel_path": "scanner.py", "score": -3.2629, "snippet": "...Recursive >>>directory<<< scanner..."},
  {"rel_path": "__pycache__/scanner.cpython-313.pyc", "score": -3.238, "snippet": "...directory...scan_directories..."}
]
```

### Incremental indexing

```
First build:  {'indexed': 2, 'skipped': 0, 'removed': 0, 'errors': 0}
Second build: {'indexed': 0, 'skipped': 2, 'removed': 0, 'errors': 0}  # unchanged
Third build:  {'indexed': 1, 'skipped': 1, 'removed': 0, 'errors': 0}  # a.txt changed
Fourth build: {'indexed': 0, 'skipped': 1, 'removed': 1, 'errors': 0}  # b.txt removed
PASS: all incremental scenarios verified
```

### Multi-directory scan

```
$ python .codex/skills/rag-index/scanner.py .codex/skills/rag-index .codex/skills/vibe-loop --output manifest.json
Wrote 2 entries to manifest.json
```
Manifest contains entries from both roots with metadata (path, rel_path, size, mtime, type, root).

### Gitignore exclusion (temp dir test)

```
.gitignore contains: *.log, build/
Scan result: ['.gitignore', 'keep.py', 'src.py']  # ignore.log and build/ excluded
--no-gitignore: ['.gitignore', 'ignore.log', 'keep.py', 'src.py', 'build/out.js']
PASS: gitignore exclusions work
PASS: --no-gitignore works
```

### Include/exclude/file-type/depth filters

```
--include "*.md" --max-depth 1  → 20 .md files
--file-types .py --max-depth 1  → 11 .py files
--max-depth 0                   → root-level files only
```

## Active issues

(None)

## Decisions

(No decisions)
