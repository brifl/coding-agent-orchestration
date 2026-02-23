#!/usr/bin/env python3
"""
plan_pipeline.py

PipelineConfig schema and config resolution for `agentctl plan`.

Config resolution order (highest priority first):
  1. CLI flags
  2. Repo-local  .vibe/plan_pipeline.json
  3. Global      ~/.vibe/plan_pipeline.json
  4. Defaults
"""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass
class PipelineConfig:
    """Resolved configuration for one plan-pipeline run."""

    problem_statement: str
    provider: str
    dry_run: bool = False
    output_path: str = ".vibe/PLAN.md"
    overwrite: bool = False

    # Provider-specific options forwarded verbatim to the provider layer.
    provider_options: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Config file resolution
# ---------------------------------------------------------------------------

_CONFIG_FILENAME = "plan_pipeline.json"


def _load_json_config(path: Path) -> dict[str, Any]:
    """Load a JSON config file; return {} on missing or parse error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _global_config_path() -> Path:
    return Path.home() / ".vibe" / _CONFIG_FILENAME


def _repo_config_path(repo_root: Path) -> Path:
    return repo_root / ".vibe" / _CONFIG_FILENAME


def _merge_config(
    repo_root: Path,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """Merge config sources (lowest → highest priority): global → repo-local → overrides."""
    merged: dict[str, Any] = {}
    for source in (
        _load_json_config(_global_config_path()),
        _load_json_config(_repo_config_path(repo_root)),
        overrides,
    ):
        merged.update({k: v for k, v in source.items() if v is not None})
    return merged


# ---------------------------------------------------------------------------
# Provider Protocol (injectable for offline testing)
# ---------------------------------------------------------------------------

@runtime_checkable
class PipelineProvider(Protocol):
    """Protocol for LLM providers used in pipeline steps."""

    def call(self, prompt_id: str, inputs: dict[str, Any]) -> str:
        """Call the provider with the given prompt and inputs; return raw string output."""
        ...


# ---------------------------------------------------------------------------
# Pipeline step executor
# ---------------------------------------------------------------------------

class PipelineStepError(Exception):
    """Raised when a pipeline step fails execution or schema validation.

    Attributes:
        step_name:  Human-readable step name (prompt_id with 'prompt.' stripped).
        prompt_id:  The prompt ID that caused the failure.
        raw_output: First 200 chars of the raw provider output for diagnosis.
    """

    def __init__(
        self, step_name: str, prompt_id: str, message: str, raw_output: str = ""
    ) -> None:
        self.step_name = step_name
        self.prompt_id = prompt_id
        self.raw_output = raw_output
        super().__init__(f"[{step_name}] {prompt_id}: {message}")


# Minimal required-key schema per prompt step.  Keys not listed here have no
# required fields (unknown prompt_ids pass with an empty required set).
_STEP_REQUIRED_KEYS: dict[str, list[str]] = {
    "prompt.ideation": ["features"],
    "prompt.feature_breakdown": ["feature_breakdown"],
    "prompt.architecture": ["architecture"],
    "prompt.milestones": ["milestones"],
    "prompt.stages_from_milestones": ["stages"],
    "prompt.checkpoints_from_stage": ["checkpoints"],
}

_PROVIDER_CALL_EXCEPTIONS = (
    TimeoutError,
    OSError,
    ValueError,
    TypeError,
    RuntimeError,
)


def _run_pipeline_step(
    prompt_id: str,
    inputs: dict[str, Any],
    config: PipelineConfig,
    *,
    provider: PipelineProvider | None = None,
) -> dict[str, Any]:
    """Run one pipeline step: call provider, parse JSON output, validate schema.

    Args:
        prompt_id: The prompt ID to invoke (e.g. ``"prompt.ideation"``).
        inputs:    Variable dict forwarded to the provider verbatim.
        config:    Resolved pipeline configuration (used for provider lookup when
                   no explicit *provider* stub is supplied).
        provider:  Optional provider override.  Pass a stub here for offline
                   testing — if ``None``, the function raises immediately because
                   real provider integration is deferred to checkpoint 23.2.

    Returns:
        Parsed ``dict`` output from the provider, validated against the
        per-step required-key schema.

    Raises:
        PipelineStepError: If the provider call fails, returns non-JSON, returns
                           a non-object JSON value, or the output is missing
                           required keys for this step.
    """
    step_name = prompt_id.removeprefix("prompt.")
    required_keys = _STEP_REQUIRED_KEYS.get(prompt_id, [])

    if provider is None:
        raise PipelineStepError(
            step_name,
            prompt_id,
            "No provider available. Pass a provider stub or configure config.provider "
            "(real provider integration implemented in checkpoint 23.2).",
        )

    # --- call provider ---
    try:
        raw = provider.call(prompt_id, inputs)
    except _PROVIDER_CALL_EXCEPTIONS as exc:
        raise PipelineStepError(
            step_name,
            prompt_id,
            f"Provider call raised {type(exc).__name__}: {exc}",
        ) from exc
    except Exception as exc:
        # Keep a final catch for unknown provider-side failures while preserving
        # existing PipelineStepError behavior and diagnostics.
        raise PipelineStepError(
            step_name,
            prompt_id,
            f"Provider call raised {type(exc).__name__}: {exc}",
        ) from exc

    # --- parse JSON ---
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        snippet = (raw or "")[:200]
        raise PipelineStepError(
            step_name,
            prompt_id,
            f"Provider returned non-JSON: {exc}",
            raw_output=snippet,
        ) from exc

    if not isinstance(result, dict):
        snippet = (raw or "")[:200]
        raise PipelineStepError(
            step_name,
            prompt_id,
            f"Provider returned non-object JSON (got {type(result).__name__})",
            raw_output=snippet,
        )

    # --- validate required keys ---
    missing = [k for k in required_keys if k not in result]
    if missing:
        snippet = (raw or "")[:200]
        raise PipelineStepError(
            step_name,
            prompt_id,
            f"Output missing required keys: {missing}",
            raw_output=snippet,
        )

    return result


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------

# The ordered sequence of prompt IDs executed during a full pipeline run.
_PIPELINE_SEQUENCE: list[str] = [
    "prompt.ideation",
    "prompt.feature_breakdown",
    "prompt.architecture",
    "prompt.milestones",
    "prompt.stages_from_milestones",
    "prompt.checkpoints_from_stage",
]


@dataclass
class PipelineResult:
    """Result of a complete plan authoring pipeline run."""

    run_id: str
    stages: list[dict[str, Any]]
    checkpoints: list[dict[str, Any]]
    # All step outputs keyed by prompt_id, for downstream use.
    step_outputs: dict[str, Any] = field(default_factory=dict)


def _step_inputs(
    prompt_id: str,
    config: PipelineConfig,
    previous_output: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build the input dict for a pipeline step.

    The base always includes *problem_statement* from config; all keys from
    the previous step's output are merged in so each step can access the full
    accumulated context.
    """
    inputs: dict[str, Any] = {"problem_statement": config.problem_statement}
    if previous_output:
        inputs.update(previous_output)
    return inputs


