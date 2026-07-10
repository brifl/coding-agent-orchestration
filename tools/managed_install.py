#!/usr/bin/env python3
"""Deterministic reconciliation for framework-managed skill bundles."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping


MANIFEST_FILENAME = ".vibe-install-manifest.json"
MANIFEST_SCHEMA_VERSION = 1
PRE_MANIFEST_RETIRED_SKILLS = frozenset({"vibe-one-loop"})
_SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ManagedInstallReport:
    managed_skills: tuple[str, ...]
    bundle_sha256: str
    changed_files: tuple[str, ...]
    repaired_files: tuple[str, ...]
    removed_extras: tuple[str, ...]
    retired_skills: tuple[str, ...]
    manifest_path: Path


@dataclass(frozen=True)
class _Manifest:
    managed_skills: tuple[str, ...]
    files: dict[str, str]
    bundle_sha256: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_skill_name(name: str) -> str:
    if not _SKILL_NAME_RE.fullmatch(name) or name in {".", ".."}:
        raise ValueError(f"Invalid managed skill name: {name!r}")
    return name


def _validate_relative_file(value: str, managed_skills: set[str]) -> PurePosixPath:
    rel = PurePosixPath(value)
    if rel.is_absolute() or len(rel.parts) < 2 or any(part in {"", ".", ".."} for part in rel.parts):
        raise ValueError(f"Invalid managed manifest path: {value!r}")
    if rel.parts[0] not in managed_skills:
        raise ValueError(f"Managed manifest path is outside declared skills: {value!r}")
    return rel


def _bundle_sha256(managed_skills: tuple[str, ...], files: Mapping[str, str]) -> str:
    canonical = json.dumps(
        {"managed_skills": list(managed_skills), "files": dict(sorted(files.items()))},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _manifest_bytes(manifest: _Manifest) -> bytes:
    payload = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "managed_skills": list(manifest.managed_skills),
        "files": dict(sorted(manifest.files.items())),
        "bundle_sha256": manifest.bundle_sha256,
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _load_manifest(path: Path) -> _Manifest | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid managed install manifest {path}: {exc}") from exc
    if payload.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"Unsupported managed install manifest schema in {path}.")
    raw_skills = payload.get("managed_skills")
    raw_files = payload.get("files")
    if not isinstance(raw_skills, list) or not all(isinstance(name, str) for name in raw_skills):
        raise ValueError(f"Invalid managed_skills in {path}.")
    managed_skills = tuple(sorted({_validate_skill_name(name) for name in raw_skills}))
    if list(managed_skills) != raw_skills:
        raise ValueError(f"managed_skills must be unique and sorted in {path}.")
    if not isinstance(raw_files, dict):
        raise ValueError(f"Invalid files map in {path}.")
    files: dict[str, str] = {}
    skill_set = set(managed_skills)
    for raw_path, raw_digest in raw_files.items():
        if not isinstance(raw_path, str) or not isinstance(raw_digest, str):
            raise ValueError(f"Invalid files entry in {path}.")
        rel = _validate_relative_file(raw_path, skill_set)
        if not _DIGEST_RE.fullmatch(raw_digest):
            raise ValueError(f"Invalid digest for {raw_path!r} in {path}.")
        files[rel.as_posix()] = raw_digest
    bundle_sha256 = str(payload.get("bundle_sha256", ""))
    if bundle_sha256 != _bundle_sha256(managed_skills, files):
        raise ValueError(f"Managed install manifest bundle digest mismatch in {path}.")
    return _Manifest(managed_skills, files, bundle_sha256)


def _collect_desired_sources(
    skill_sources: Mapping[str, Path],
    overlays: Mapping[str, Path],
) -> tuple[tuple[str, ...], dict[str, Path]]:
    managed_skills = tuple(sorted(_validate_skill_name(name) for name in skill_sources))
    if not managed_skills:
        raise ValueError("At least one managed skill is required.")
    desired: dict[str, Path] = {}
    for name in managed_skills:
        source_root = skill_sources[name]
        if not source_root.is_dir():
            raise FileNotFoundError(f"Managed skill source not found: {source_root}")
        for source in sorted(source_root.rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(source_root)
            if "__pycache__" in relative.parts or source.suffix in {".pyc", ".pyo"}:
                continue
            desired[(PurePosixPath(name) / PurePosixPath(*relative.parts)).as_posix()] = source
    skill_set = set(managed_skills)
    for raw_relative, source in overlays.items():
        relative = _validate_relative_file(raw_relative, skill_set).as_posix()
        if not source.is_file():
            raise FileNotFoundError(f"Managed overlay source not found: {source}")
        desired[relative] = source
    return managed_skills, dict(sorted(desired.items()))


def _current_files(skill_path: Path, skill_name: str) -> dict[str, Path]:
    if not skill_path.is_dir():
        return {}
    files: dict[str, Path] = {}
    for path in sorted(skill_path.rglob("*")):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(skill_path)
        files[(PurePosixPath(skill_name) / PurePosixPath(*relative.parts)).as_posix()] = path
    return files


def _extra_directories(
    skill_path: Path,
    skill_name: str,
    desired_files: set[str],
) -> list[str]:
    if not skill_path.is_dir():
        return []
    desired_directories: set[str] = set()
    for relative in desired_files:
        parts = PurePosixPath(relative).parts
        for index in range(2, len(parts)):
            desired_directories.add(PurePosixPath(*parts[:index]).as_posix())
    extras: list[str] = []
    for path in sorted(skill_path.rglob("*")):
        if not path.is_dir() or path.is_symlink():
            continue
        relative = path.relative_to(skill_path)
        manifest_relative = (
            PurePosixPath(skill_name) / PurePosixPath(*relative.parts)
        ).as_posix()
        if manifest_relative not in desired_directories:
            extras.append(f"{manifest_relative}/")
    return extras


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _write_manifest_atomic(path: Path, content: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    try:
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def reconcile_managed_skills(
    skills_root: Path,
    skill_sources: Mapping[str, Path],
    overlays: Mapping[str, Path],
) -> ManagedInstallReport:
    """Converge managed skill directories and write the ownership manifest last."""
    skills_root = skills_root.resolve()
    skills_root.mkdir(parents=True, exist_ok=True)
    manifest_path = skills_root / MANIFEST_FILENAME
    prior = _load_manifest(manifest_path)
    managed_skills, desired_sources = _collect_desired_sources(skill_sources, overlays)
    desired_hashes = {relative: _sha256(source) for relative, source in desired_sources.items()}
    bundle_sha256 = _bundle_sha256(managed_skills, desired_hashes)
    desired_manifest = _Manifest(managed_skills, desired_hashes, bundle_sha256)
    desired_manifest_bytes = _manifest_bytes(desired_manifest)

    current_by_skill = {
        name: _current_files(skills_root / name, name)
        for name in managed_skills
    }
    changed_files: list[str] = []
    repaired_files: list[str] = []
    removed_extras: list[str] = []
    changed_skills: set[str] = set()
    prior_files = prior.files if prior else {}
    for name in managed_skills:
        current_files = current_by_skill[name]
        desired_for_skill = {
            relative: digest
            for relative, digest in desired_hashes.items()
            if PurePosixPath(relative).parts[0] == name
        }
        extras = sorted(set(current_files) - set(desired_for_skill))
        extras.extend(
            _extra_directories(
                skills_root / name,
                name,
                set(desired_for_skill),
            )
        )
        extras = sorted(set(extras))
        removed_extras.extend(extras)
        if extras:
            changed_skills.add(name)
        for relative, desired_digest in desired_for_skill.items():
            current_path = current_files.get(relative)
            current_digest = _sha256(current_path) if current_path and current_path.is_file() else None
            if current_digest == desired_digest:
                continue
            changed_files.append(relative)
            changed_skills.add(name)
            prior_digest = prior_files.get(relative)
            if (prior_digest is not None and current_digest != prior_digest) or (
                prior is None and current_digest is not None
            ):
                repaired_files.append(relative)

    previous_skills = set(prior.managed_skills) if prior else set()
    retired_skills = sorted(
        name
        for name in (previous_skills - set(managed_skills)) | PRE_MANIFEST_RETIRED_SKILLS
        if (skills_root / name).exists() or (skills_root / name).is_symlink()
    )

    manifest_matches = manifest_path.exists() and manifest_path.read_bytes() == desired_manifest_bytes
    if not changed_skills and not retired_skills and manifest_matches:
        return ManagedInstallReport(
            managed_skills,
            bundle_sha256,
            tuple(),
            tuple(),
            tuple(),
            tuple(),
            manifest_path,
        )

    stage_root = Path(tempfile.mkdtemp(prefix=".vibe-install-stage-", dir=skills_root.parent))
    backup_root = Path(tempfile.mkdtemp(prefix=".vibe-install-backup-", dir=skills_root.parent))
    try:
        for relative, source in desired_sources.items():
            name = PurePosixPath(relative).parts[0]
            if name not in changed_skills:
                continue
            destination = stage_root.joinpath(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        staged_hashes = {
            relative: _sha256(stage_root.joinpath(*PurePosixPath(relative).parts))
            for relative in desired_hashes
            if PurePosixPath(relative).parts[0] in changed_skills
        }
        expected_staged = {
            relative: digest
            for relative, digest in desired_hashes.items()
            if PurePosixPath(relative).parts[0] in changed_skills
        }
        if staged_hashes != expected_staged:
            raise RuntimeError("Managed install staging digest validation failed.")

        affected = sorted(changed_skills | set(retired_skills))
        processed: list[str] = []
        try:
            for name in affected:
                destination = skills_root / name
                backup = backup_root / name
                if destination.exists() or destination.is_symlink():
                    destination.replace(backup)
                processed.append(name)
                staged = stage_root / name
                if staged.exists():
                    staged.replace(destination)
            _write_manifest_atomic(manifest_path, desired_manifest_bytes)
        except Exception:
            for name in reversed(processed):
                destination = skills_root / name
                backup = backup_root / name
                _remove_path(destination)
                if backup.exists() or backup.is_symlink():
                    backup.replace(destination)
            raise
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)
        shutil.rmtree(backup_root, ignore_errors=True)

    return ManagedInstallReport(
        managed_skills,
        bundle_sha256,
        tuple(sorted(changed_files)),
        tuple(sorted(repaired_files)),
        tuple(sorted(removed_extras)),
        tuple(retired_skills),
        manifest_path,
    )
