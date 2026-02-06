# Documentation Severity Rubric

This rubric defines deterministic `MAJOR|MODERATE|MINOR` classification for
continuous documentation findings.

## Classification Rules

1. Choose the highest severity that matches the evidence.
2. If multiple impacts apply, classify by highest user risk.
3. Prefer explicit failure evidence over subjective quality preference.
4. Severity is independent of fix size.

## Severity Criteria

| Severity | Definition | Deterministic triggers |
| --- | --- | --- |
| `MAJOR` | Missing or incorrect docs likely cause failed setup, unsafe behavior, or materially incorrect operation. | Required setup/usage/security information is absent or wrong; documented command/flow is known broken; migration omission would strand critical knowledge. |
| `MODERATE` | Docs are usable but incomplete, confusing, or stale in ways that materially slow correct usage. | Important section is partial/misaligned; structure causes repeated mis-navigation; duplicated content introduces conflicting guidance without immediate breakage. |
| `MINOR` | Quality polish issue with low risk to successful usage. | Tone/style inconsistency, minor redundancy, weak heading hierarchy, outdated non-critical examples, or formatting debt. |

## Phase-Specific Guidance

Gap-phase severity defaults:

- Missing required install/configuration/runbook docs: `MAJOR`.
- Missing non-critical explanatory section: `MODERATE`.
- Missing optional background/context section: `MINOR`.

Refactor-phase severity defaults:

- Inaccurate instructions with likely operational impact: `MAJOR`.
- Bloated/duplicated docs causing ambiguity but with clear workaround: `MODERATE`.
- Structure/readability cleanup with no correctness impact: `MINOR`.

## Example Classification Table

| Finding | Phase | Severity | Rationale |
| --- | --- | --- | --- |
| `README.md` points to `python tools/agentctl.py next --format json` (wrong flag order) | `refactor` | `MAJOR` | Copy-paste command fails and blocks core workflow execution. |
| `docs/skill_lifecycle.md` lacks migration steps for wiki-export artifacts | `gap` | `MODERATE` | Important for maintainability, but users can proceed with existing docs. |
| Two docs repeat the same glossary paragraph with minor wording drift | `refactor` | `MINOR` | Redundant and noisy but does not change behavior or correctness. |

## Tie-Break Rules

- If evidence is uncertain between `MAJOR` and `MODERATE`, classify as
  `MODERATE` and add an explicit validation task.
- If uncertainty is between `MODERATE` and `MINOR`, classify as `MINOR` unless
  repeated user confusion or support churn is documented.

## Required Output Fields Per Finding

Each classification must include:

- `severity`: one of `MAJOR|MODERATE|MINOR`.
- `rationale`: one-sentence justification tied to observable impact.
- `evidence`: concrete location or excerpt proving the gap/refactor issue.
