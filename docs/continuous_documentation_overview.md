# Continuous Documentation Overview

This document defines the design contract for the continuous-documentation
workflow introduced in Stage 21A.

## Purpose

The workflow repeatedly performs two deterministic phases:

1. Gap phase: detect missing documentation and apply targeted gap fixes.
2. Refactor phase: analyze existing documentation quality and apply refactors.

The loop may stop only when no `MAJOR` or `MODERATE` findings remain.

## Scope

In-scope documentation surfaces:

- Root and nested `README.md` files.
- `docs/**/*.md` repository documentation.
- Embedded guides in source files and scripts that contain user-facing sections
  (for example headings like `Usage`, `Quickstart`, `How to`, `Troubleshooting`,
  or equivalent structured guide blocks).
- Migration targets for external wiki content represented as file artifacts
  under `docs/wiki-export/`.

Out of scope:

- Generated docs from external services unless their source files are in-repo.
- Binary docs/assets without editable text sources.

## Wiki Migration Rules

When a finding recommends `create_wiki_page` or `migrate_to_wiki`, the workflow
must produce deterministic file artifacts instead of direct external writes:

- Wiki page markdown file under `docs/wiki-export/`.
- Mapping manifest entry in `docs/wiki-export/map.json`.
- Stable mapping key from repo path + heading slug.

Routing rules:

- Cross-cutting process docs are valid wiki migration candidates.
- Component/API-specific instructions should prefer code-specific docs in-repo.
- Migration recommendations must keep source-to-target traceability.

## Finding Schema

Each finding must use the following fields.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `finding_id` | string | yes | Stable deterministic id (for example hash of normalized phase/category/location payload). |
| `phase` | enum | yes | `gap` or `refactor`. |
| `category` | string | yes | Gap/refactor category (for example `missing_doc`, `accuracy`, `bloat`, `structure`). |
| `severity` | enum | yes | `MAJOR`, `MODERATE`, or `MINOR` from rubric. |
| `location` | object | yes | At minimum `path`; optional `section`, `line`, `context_key`. |
| `recommendation` | object | yes | Action payload with concrete next step (`edit_section`, `create_doc`, `create_wiki_page`, `migrate_to_wiki`, etc.). |

Recommended helper fields for deterministic processing:

- `evidence`: short excerpt or rationale supporting classification.
- `owner`: default `docs` or module owner if known.
- `depends_on`: list of finding IDs that must resolve first.

Example finding payload:

```json
{
  "finding_id": "gap:missing_doc:docs/setup.md#database-config:9f4b6e1a",
  "phase": "gap",
  "category": "missing_doc",
  "severity": "MAJOR",
  "location": {
    "path": "README.md",
    "section": "Configuration"
  },
  "recommendation": {
    "action": "create_doc",
    "target_path": "docs/setup/database.md",
    "summary": "Document required database variables and bootstrap order."
  },
  "evidence": "README references DATABASE_URL but provides no setup guidance."
}
```
