# Coding Conventions

## Imports

- Every file starts with `from __future__ import annotations`.
- Use **absolute imports** only (`from engine.models import ...`), never
  relative (`from ..models import ...`).
- Order: stdlib, then third-party, then local — alphabetized within each
  group. Enforced by `ruff` rule `I`.
- No wildcard imports (`from module import *`).

## Type annotations

- Use **modern union syntax**: `X | None`, not `Optional[X]`.
- Use **lowercase built-in generics**: `list`, `dict`, `tuple`, `set`,
  not `List`, `Dict`, `Tuple`, `Set` from `typing`.
- Use `Literal` for fixed string enums
  (e.g. `ToolStatus = Literal["ok", "retryable", "fatal", "rejected"]`).
- Annotate **all** function signatures including return types.
- Annotate **all** dataclass and Pydantic model fields.

## Classes

- PascalCase names.
- Use `@dataclass(frozen=True)` by default. Mutable dataclasses are
  acceptable only for objects that hold runtime state (stores, caches,
  providers).
- Pydantic models use `model_config = ConfigDict(extra="forbid", frozen=True)`
  and constrain fields with `Field(min_length=1)`, `Field(ge=0)`, etc.

## Functions

- `lowercase_with_underscores`.
- Private helpers are prefixed with `_`
  (e.g. `_build_keep_full`, `_normalize_update`).
- Use **keyword-only arguments** (the `*` separator) when a function
  accepts three or more parameters.
- Always annotate the return type, even if it is `None`.

## Interfaces

- Define interfaces with `Protocol`, not `ABC`.
- Factory callables are typed via a `Protocol` class with a `__call__`
  method (e.g. `DocBuilderFactory`, `PackingStrategyFactory`).

## Error handling

- Custom exception classes inherit from `ValueError` (not `Exception`).
- Name them `{Domain}Error` or `{Domain}ValidationError`
  (e.g. `ContextPackError`, `NarratorOutputValidationError`).

## Schemas

- Validation functions are named `validate_{role}_output(payload)`.
  They delegate to a shared `_validate_schema()` helper that takes the
  schema dict, exception class, and label.

## Tests

- Test files are named `test_{module}.py`.
- Test functions are named `test_{behaviour_description}` — descriptive,
  no numeric suffixes.
- Use plain `assert` statements, not `unittest`-style methods.
- Shared fixtures live in `tests/conftest.py`.
- Module-local test helpers are prefixed with `_`
  (e.g. `_doc_type()`, `_snapshot()`).

## Docstrings

- Every file has a **module-level docstring** (one-liner is fine).
- Public and base classes have a class docstring.
- Docstrings on individual methods are optional — add them when the
  logic is not self-evident from the signature.

## Linting

- **ruff** with rules `E`, `F`, `I`; line length 88; target `py310`.
- Run `ruff check` and `ruff format` before committing.
