"""Tests for the plan authoring pipeline (checkpoints 23.1–23.4)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Ensure tools/ is on the import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from plan_pipeline import (  # noqa: E402
    PipelineConfig,
    PipelineStepError,
    _run_pipeline_step,
)


# ---------------------------------------------------------------------------
# Stub provider helpers
# ---------------------------------------------------------------------------

class _StubProvider:
    """Provider stub that returns a fixed JSON string."""

    def __init__(self, response: str) -> None:
        self._response = response

    def call(self, prompt_id: str, inputs: dict[str, Any]) -> str:
        return self._response


class _RaisingProvider:
    """Provider stub that raises on call."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def call(self, prompt_id: str, inputs: dict[str, Any]) -> str:
        raise self._exc


def _make_config(**kwargs: Any) -> PipelineConfig:
    defaults = dict(
        problem_statement="Build a todo app",
        provider="stub",
        dry_run=False,
        output_path=".vibe/PLAN.md",
        overwrite=False,
    )
    defaults.update(kwargs)
    return PipelineConfig(**defaults)


# ---------------------------------------------------------------------------
# pipeline_step — happy-path tests
# ---------------------------------------------------------------------------

class TestRunPipelineStepSuccess:
    def test_pipeline_step_well_formed_json_returns_dict(self) -> None:
        """Stub returning well-formed JSON with required keys → structured dict."""
        payload = {"features": ["auth", "crud", "export"]}
        stub = _StubProvider(json.dumps(payload))
        config = _make_config()

        result = _run_pipeline_step(
            "prompt.ideation", {"problem": "Build a todo app"}, config, provider=stub
        )

        assert result == payload

    def test_pipeline_step_passes_unknown_prompt_id_without_required_keys(self) -> None:
        """Unknown prompt IDs have no required-key schema; any dict passes."""
        payload = {"arbitrary_key": 42}
        stub = _StubProvider(json.dumps(payload))
        config = _make_config()

        result = _run_pipeline_step(
            "prompt.custom_step", {}, config, provider=stub
        )

        assert result == payload

    def test_pipeline_step_feature_breakdown_required_key(self) -> None:
        payload = {"feature_breakdown": [{"name": "login", "priority": "P0"}]}
        stub = _StubProvider(json.dumps(payload))
        config = _make_config()

        result = _run_pipeline_step(
            "prompt.feature_breakdown", {"features": ["login"]}, config, provider=stub
        )

        assert "feature_breakdown" in result

    def test_pipeline_step_extra_keys_allowed(self) -> None:
        """Extra keys beyond the required set are accepted."""
        payload = {"features": ["x"], "metadata": {"version": 1}}
        stub = _StubProvider(json.dumps(payload))
        config = _make_config()

        result = _run_pipeline_step(
            "prompt.ideation", {}, config, provider=stub
        )

        assert result["metadata"]["version"] == 1


# ---------------------------------------------------------------------------
# pipeline_step — failure / diagnostic tests
# ---------------------------------------------------------------------------

