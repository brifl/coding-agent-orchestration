# COMPONENT Workflow Contract

## Purpose

Translate **one architectural component** into a **component-level design**. This further specifies `AGENTS.md` for this mode.

## Instruction precedence & read order
1. As specified by `AGENTS.md`
2. This file
3. `.component/COMPONENTS_DESCRIPTION.md`
4. `.component/STATE.md`
6. `.component/HISTORY.md`
7. `.architecture/ARCHITECTURE_DESCRIPTION.md` (read-only reference)

## Scope

This layer receives **exactly one architectural element** (identified by its top-level number: 10, 20, 30…) and breaks it down into the concrete components required to implement it.

If it is not clear which element is being targeted, you MUST ask to confirm.

## Abstraction level for components

Describe components by **concrete role and technology** for a **buildable unit of work** that are required to implement the target architectural component.

The correct level of abstraction for a component (10.1, 10.2, ...) is one where:
- A specific technology (or set of technologies) is (are) identified for implementation
- The component has a clear objective and coherent set of responsabilities
- It maps to a recognizable delivrable (a service, a schema, a configured runtime, a UI module, ...)
- it remains large enough to likely require work on a few different features in order to deliver (roughly the size of one or a few "SPRINT" in AGILE).

For example, a component could be: "Authentication mechanism", with chosen technlogies (e.g. Oauth 2.0 implemented with Passport.js, hashing with bcrypt, ...). It should not be "A social media app" (that's too broad) nor should it be "A sign-in form" (this would be a checkpoint to implement).


## Numbering rules

Components are numbered as sub-elements of their main parent architectural element:

- Architectural element 10 → components 10.1, 10.2, …, 10.14...
- Architectural element 20 → components 20.1, 20.2, 20.3 …

There is no fixed upper bound on component count — use as many as relevant.You can group related components in the same unit (e.g. 10.1, 10.2, 11.1, 11.2, 11.3 for set of closely related components).

## Input requirements
The prompt must provide or reference:
- the target architectural element number (e.g. "element 10")
- access to the current `.architecture/ARCHITECTURE_DESCRIPTION.md` (or its relevant section)

If the architecture has not been reviewed/approved (status ≠ DONE in `.architecture/STATE.md`), log a warning in `.component/STATE.md` but proceed unless explicitly told to stop.

## Agentic Workflow Files to Update

Use `.component/STATE.md` OPTIONAL, to track core, hot topic issues that required immediate attention before moving forward. Blocking items.

Use `.component/HISTORY.md` to archive resolved questions and completed component reviews at each iteration.
