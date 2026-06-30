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

## Deferral markers

Use `[DEFERRED]` to bypass a blocked stage or checkpoint without removing it
from the plan when independent later work can safely proceed. `(SKIP)` is still
recognized as a legacy bypass marker.

- Stage syntax: `## [DEFERRED] Stage 14 — Title`
- Checkpoint syntax: `### [DEFERRED] 14.1 — Title`
- Add a short reason and unblock/revisit condition near the deferred item.
- Advance behavior: `[DEFERRED]` stages/checkpoints are parsed but skipped when advancing.
- Dependency behavior: `[DEFERRED]` does not satisfy `depends_on`; dependent work should wait or also be deferred.
- Consolidation: `[DEFERRED]` stages/checkpoints are preserved only while they have a real owner/outcome.
- Reactivation: remove `[DEFERRED]` once the unblock condition is true.