class TestRunPipelineStepFailures:
    def test_pipeline_step_malformed_json_raises_pipeline_step_error(self) -> None:
        """Malformed JSON → PipelineStepError with diagnostic."""
        stub = _StubProvider("not valid json {{{")
        config = _make_config()

        with pytest.raises(PipelineStepError) as exc_info:
            _run_pipeline_step("prompt.ideation", {}, config, provider=stub)

        err = exc_info.value
        assert err.prompt_id == "prompt.ideation"
        assert err.step_name == "ideation"
        assert "non-JSON" in str(err)
        # raw_output snippet is included
        assert "not valid json" in err.raw_output

    def test_pipeline_step_missing_required_key_raises_pipeline_step_error(self) -> None:
        """Well-formed JSON missing a required key → PipelineStepError."""
        payload = {"wrong_key": "value"}
        stub = _StubProvider(json.dumps(payload))
        config = _make_config()

        with pytest.raises(PipelineStepError) as exc_info:
            _run_pipeline_step("prompt.ideation", {}, config, provider=stub)

        err = exc_info.value
        assert "features" in str(err)
        assert err.step_name == "ideation"

    def test_pipeline_step_non_object_json_raises_pipeline_step_error(self) -> None:
        """JSON array instead of object → PipelineStepError."""
        stub = _StubProvider(json.dumps(["item1", "item2"]))
        config = _make_config()

        with pytest.raises(PipelineStepError) as exc_info:
            _run_pipeline_step("prompt.ideation", {}, config, provider=stub)

        assert "non-object" in str(exc_info.value)

    def test_pipeline_step_provider_exception_wrapped_in_pipeline_step_error(self) -> None:
        """Provider raising RuntimeError → PipelineStepError wrapping original."""
        stub = _RaisingProvider(RuntimeError("network timeout"))
        config = _make_config()

        with pytest.raises(PipelineStepError) as exc_info:
            _run_pipeline_step("prompt.ideation", {}, config, provider=stub)

        err = exc_info.value
        assert "RuntimeError" in str(err)
        assert "network timeout" in str(err)
        assert err.__cause__ is not None

    def test_pipeline_step_no_provider_raises_pipeline_step_error(self) -> None:
        """No provider supplied → PipelineStepError with clear message."""
        config = _make_config()

        with pytest.raises(PipelineStepError) as exc_info:
            _run_pipeline_step("prompt.ideation", {}, config, provider=None)

        assert "No provider" in str(exc_info.value)

    def test_pipeline_step_error_attributes_present(self) -> None:
        """PipelineStepError exposes step_name, prompt_id, raw_output."""
        stub = _StubProvider("bad json")
        config = _make_config()

        with pytest.raises(PipelineStepError) as exc_info:
            _run_pipeline_step("prompt.architecture", {}, config, provider=stub)

        err = exc_info.value
        assert err.step_name == "architecture"
        assert err.prompt_id == "prompt.architecture"
        assert isinstance(err.raw_output, str)

    def test_pipeline_step_raw_output_snippet_truncated(self) -> None:
        """raw_output is at most 200 chars even for very long bad output."""
        long_bad = "x" * 500
        stub = _StubProvider(long_bad)
        config = _make_config()

        with pytest.raises(PipelineStepError) as exc_info:
            _run_pipeline_step("prompt.ideation", {}, config, provider=stub)

        assert len(exc_info.value.raw_output) <= 200


# ---------------------------------------------------------------------------
# pipeline_orchestration — run_plan_pipeline tests
# ---------------------------------------------------------------------------

from plan_pipeline import PipelineResult, run_plan_pipeline  # noqa: E402


# Preset provider responses for each pipeline step (all with required keys).
_FULL_PIPELINE_RESPONSES: dict[str, Any] = {
    "prompt.ideation": json.dumps({"features": ["auth", "crud"]}),
    "prompt.feature_breakdown": json.dumps({"feature_breakdown": [{"name": "auth"}]}),
    "prompt.architecture": json.dumps({"architecture": {"components": ["api", "db"]}}),
    "prompt.milestones": json.dumps({"milestones": [{"name": "MVP"}]}),
    "prompt.stages_from_milestones": json.dumps({"stages": [{"id": "1", "name": "MVP"}]}),
    "prompt.checkpoints_from_stage": json.dumps({"checkpoints": [{"id": "1.0", "title": "Init"}]}),
}


class _MappingProvider:
    """Provider stub returning preset JSON responses by prompt_id."""

    def __init__(self, responses: dict[str, str], *, call_log: list[str] | None = None) -> None:
        self._responses = responses
        self._call_log = call_log if call_log is not None else []

    def call(self, prompt_id: str, inputs: dict[str, Any]) -> str:
        self._call_log.append(prompt_id)
        return self._responses.get(prompt_id, json.dumps({"result": f"ok for {prompt_id}"}))


