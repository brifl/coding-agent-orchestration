# COMPONENT Workflow Contract

## Purpose

Translate **one architectural element** into a **component-level design**. This further specifies `AGENTS.md` for this mode.

## Instruction precedence & read order
1. As specified by `AGENTS.md`
2. This file
3. `.component/COMPONENTS_DESCRIPTIONS.md`
4. `.component/STATE.md`
6. `.component/HISTORY.md`
7. `.architecture/ARCHITECTURE_DESCRIPTION.md` (read-only reference)

## Meta-templates

| File | Role |
|------|------|
| `components_description_tplt.md` | Output template and deliverable for the component design |
| `state_tplt.md` | Blocking issues requiring immediate attention |
| `plan_tplt.md` | Component-level questions requiring discussion or decision |
| `history_tplt.md` | Resolved questions and completed component reviews |

## Scope

This mode receives **exactly one architectural element** (identified by its top-level number: 10, 20, 30...) and breaks it down into the concrete components required to implement it.

## Input requirements

The prompt must provide or reference:
- the target architectural element number (e.g. "element 10")
- access to the current `.architecture/ARCHITECTURE_DESCRIPTION.md` (or its relevant section)

If the architecture has not been reviewed/approved (status ≠ DONE in `.architecture/STATE.md`), log a warning in `.component/STATE.md` but proceed unless explicitly told to stop.

## Abstraction level

Describe components by **concrete role and technology** for a **buildable unit of work** required to implement the target architectural element.

The correct level of abstraction for a component (10.1, 10.2, ...) is one where:
- A specific technology (or set of technologies) is identified for implementation
- The component has a clear objective and coherent set of responsibilities
- It maps to a recognizable deliverable (a service, a schema, a configured runtime, a UI module, ...)
- It remains large enough to likely require work on a few different features in order to deliver (roughly the size of one or a few sprints)

For example, a component could be: "Authentication mechanism", with chosen technologies (e.g. OAuth 2.0 implemented with Passport.js, hashing with bcrypt, ...). It should not be "A social media app" (too broad) nor should it be "A sign-in form" (that would be a checkpoint to implement).

## Numbering rules

Components are numbered as sub-elements of their parent architectural element:

- Architectural element 10 → components 10.1, 10.2, ..., 10.14...
- Architectural element 20 → components 20.1, 20.2, 20.3 ...

There is no fixed upper bound on component count — use as many as relevant. You can group related components in the same unit (e.g. 10.1, 10.2, 11.1, 11.2, 11.3 for sets of closely related components).

## Planning rule

Use `.component/PLAN.md` to track component-level questions that require discussion, investigation, or explicit decision. What needs to happen next so we can advance the development of the components for this project.

Use `.component/STATE.md` for blocking issues that require immediate attention before moving forward.