def _run_dir(repo_root: Path, run_id: str) -> Path:
    """Return the directory used to store step outputs for *run_id*."""
    return repo_root / ".vibe" / "plan_pipeline" / run_id


def run_plan_pipeline(
    config: PipelineConfig,
    repo_root: Path,
    *,
    provider: PipelineProvider | None = None,
    run_id: str | None = None,
    resume_run_id: str | None = None,
) -> PipelineResult:
    """Run the full 6-step plan authoring pipeline.

    Steps are executed in sequence: ideation → feature_breakdown →
    architecture → milestones → stages_from_milestones →
    checkpoints_from_stage.

    Each step's output is saved to
    ``.vibe/plan_pipeline/<run_id>/step_<N>_<name>.json``.  On resume, any
    step whose output file already exists is loaded from disk rather than
    calling the provider again.

    Args:
        config:        Resolved pipeline configuration.
        repo_root:     Repository root (used for the run directory).
        provider:      Optional provider stub.  If ``None`` the real provider
                       integration (checkpoint 23.2+) would be used; for now a
                       missing provider raises ``PipelineStepError`` on the
                       first step.
        run_id:        Explicit run ID.  A short UUID is generated if omitted.
        resume_run_id: Run ID of a previous run to resume.  Existing step
                       output files from that run are reused; missing files
                       trigger a fresh provider call.

    Returns:
        ``PipelineResult`` containing *stages* and *checkpoints* extracted
        from the final two steps.

    Raises:
        PipelineStepError: If any step fails.
    """
    effective_run_id = run_id or uuid.uuid4().hex[:8]
    run_dir = _run_dir(
        repo_root, resume_run_id if resume_run_id else effective_run_id
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    step_outputs: dict[str, Any] = {}
    previous_output: dict[str, Any] | None = None
    total = len(_PIPELINE_SEQUENCE)

    for i, prompt_id in enumerate(_PIPELINE_SEQUENCE, 1):
        step_name = prompt_id.removeprefix("prompt.")
        step_file = run_dir / f"step_{i}_{step_name}.json"

        if step_file.exists():
            print(
                f"Step {i}/{total}: {prompt_id} (resumed from {step_file.name})",
                file=sys.stderr,
            )
            loaded = json.loads(step_file.read_text(encoding="utf-8"))
            step_outputs[prompt_id] = loaded
            previous_output = loaded
            continue

        print(f"Step {i}/{total}: running {prompt_id}...", file=sys.stderr)
        inputs = _step_inputs(prompt_id, config, previous_output)
        output = _run_pipeline_step(prompt_id, inputs, config, provider=provider)

        step_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
        step_outputs[prompt_id] = output
        previous_output = output

    stages = step_outputs.get("prompt.stages_from_milestones", {}).get("stages", [])
    checkpoints = step_outputs.get("prompt.checkpoints_from_stage", {}).get(
        "checkpoints", []
    )
    return PipelineResult(
        run_id=effective_run_id,
        stages=stages,
        checkpoints=checkpoints,
        step_outputs=step_outputs,
    )


# ---------------------------------------------------------------------------
# PLAN.md writer
# ---------------------------------------------------------------------------

from constants import COMPLEXITY_BUDGET as _PLAN_WRITER_COMPLEXITY_BUDGET


def _render_checkpoint_section(cp: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Render one checkpoint as PLAN.md lines.

    Returns (lines, complexity_warnings).
    """
    cp_id = str(cp.get("id", ""))
    cp_title = cp.get("title", f"Checkpoint {cp_id}")
    cp_obj = cp.get("objective", "")
    cp_deliverables: list[str] = cp.get("deliverables") or []
    cp_acceptance: list[str] = cp.get("acceptance") or []
    cp_demo: list[str] = cp.get("demo_commands") or []

    warnings: list[str] = []
    lines: list[str] = []

    lines.append(f"### {cp_id} — {cp_title}")
    lines.append("")
    lines.append("* **Objective:**")
    lines.append(f"  {cp_obj}" if cp_obj else "  (TBD)")
    lines.append("")
    lines.append("* **Deliverables:**")
    for d in cp_deliverables:
        lines.append(f"  * {d}")
    if not cp_deliverables:
        lines.append("  * (TBD)")
    lines.append("")
    lines.append("* **Acceptance:**")
    for a in cp_acceptance:
        lines.append(f"  * {a}")
    if not cp_acceptance:
        lines.append("  * (TBD)")
    lines.append("")
    lines.append("* **Demo commands:**")
    for d in cp_demo:
        lines.append(f"  * `{d}`")
    if not cp_demo:
        lines.append("  * `echo done`")
    lines.append("")
    lines.append("* **Evidence:**")
    lines.append("  * (TBD)")
    lines.append("")
    lines.append("---")
    lines.append("")

    budget = _PLAN_WRITER_COMPLEXITY_BUDGET
    for field, items, key in (
        ("Deliverables", cp_deliverables, "Deliverables"),
        ("Acceptance", cp_acceptance, "Acceptance"),
        ("Demo commands", cp_demo, "Demo commands"),
    ):
        if len(items) > budget[key]:
            warnings.append(
                f"Checkpoint {cp_id}: {field} ({len(items)}) exceeds budget "
                f"({budget[key]}); consider splitting."
            )

    return lines, warnings


def render_plan_md(result: PipelineResult) -> tuple[str, list[str]]:
    """Convert a ``PipelineResult`` into a PLAN.md document string.

    Checkpoints are grouped under their parent stage.  Each checkpoint is
    checked against the complexity budget; warnings are collected and returned
    but do **not** block rendering.

    Args:
        result: A ``PipelineResult`` produced by ``run_plan_pipeline``.

    Returns:
        ``(plan_text, warnings)`` where *plan_text* is a complete PLAN.md
        string and *warnings* is a (possibly empty) list of complexity
        advisory strings.
    """
    from collections import defaultdict

    stages: list[dict[str, Any]] = result.stages or []
    checkpoints: list[dict[str, Any]] = result.checkpoints or []

    # Group checkpoints by stage_id (coerced to str for dict key consistency).
    stage_checkpoints: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cp in checkpoints:
        sid = str(cp.get("stage_id", stages[0].get("id", "1") if stages else "1"))
        stage_checkpoints[sid].append(cp)

    all_warnings: list[str] = []
    lines: list[str] = ["# PLAN", ""]

    for stage in stages:
        sid = str(stage.get("id", ""))
        sname = stage.get("name", f"Stage {sid}")
        sobj = stage.get("objective", "")

        lines.append(f"## Stage {sid} — {sname}")
        lines.append("")
        lines.append("**Stage objective:**")
        lines.append(sobj if sobj else "(TBD)")
        lines.append("")
        lines.append("---")
        lines.append("")

        for cp in stage_checkpoints.get(sid, []):
            cp_lines, cp_warnings = _render_checkpoint_section(cp)
            lines.extend(cp_lines)
            all_warnings.extend(cp_warnings)

    return "\n".join(lines), all_warnings


# ---------------------------------------------------------------------------
# Validation / fail-fast
# ---------------------------------------------------------------------------

class PipelineConfigError(ValueError):
    """Raised when PipelineConfig cannot be resolved or is invalid."""


def resolve_config(
    repo_root: Path,
    *,
    problem_statement: str | None = None,
    provider: str | None = None,
    dry_run: bool = False,
    output_path: str | None = None,
    overwrite: bool = False,
) -> PipelineConfig:
    """Resolve CLI flags against config files and return a validated PipelineConfig.

    Raises PipelineConfigError on missing required fields or output-path conflicts.
    """
    cli_overrides: dict[str, Any] = {
        k: v
        for k, v in {
            "problem_statement": problem_statement,
            "provider": provider,
            "output_path": output_path,
        }.items()
        if v is not None
    }
    # dry_run and overwrite are flags (bool), always take them from CLI
    merged = _merge_config(repo_root, cli_overrides)

    resolved_problem = merged.get("problem_statement")
    resolved_provider = merged.get("provider")
    resolved_output = merged.get("output_path", ".vibe/PLAN.md")
    resolved_dry_run = dry_run
    resolved_overwrite = overwrite
    provider_options: dict[str, Any] = merged.get("provider_options") or {}

    # Fail-fast: problem statement is mandatory
    if not resolved_problem or not str(resolved_problem).strip():
        raise PipelineConfigError(
            "Missing --problem-statement. "
            "Provide it via CLI or set 'problem_statement' in "
            ".vibe/plan_pipeline.json or ~/.vibe/plan_pipeline.json."
        )

    # Fail-fast: provider is mandatory unless dry-run (no LLM calls in dry-run)
    if not resolved_dry_run and (not resolved_provider or not str(resolved_provider).strip()):
        raise PipelineConfigError(
            "Missing provider. "
            "Provide it via --provider or set 'provider' in "
            ".vibe/plan_pipeline.json or ~/.vibe/plan_pipeline.json."
        )

    # Fail-fast: output path conflict (exists + no --overwrite) — only in non-dry-run
    if not resolved_dry_run:
        out = Path(resolved_output)
        if not out.is_absolute():
            out = repo_root / out
        if out.exists() and not resolved_overwrite:
            raise PipelineConfigError(
                f"Output file already exists: {out}. "
                "Use --overwrite to replace it, or choose a different --output path."
            )

    return PipelineConfig(
        problem_statement=str(resolved_problem).strip(),
        provider=str(resolved_provider).strip() if resolved_provider else "",
        dry_run=resolved_dry_run,
        output_path=resolved_output,
        overwrite=resolved_overwrite,
        provider_options=provider_options,
    )