class TestRunPipelineOrchestration:
    def test_pipeline_orchestration_6_steps_returns_pipeline_result(
        self, tmp_path: Path
    ) -> None:
        """Full 6-step pipeline with stub produces PipelineResult with stages and checkpoints."""
        call_log: list[str] = []
        provider = _MappingProvider(_FULL_PIPELINE_RESPONSES, call_log=call_log)
        config = _make_config()

        result = run_plan_pipeline(config, tmp_path, provider=provider, run_id="test-run")

        assert isinstance(result, PipelineResult)
        assert result.run_id == "test-run"
        assert result.stages == [{"id": "1", "name": "MVP"}]
        assert result.checkpoints == [{"id": "1.0", "title": "Init"}]
        assert len(call_log) == 6  # all steps called

    def test_pipeline_orchestration_creates_step_output_files(
        self, tmp_path: Path
    ) -> None:
        """Each step writes its output to disk."""
        provider = _MappingProvider(_FULL_PIPELINE_RESPONSES)
        config = _make_config()

        run_plan_pipeline(config, tmp_path, provider=provider, run_id="files-run")

        run_dir = tmp_path / ".vibe" / "plan_pipeline" / "files-run"
        assert run_dir.is_dir()
        step_files = list(run_dir.glob("step_*.json"))
        assert len(step_files) == 6

    def test_pipeline_orchestration_resume_skips_completed_steps(
        self, tmp_path: Path
    ) -> None:
        """Resume loads existing step files; only missing steps call the provider."""
        call_log: list[str] = []
        provider = _MappingProvider(_FULL_PIPELINE_RESPONSES, call_log=call_log)
        config = _make_config()

        # First full run — all 6 steps called
        run_plan_pipeline(config, tmp_path, provider=provider, run_id="resume-run")
        assert len(call_log) == 6

        # Delete step 3 (architecture) output to simulate partial failure
        run_dir = tmp_path / ".vibe" / "plan_pipeline" / "resume-run"
        (run_dir / "step_3_architecture.json").unlink()

        # Resume run — only step 3 (and steps 4-6 already have files) should re-run
        call_log.clear()
        run_plan_pipeline(
            config, tmp_path, provider=provider, resume_run_id="resume-run"
        )
        # Only step 3 is missing; steps 1,2,4,5,6 have files → only step 3 re-called
        assert call_log == ["prompt.architecture"]

    def test_pipeline_orchestration_step_outputs_accessible(
        self, tmp_path: Path
    ) -> None:
        """step_outputs dict contains all 6 step outputs keyed by prompt_id."""
        provider = _MappingProvider(_FULL_PIPELINE_RESPONSES)
        config = _make_config()

        result = run_plan_pipeline(config, tmp_path, provider=provider)

        assert "prompt.ideation" in result.step_outputs
        assert "prompt.checkpoints_from_stage" in result.step_outputs
        assert result.step_outputs["prompt.ideation"] == {"features": ["auth", "crud"]}

    def test_pipeline_orchestration_propagates_step_error(
        self, tmp_path: Path
    ) -> None:
        """A failing step raises PipelineStepError and stops the pipeline."""
        bad_responses = dict(_FULL_PIPELINE_RESPONSES)
        bad_responses["prompt.architecture"] = "not valid json"
        provider = _MappingProvider(bad_responses)
        config = _make_config()

        with pytest.raises(PipelineStepError) as exc_info:
            run_plan_pipeline(config, tmp_path, provider=provider)

        assert exc_info.value.step_name == "architecture"


# ---------------------------------------------------------------------------
# plan_writer — render_plan_md tests
# ---------------------------------------------------------------------------

from plan_pipeline import render_plan_md  # noqa: E402


def _make_result(
    stages: list[dict[str, Any]] | None = None,
    checkpoints: list[dict[str, Any]] | None = None,
) -> PipelineResult:
    return PipelineResult(
        run_id="test",
        stages=stages or [],
        checkpoints=checkpoints or [],
    )


