# Stage ordering

## Stage ID format

A stage ID is an integer with an optional alpha suffix.

- Grammar: `<int><optional alpha suffix>`
- Examples: `12`, `12A`, `12B`, `13`
- Regex (canonical): `^[0-9]+[A-Z]?$`

The stage ID is the token used in PLAN headers, e.g. `## Stage 12A — Title`.

## Ordering rules

Stages sort by numeric value first, then by suffix.

1) Compare the integer portion as a number (not lexicographically).
2) For equal integers, the empty suffix sorts before any letter suffix.
3) Suffix letters sort A–Z.

## Examples

- `11, 12, 12A, 12B, 13`
- `2, 2A, 2B, 3`
- `9, 10, 10A, 11`

## (SKIP) markers

Use `(SKIP)` to defer a stage or checkpoint without removing it from the plan.

- Stage syntax: `## (SKIP) Stage 14 — Title`
- Checkpoint syntax: `### (SKIP) 14.1 — Title`
- Advance behavior: `(SKIP)` checkpoints are parsed but skipped when advancing.
- Consolidation: `(SKIP)` stages/checkpoints are preserved (not archived).
- Reactivation: remove `(SKIP)` to make the item active again.
