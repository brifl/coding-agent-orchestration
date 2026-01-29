# Context Schema

This document defines the schema for the `.vibe/CONTEXT.md` file. The schema
separates persistent project context from ephemeral session notes.

## Structure

### Persistent (project) context
The following sections should be stable over time and updated incrementally:

- **Architecture**: High-level overview of the system and major components.
- **Key Decisions**: Important decisions with date and rationale.
- **Gotchas**: Known pitfalls, edge cases, or workflow traps.
- **Hot Files**: Files or paths that are frequently edited or critical.

### Ephemeral (session) context
This section is session-scoped and should be cleared/rotated when stale:

- **Agent Notes**: Temporary notes, current checkpoint focus, or open threads.

## Formatting guidance

- Keep entries short and scannable (bullets preferred).
- Add dates to decisions or time-sensitive notes.
- Avoid duplicating information that already lives in STATE/PLAN.