class TestRenderPlanMdWriter:
    def test_plan_writer_renders_plan_header(self) -> None:
        """Rendered PLAN.md starts with '# PLAN'."""
        result = _make_result(
            stages=[{"id": "1", "name": "MVP", "objective": "Build it"}],
            checkpoints=[{
                "id": "1.0", "stage_id": "1", "title": "Init",
                "objective": "Set up", "deliverables": ["Install deps"],
                "acceptance": ["Tests pass"], "demo_commands": ["echo hi"],
            }],
        )
        plan_text, _ = render_plan_md(result)
        assert plan_text.startswith("# PLAN")

    def test_plan_writer_includes_stage_heading(self) -> None:
        """Stage heading appears as '## Stage N — Name'."""
        result = _make_result(
            stages=[{"id": "1", "name": "Bootstrap", "objective": "Start"}],
            checkpoints=[{"id": "1.0", "stage_id": "1", "title": "T"}],
        )
        plan_text, _ = render_plan_md(result)
        assert "## Stage 1 — Bootstrap" in plan_text

    def test_plan_writer_includes_checkpoint_heading(self) -> None:
        """Checkpoint heading appears as '### N.M — Title'."""
        result = _make_result(
            stages=[{"id": "1", "name": "S", "objective": ""}],
            checkpoints=[{"id": "1.0", "stage_id": "1", "title": "Init project"}],
        )
        plan_text, _ = render_plan_md(result)
        assert "### 1.0 — Init project" in plan_text

    def test_plan_writer_includes_required_checkpoint_fields(self) -> None:
        """Rendered checkpoint includes Objective, Deliverables, Acceptance, Demo commands, Evidence."""
        result = _make_result(
            stages=[{"id": "1", "name": "S", "objective": ""}],
            checkpoints=[{"id": "1.0", "stage_id": "1", "title": "T"}],
        )
        plan_text, _ = render_plan_md(result)
        for field in ("Objective", "Deliverables", "Acceptance", "Demo commands", "Evidence"):
            assert field in plan_text, f"Missing field: {field}"

    def test_plan_writer_no_warnings_within_budget(self) -> None:
        """Checkpoints within complexity budget produce no warnings."""
        result = _make_result(
            stages=[{"id": "1", "name": "S", "objective": ""}],
            checkpoints=[{
                "id": "1.0", "stage_id": "1", "title": "T",
                "deliverables": ["a", "b"],  # <=5
                "acceptance": ["x"],          # <=6
                "demo_commands": ["y"],        # <=4
            }],
        )
        _, warnings = render_plan_md(result)
        assert warnings == []

    def test_plan_writer_over_budget_deliverables_emits_warning(self) -> None:
        """Over-budget Deliverables list emits a warning but renders without error."""
        result = _make_result(
            stages=[{"id": "1", "name": "S", "objective": ""}],
            checkpoints=[{
                "id": "1.0", "stage_id": "1", "title": "T",
                "deliverables": ["a", "b", "c", "d", "e", "f"],  # >5
            }],
        )
        plan_text, warnings = render_plan_md(result)
        assert any("Deliverables" in w and "1.0" in w for w in warnings)
        # Rendering still succeeded
        assert "### 1.0" in plan_text

    def test_plan_writer_empty_result_renders_header_only(self) -> None:
        """Empty PipelineResult renders without error (header only)."""
        plan_text, warnings = render_plan_md(_make_result())
        assert plan_text.startswith("# PLAN")
        assert warnings == []

    def test_plan_writer_generated_plan_passes_agentctl_validate(
        self, tmp_path: Path
    ) -> None:
        """Rendered PLAN.md (written to disk) passes agentctl validate."""
        import subprocess

        result = _make_result(
            stages=[{"id": "1", "name": "Alpha", "objective": "Build alpha"}],
            checkpoints=[{
                "id": "1.0", "stage_id": "1", "title": "Setup",
                "objective": "Initialize project",
                "deliverables": ["Create repo", "Install deps"],
                "acceptance": ["Tests pass"],
                "demo_commands": ["echo done"],
            }],
        )
        plan_text, _ = render_plan_md(result)

        # Write PLAN.md + matching STATE.md to tmp_path
        vibe = tmp_path / ".vibe"
        vibe.mkdir()
        (vibe / "PLAN.md").write_text(plan_text, encoding="utf-8")
        (vibe / "STATE.md").write_text(
            "# STATE\n\n"
            "## Session read order\n\n"
            "1) `AGENTS.md`\n"
            "2) `.vibe/STATE.md` (this file)\n"
            "3) `.vibe/PLAN.md`\n\n"
            "## Current focus\n\n"
            "- Stage: 1\n"
            "- Checkpoint: 1.0\n"
            "- Status: NOT_STARTED\n\n"
            "## Objective (current checkpoint)\n\nInitialize project.\n\n"
            "## Deliverables (current checkpoint)\n\n- Create repo\n\n"
            "## Acceptance (current checkpoint)\n\n- Tests pass\n\n"
            "## Work log (current session)\n\n- 2026-02-19: test\n\n"
            "## Evidence\n\n(None)\n\n"
            "## Active issues\n\n- None.\n\n"
            "## Decisions\n\n- None.\n",
            encoding="utf-8",
        )

        # Run agentctl validate
        agentctl = Path(__file__).parent.parent.parent / "tools" / "agentctl.py"
        proc = subprocess.run(
            [sys.executable, str(agentctl), "--repo-root", str(tmp_path), "validate"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"validate failed:\n{proc.stdout}\n{proc.stderr}"


# ---------------------------------------------------------------------------
# Integration tests: config validation and overwrite guard (checkpoint 23.4)
# ---------------------------------------------------------------------------

from plan_pipeline import PipelineConfigError, resolve_config  # noqa: E402


class TestConfigValidation:
    def test_config_missing_problem_statement_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PipelineConfigError, match="problem.statement"):
            resolve_config(tmp_path)

    def test_config_missing_provider_raises_when_not_dry_run(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(PipelineConfigError, match="provider"):
            resolve_config(tmp_path, problem_statement="build a thing", dry_run=False)

    def test_config_provider_not_required_in_dry_run(self, tmp_path: Path) -> None:
        """dry_run=True succeeds even without a provider."""
        config = resolve_config(
            tmp_path, problem_statement="build a thing", dry_run=True
        )
        assert config.dry_run is True
        assert config.provider == ""

    def test_config_output_conflict_raises_without_overwrite(
        self, tmp_path: Path
    ) -> None:
        """Existing output file without --overwrite raises PipelineConfigError."""
        existing = tmp_path / "PLAN.md"
        existing.write_text("existing", encoding="utf-8")
        with pytest.raises(PipelineConfigError, match="already exists"):
            resolve_config(
                tmp_path,
                problem_statement="build",
                provider="anthropic",
                output_path=str(existing),
            )

    def test_config_overwrite_flag_bypasses_conflict(self, tmp_path: Path) -> None:
        """--overwrite allows writing to an existing output file."""
        existing = tmp_path / "PLAN.md"
        existing.write_text("existing", encoding="utf-8")
        config = resolve_config(
            tmp_path,
            problem_statement="build",
            provider="anthropic",
            output_path=str(existing),
            overwrite=True,
        )
        assert config.overwrite is True

    def test_config_repo_local_overrides_global(self, tmp_path: Path) -> None:
        """Repo-local config overrides global config for provider."""
        global_dir = tmp_path / "global_home"
        global_dir.mkdir()
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        vibe_dir = repo_dir / ".vibe"
        vibe_dir.mkdir()

        import json as _json
        (global_dir / ".vibe").mkdir()
        (global_dir / ".vibe" / "plan_pipeline.json").write_text(
            _json.dumps({"provider": "global_provider", "problem_statement": "p"}),
            encoding="utf-8",
        )
        (vibe_dir / "plan_pipeline.json").write_text(
            _json.dumps({"provider": "repo_provider"}),
            encoding="utf-8",
        )
        # Patch home to use our fake global dir
        import unittest.mock as mock
        with mock.patch("pathlib.Path.home", return_value=global_dir):
            config = resolve_config(repo_dir, dry_run=True)
        assert config.provider == "repo_provider"


class TestDocsExist:
    def test_plan_authoring_docs_exist(self) -> None:
        """docs/plan_authoring.md must exist and be non-empty."""
        docs_path = Path(__file__).parent.parent.parent / "docs" / "plan_authoring.md"
        assert docs_path.exists(), "docs/plan_authoring.md is missing"
        assert docs_path.stat().st_size > 100, "docs/plan_authoring.md is too small"
