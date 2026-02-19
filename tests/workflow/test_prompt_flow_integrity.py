"""Integrity checks for prompt-flow wiring."""
from __future__ import annotations

import re
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from agentctl import (  # type: ignore
    _collect_workflow_prompt_refs,
    _load_prompt_catalog_index,
    _role_for_prompt_id,
    validate,
)


CORE_PROMPT_IDS = [
    "prompt.stage_design",
    "prompt.checkpoint_implementation",
    "prompt.checkpoint_review",
    "prompt.issues_triage",
    "prompt.consolidation",
    "prompt.context_capture",
    "prompt.process_improvements",
    "prompt.advance_checkpoint",
]


def _write_prompt_catalog(repo_root: Path) -> None:
    prompts_dir = repo_root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    sections = []
    for prompt_id in CORE_PROMPT_IDS:
        sections.append(
            "\n".join(
                [
                    f"## {prompt_id} - {prompt_id}",
                    "```md",
                    prompt_id,
                    "```",
                ]
            )
        )
    (prompts_dir / "template_prompts.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def test_validate_strict_fails_for_unknown_workflow_prompt(
    temp_repo: Path, vibe_state: Path, vibe_plan: Path
) -> None:
    _ = (vibe_state, vibe_plan)
    _write_prompt_catalog(temp_repo)

    workflows_dir = temp_repo / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / "broken.yaml").write_text(
        """name: broken
description: bad workflow
triggers:
  - type: manual
steps:
  - prompt_id: prompt.refactor_checkpoint
""",
        encoding="utf-8",
    )

    result = validate(temp_repo, strict=True)
    assert result.ok is False
    assert any(
        "broken.yaml: unknown prompt id 'prompt.refactor_checkpoint'" in message
        for message in result.errors
    )


def test_bootstrap_and_docs_use_issues_triage_role_name() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    targets = [
        repo_root / "prompts" / "init" / "codex_bootstrap.md",
        repo_root / "prompts" / "init" / "claude_bootstrap.md",
        repo_root / "prompts" / "init" / "gemini_bootstrap.md",
        repo_root / "prompts" / "init" / "copilot_bootstrap.md",
        repo_root / "prompts" / "init" / "generic_bootstrap.md",
        repo_root / "docs" / "concepts.md",
    ]

    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert " / triage / " not in text
        assert "issues_triage" in text


def test_repo_workflow_prompt_ids_exist_and_are_mapped() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    catalog_index, _, catalog_error = _load_prompt_catalog_index(repo_root)
    assert catalog_error is None

    refs, warnings = _collect_workflow_prompt_refs(repo_root)
    assert not warnings

    missing = [f"{workflow}:{prompt_id}" for workflow, prompt_id in refs if prompt_id not in catalog_index]
    unmapped = [f"{workflow}:{prompt_id}" for workflow, prompt_id in refs if _role_for_prompt_id(prompt_id) is None]
    assert not missing
    assert not unmapped


def test_skill_prompt_catalog_is_synced_with_repo_catalog() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    canonical = repo_root / "prompts" / "template_prompts.md"
    skill_copy = repo_root / ".codex" / "skills" / "vibe-prompts" / "resources" / "template_prompts.md"

    assert canonical.exists()
    assert skill_copy.exists()
    assert canonical.read_text(encoding="utf-8") == skill_copy.read_text(encoding="utf-8")


def test_issue_schema_language_uses_impact() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    targets = [
        repo_root / "AGENTS.md",
        repo_root / "templates" / "repo_root" / "AGENTS.md",
        repo_root / "README.md",
        repo_root / "prompts" / "template_prompts.md",
        repo_root / "templates" / "vibe_folder" / "STATE.md",
    ]

    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "Severity:" not in text
        # Allow "Severity rubric" / "Severity analysis" (doc references) but forbid
        # impact-label usage like "Severity MAJOR" or "Severity HIGH".
        assert not re.search(r"Severity [A-Z]", text), (
            f"Use 'impact' not 'severity' for issue labels in {path.name}"
        )
