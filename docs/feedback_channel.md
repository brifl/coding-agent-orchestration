# Feedback Channel

The structured human feedback channel lets humans write prioritized feedback entries in `.vibe/FEEDBACK.md`, have them automatically converted to Issue records in `STATE.md`, and have the dispatcher route to `issues_triage` when unprocessed feedback exists.

## FEEDBACK.md format

Each entry is a Markdown checkbox with required sub-fields:

```markdown
- [ ] FEEDBACK-001: Short description of the feedback
  - Impact: MAJOR
  - Type: concern
  - Description: Detailed description of the issue or question.
  - Expected: What the correct behavior or outcome should be.
  - Proposed action: What you suggest the agent should do about it.
```

### Field reference

| Field | Required | Valid values |
|-------|----------|-------------|
| `Impact` | Yes | `QUESTION`, `MINOR`, `MAJOR`, `BLOCKER` |
| `Type` | Yes | `bug`, `feature`, `concern`, `question` |
| `Description` | Yes | Free text |
| `Expected` | Yes | Free text |
| `Proposed action` | Yes | Free text |

### Rules

- FEEDBACK-IDs must be unique within the file.
- The checkbox `[ ]` marks an unprocessed entry; `[x]` means processed.
- After injection, a `<!-- processed: ISSUE-NNN -->` comment is added to the header line.

## Workflow: write → inject → triage → ack

### Step 1 — Write feedback

Add one or more entries to `.vibe/FEEDBACK.md`:

```markdown
- [ ] FEEDBACK-002: Config validation does not catch missing required fields
  - Impact: MAJOR
  - Type: bug
  - Description: When a required field is absent from the config, the validator silently passes.
  - Expected: Validator should exit 2 with a field-level diagnostic.
  - Proposed action: Add a required-field check in _validate_config().
```

Validate the file is well-formed:

```
python tools/agentctl.py --repo-root . feedback validate
```

### Step 2 — Inject feedback as Issues

Run inject to convert entries to `STATE.md` Issue records:

```
python tools/agentctl.py --repo-root . feedback inject
```

Use `--dry-run` to preview without modifying files:

```
python tools/agentctl.py --repo-root . feedback inject --dry-run
```

After injection, `STATE.md` `## Active issues` will contain a new issue block and FEEDBACK.md entries will be marked `[x]` with a processed comment.

### Step 3 — Dispatcher routes to issues_triage

When `agentctl next` detects unprocessed feedback, it routes to `issues_triage` instead of the normal next role:

```json
{
  "recommended_role": "issues_triage",
  "reason": "Unprocessed human feedback: 2 entries (top impact: MAJOR). Run agentctl feedback inject."
}
```

The dispatcher selects the highest-impact entry to surface in the reason string. Impact priority: `BLOCKER > MAJOR > MINOR > QUESTION`.

### Step 4 — Acknowledge (archive) processed entries

After the issues have been triaged, archive processed feedback entries to `HISTORY.md`:

```
python tools/agentctl.py --repo-root . feedback ack
```

This:
- Appends entries to the `## Feedback archive` section in `HISTORY.md` (creates the section if absent).
- Removes archived entries from `FEEDBACK.md` (unprocessed entries are left untouched).
- Prints a summary: `"Archived N feedback entries to HISTORY.md."`

Running `ack` again on an already-clean `FEEDBACK.md` prints `"Nothing to archive."` and exits 0.

## Dispatcher integration

`agentctl validate` emits a warning when `FEEDBACK.md` has unprocessed entries:

```
warnings: [".vibe/FEEDBACK.md: Unprocessed human feedback: 2 entries (top impact: MAJOR). Run agentctl feedback inject."]
```

The feedback gate fires **after** hard-stop conditions (missing LOOP_RESULT, DECISION_REQUIRED) and **before** the normal checkpoint routing. This ensures feedback is always surfaced promptly.

## Backward compatibility

Repos without `.vibe/FEEDBACK.md` are entirely unaffected:
- `_has_unprocessed_feedback` returns `(False, "")`.
- `agentctl validate` emits no FEEDBACK.md warning.
- All `agentctl feedback` subcommands exit 0 gracefully when the file is absent.
