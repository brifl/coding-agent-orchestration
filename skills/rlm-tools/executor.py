#!/usr/bin/env python3
"""RLM executor with bounded iteration, subcall caching, and resumable state."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_RLM_DIR = REPO_ROOT / "tools" / "rlm"
if str(TOOLS_RLM_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_RLM_DIR))

from context_bundle import _build_bundle, _read_task  # type: ignore
from runtime import RLMRuntime, RuntimeErrorState  # type: ignore

EXECUTOR_STATE_FILE = "executor_state.json"
RUNTIME_STATE_FILE = "state.json"
CACHE_MODES = {"readwrite", "readonly", "off"}
SUPPORTED_MODES = {"baseline", "subcalls"}
DEFAULT_RETRY_ATTEMPTS = 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=True)


def _resolve_path(value: str, repo_root: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (repo_root / path)


def _normalize_mode(task: dict[str, Any]) -> str:
    mode = str(task.get("mode", "")).strip().lower()
    if mode not in SUPPORTED_MODES:
        allowed = ", ".join(sorted(SUPPORTED_MODES))
        raise RuntimeError(f"Task mode must be one of: {allowed}.")
    return mode


def _program_key(task: dict[str, Any], mode: str) -> str:
    if mode == "subcalls" and isinstance(task.get("subcalls_program"), list):
        return "subcalls_program"
    return "baseline_program"


def _validate_program(task: dict[str, Any], mode: str) -> list[str]:
    key = _program_key(task, mode)
    program = task.get(key)
    if not isinstance(program, list) or not program:
        raise RuntimeError(
            f"Task must define a non-empty '{key}' list for executor mode '{mode}'."
        )
    normalized: list[str] = []
    for idx, item in enumerate(program):
        if not isinstance(item, str) or not item.strip():
            raise RuntimeError(f"{key}[{idx}] must be a non-empty string.")
        normalized.append(item)
    return normalized


def _normalize_cache_mode(raw: str | None, *, mode: str) -> str:
    value = str(raw or "").strip().lower()
    if mode == "subcalls":
        if value not in CACHE_MODES:
            allowed = "|".join(sorted(CACHE_MODES))
            raise RuntimeError(
                f"Subcall mode requires explicit --cache {{{allowed}}}."
            )
        return value
    if not value:
        return "off"
    if value not in CACHE_MODES:
        allowed = "|".join(sorted(CACHE_MODES))
        raise RuntimeError(f"Cache mode must be one of: {allowed}.")
    return value


def _cache_path_for_task(task_id: str, repo_root: Path) -> Path:
    return repo_root / ".vibe" / "rlm" / "cache" / f"{task_id}.jsonl"


def _load_cache_index(path: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return index
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                continue
            request_hash = str(payload.get("request_hash", "")).strip()
            if not request_hash:
                continue
            index.setdefault(request_hash, payload)
    return index


def _append_cache_entry(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _normalize_provider_name(value: Any) -> str:
    return str(value).strip().lower()


def _normalize_provider_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise RuntimeError(f"{field} must be an array of provider names.")
    normalized: list[str] = []
    for idx, item in enumerate(value):
        name = _normalize_provider_name(item)
        if not name:
            raise RuntimeError(f"{field}[{idx}] must be a non-empty provider name.")
        if name not in normalized:
            normalized.append(name)
    return normalized


def _provider_policy_details(provider_policy: dict[str, Any]) -> dict[str, Any]:
    primary = _normalize_provider_name(provider_policy.get("primary", ""))
    allowed = _normalize_provider_list(
        provider_policy.get("allowed"),
        "provider_policy.allowed",
    )
    fallback = _normalize_provider_list(
        provider_policy.get("fallback", []),
        "provider_policy.fallback",
    )

    if not primary:
        raise RuntimeError("provider_policy.primary must be a non-empty provider name.")
    if primary not in allowed:
        raise RuntimeError("provider_policy.primary must be listed in provider_policy.allowed.")
    invalid_fallback = [name for name in fallback if name not in allowed]
    if invalid_fallback:
        raise RuntimeError(
            "provider_policy.fallback entries must be listed in provider_policy.allowed: "
            + ", ".join(invalid_fallback)
        )

    candidate_order: list[str] = [primary]
    for name in fallback:
        if name not in candidate_order:
            candidate_order.append(name)
    for name in allowed:
        if name not in candidate_order:
            candidate_order.append(name)

    return {
        "allowed": allowed,
        "candidate_order": candidate_order,
        "fallback": fallback,
        "primary": primary,
    }


def _mock_provider_response(provider: str, prompt: str) -> str:
    request_material = {
        "prompt": prompt,
        "provider": provider,
    }
    digest = _sha256_text(_stable_json(request_material))
    return f"{provider}:{digest[:24]}"


def _query_with_deterministic_retry(provider: str, prompt: str) -> tuple[str, int]:
    normalized_prompt = str(prompt)
    fail_provider = ""
    if normalized_prompt.startswith("FAIL_PROVIDER:"):
        parts = normalized_prompt.split(":", 2)
        if len(parts) == 3:
            fail_provider = parts[1].strip().lower()
            normalized_prompt = parts[2]

    failures: list[str] = []
    for attempt in range(1, DEFAULT_RETRY_ATTEMPTS + 1):
        try:
            if fail_provider and provider == fail_provider:
                raise RuntimeError(f"simulated deterministic failure for provider '{provider}'")

            # Deterministic transient failure hook for testing retry behavior.
            if normalized_prompt.startswith("TRANSIENT_FAIL_ONCE:") and attempt == 1:
                raise RuntimeError("simulated transient provider failure")

            response_prompt = normalized_prompt
            if normalized_prompt.startswith("TRANSIENT_FAIL_ONCE:"):
                response_prompt = normalized_prompt.split(":", 1)[1]
            return _mock_provider_response(provider, response_prompt), attempt
        except RuntimeError as exc:
            failures.append(f"attempt {attempt}: {exc}")

    raise RuntimeErrorState(
        "Subcall failed after deterministic retries: " + "; ".join(failures)
    )


def _build_llm_query_handler(
    task: dict[str, Any],
    state: dict[str, Any],
    trace_path: Path,
    repo_root: Path,
    runtime: RLMRuntime,
) -> Callable[..., dict[str, Any]]:
    provider_policy = task.get("provider_policy")
    if not isinstance(provider_policy, dict):
        raise RuntimeError("Task provider_policy must be an object.")
    policy = _provider_policy_details(provider_policy)
    allowed_providers = set(policy["allowed"])
    provider_order = list(policy["candidate_order"])
    cache_mode = str(state.get("cache_mode", "off")).strip().lower()
    if cache_mode not in CACHE_MODES:
        raise RuntimeError(f"Invalid cache mode '{cache_mode}'.")

    cache_path = _resolve_path(str(state.get("cache_path", "")), repo_root)
    cache_index = _load_cache_index(cache_path) if cache_mode in {"readwrite", "readonly"} else {}

    iteration_subcalls = 0
    iteration_number = runtime.iteration + 1

    def llm_query(prompt: Any, provider: str | None = None) -> dict[str, Any]:
        nonlocal iteration_subcalls

        prompt_text = str(prompt)
        requested_provider = _normalize_provider_name(provider) if provider is not None else ""
        if requested_provider:
            if requested_provider not in allowed_providers:
                allowed_raw = ", ".join(policy["allowed"])
                raise RuntimeErrorState(
                    f"Requested provider '{requested_provider}' is not allowed; allowed=[{allowed_raw}]"
                )
            provider_candidates = [requested_provider]
        else:
            provider_candidates = list(provider_order)

        max_subcalls_per_iter = int(state.get("max_subcalls_per_iter", 0))
        max_subcalls_total = int(state.get("max_subcalls_total", 0))
        subcalls_total = int(state.get("subcalls_total", 0))

        if iteration_subcalls >= max_subcalls_per_iter:
            raise RuntimeErrorState(
                "Subcall budget exceeded for iteration "
                f"{iteration_number}: max_subcalls_per_iter={max_subcalls_per_iter}."
            )

        if subcalls_total >= max_subcalls_total:
            raise RuntimeErrorState(
                "Subcall budget exceeded for run: "
                f"max_subcalls_total={max_subcalls_total}."
            )

        request_payload: dict[str, Any] = {}
        request_hash = ""
        provider_name = ""
        response_hash = ""
        response_text = ""
        cache_status = "miss"
        attempts = 0

        for candidate in provider_candidates:
            candidate_payload = {
                "prompt": prompt_text,
                "provider": candidate,
            }
            candidate_hash = _sha256_text(_stable_json(candidate_payload))
            cached = cache_index.get(candidate_hash)
            if cached is None:
                continue
            provider_name = candidate
            request_payload = candidate_payload
            request_hash = candidate_hash
            response_text = str(cached.get("response_text", ""))
            response_hash = str(cached.get("response_hash", "")) or _sha256_text(response_text)
            cache_status = "hit"
            break

        if cache_status != "hit" and cache_mode == "readonly":
            raise RuntimeErrorState(
                "Readonly cache miss for provider candidates "
                f"{provider_candidates} and prompt hash seed "
                f"{_sha256_text(prompt_text)} in {cache_path}"
            )

        if cache_status != "hit":
            provider_failures: list[str] = []
            for candidate in provider_candidates:
                candidate_payload = {
                    "prompt": prompt_text,
                    "provider": candidate,
                }
                candidate_hash = _sha256_text(_stable_json(candidate_payload))
                try:
                    response_text, attempts = _query_with_deterministic_retry(candidate, prompt_text)
                    provider_name = candidate
                    request_payload = candidate_payload
                    request_hash = candidate_hash
                    break
                except RuntimeErrorState as exc:
                    provider_failures.append(f"{candidate}: {exc}")
                    continue

            if not provider_name:
                raise RuntimeErrorState(
                    "All provider candidates failed in deterministic order: "
                    + "; ".join(provider_failures)
                )

            response_hash = _sha256_text(response_text)
            if cache_mode == "readwrite":
                cache_entry = {
                    "cached_at": _utc_now(),
                    "provider": provider_name,
                    "request_hash": request_hash,
                    "request_payload": request_payload,
                    "response_hash": response_hash,
                    "response_text": response_text,
                }
                _append_cache_entry(cache_path, cache_entry)
                cache_index[request_hash] = cache_entry

        iteration_subcalls += 1
        state["subcalls_total"] = subcalls_total + 1
        response_hashes = state.get("response_hashes")
        if not isinstance(response_hashes, list):
            response_hashes = []
            state["response_hashes"] = response_hashes
        response_hashes.append(response_hash)

        _append_trace(
            trace_path,
            {
                "attempts": attempts,
                "cache_mode": cache_mode,
                "cache_status": cache_status,
                "event": "subcall",
                "iteration": iteration_number,
                "provider": provider_name,
                "provider_candidates": provider_candidates,
                "provider_requested": requested_provider or None,
                "recorded_at": _utc_now(),
                "request_hash": request_hash,
                "response_hash": response_hash,
                "subcalls_total": state.get("subcalls_total"),
            },
        )

        return {
            "attempts": attempts,
            "cache": cache_status,
            "provider": provider_name,
            "provider_candidates": provider_candidates,
            "request_hash": request_hash,
            "response_hash": response_hash,
            "text": response_text,
        }

    return llm_query


def _load_task(task_path: Path) -> dict[str, Any]:
    task = _read_task(task_path)
    if task is None:
        raise RuntimeError("Task validation failed.")
    mode = _normalize_mode(task)
    _validate_program(task, mode)
    return task


def _bundle_dir_for_task(task: dict[str, Any], repo_root: Path) -> Path:
    output_root = repo_root / ".vibe" / "rlm" / "bundles"
    _build_bundle(task, repo_root, output_root)
    task_id = str(task.get("task_id"))
    return output_root / task_id


def _default_run_dir(task: dict[str, Any], repo_root: Path) -> Path:
    task_id = str(task.get("task_id"))
    return repo_root / ".vibe" / "rlm" / "runs" / task_id


def _state_path(run_dir: Path) -> Path:
    return run_dir / EXECUTOR_STATE_FILE


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_executor_state(run_dir: Path) -> dict[str, Any]:
    path = _state_path(run_dir)
    if not path.exists():
        raise RuntimeError(f"Missing executor state file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Executor state must be an object: {path}")
    return payload


def _save_executor_state(run_dir: Path, state: dict[str, Any]) -> None:
    _write_json(_state_path(run_dir), state)


def _safe_remove_file(path: Path) -> None:
    try:
        if path.exists() and path.is_file():
            path.unlink()
    except OSError:
        # Best effort cleanup; stale files should not hard-fail run initialization.
        return


def _prepare_new_run_artifacts(
    task: dict[str, Any],
    run_dir: Path,
    trace_path: Path,
    repo_root: Path,
) -> None:
    _safe_remove_file(run_dir / RUNTIME_STATE_FILE)
    _safe_remove_file(trace_path)

    outputs = task.get("outputs")
    if not isinstance(outputs, dict):
        return

    final_path_raw = outputs.get("final_path")
    if isinstance(final_path_raw, str) and final_path_raw.strip():
        _safe_remove_file(_resolve_path(final_path_raw, repo_root))

    artifact_paths = outputs.get("artifact_paths")
    if isinstance(artifact_paths, list):
        for raw in artifact_paths:
            if isinstance(raw, str) and raw.strip():
                _safe_remove_file(_resolve_path(raw, repo_root))


def _append_trace(trace_path: Path, payload: dict[str, Any]) -> None:
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _finalize_artifacts(task: dict[str, Any], final_payload: Any, repo_root: Path) -> str:
    outputs = task.get("outputs")
    if not isinstance(outputs, dict):
        raise RuntimeError("Task outputs must be an object.")

    final_path_raw = outputs.get("final_path")
    if not isinstance(final_path_raw, str) or not final_path_raw.strip():
        raise RuntimeError("Task outputs.final_path must be a non-empty string.")

    final_path = _resolve_path(final_path_raw, repo_root)
    final_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(final_payload, (dict, list)):
        text = json.dumps(final_payload, indent=2, sort_keys=True)
    else:
        text = str(final_payload)
    final_path.write_text(text + "\n", encoding="utf-8")

    return str(final_path)


def _init_executor_state(
    task: dict[str, Any],
    task_path: Path,
    bundle_dir: Path,
    run_dir: Path,
    trace_path: Path,
    repo_root: Path,
    cache_mode: str,
) -> dict[str, Any]:
    limits = task.get("limits")
    assert isinstance(limits, dict)

    mode = _normalize_mode(task)
    normalized_cache_mode = _normalize_cache_mode(cache_mode, mode=mode)
    task_id = str(task["task_id"])

    state = {
        "bundle_dir": str(bundle_dir),
        "cache_mode": normalized_cache_mode,
        "cache_path": str(_cache_path_for_task(task_id, repo_root)),
        "cursor": 0,
        "final_artifact": None,
        "max_root_iters": int(limits["max_root_iters"]),
        "max_stdout_chars": int(limits["max_stdout_chars"]),
        "mode": mode,
        "status": "RUNNING",
        "stop_reason": None,
        "task_id": task_id,
        "task_path": str(task_path),
        "task_sha256": _sha256_file(task_path),
        "trace_path": str(trace_path),
    }

    if mode == "subcalls":
        state["max_subcalls_per_iter"] = int(limits["max_subcalls_per_iter"])
        state["max_subcalls_total"] = int(limits["max_subcalls_total"])
        state["response_hashes"] = []
        state["subcalls_total"] = 0

    return state


def _validate_resume_state(
    state: dict[str, Any],
    run_dir: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], Path, Path]:
    task_path = Path(str(state.get("task_path", ""))).resolve()
    if not task_path.exists():
        raise RuntimeError(f"Task path in executor state no longer exists: {task_path}")

    recorded_sha = str(state.get("task_sha256", "")).strip()
    current_sha = _sha256_file(task_path)
    if recorded_sha != current_sha:
        raise RuntimeError(
            "Task content changed since executor state was created; resume would be ambiguous."
        )

    task = _load_task(task_path)
    mode = _normalize_mode(task)
    recorded_mode = str(state.get("mode", "")).strip().lower()
    if recorded_mode and recorded_mode != mode:
        raise RuntimeError(
            f"Executor state mode '{recorded_mode}' does not match task mode '{mode}'."
        )

    bundle_dir = Path(str(state.get("bundle_dir", ""))).resolve()
    if not bundle_dir.exists():
        bundle_dir = _bundle_dir_for_task(task, repo_root)

    trace_path = Path(str(state.get("trace_path", run_dir / "trace.jsonl"))).resolve()
    return task, bundle_dir, trace_path


def _record_step(
    runtime_result: dict[str, Any],
    code: str,
    cursor: int,
    trace_path: Path,
    *,
    subcalls_this_iter: int,
    subcalls_total: int,
) -> None:
    payload = {
        "code_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        "error": runtime_result.get("error"),
        "event": "iteration",
        "finalized": bool(runtime_result.get("finalized")),
        "iteration": int(runtime_result.get("iteration", 0)),
        "program_index": cursor,
        "recorded_at": _utc_now(),
        "stdout_chars": len(str(runtime_result.get("stdout", ""))),
        "stdout_truncated": bool(runtime_result.get("stdout_truncated")),
        "subcalls_this_iter": subcalls_this_iter,
        "subcalls_total": subcalls_total,
    }
    _append_trace(trace_path, payload)


def _record_stop(state: dict[str, Any], runtime: RLMRuntime, trace_path: Path) -> None:
    payload = {
        "event": "stop",
        "finalized": runtime.finalized,
        "iteration": runtime.iteration,
        "recorded_at": _utc_now(),
        "status": state.get("status"),
        "stop_reason": state.get("stop_reason"),
    }
    _append_trace(trace_path, payload)


def _step_once(
    task: dict[str, Any],
    state: dict[str, Any],
    runtime: RLMRuntime,
    trace_path: Path,
    repo_root: Path,
) -> bool:
    if state.get("status") != "RUNNING":
        return False

    max_root_iters = int(state.get("max_root_iters", 0))
    if runtime.iteration >= max_root_iters:
        state["status"] = "LIMIT_REACHED"
        state["stop_reason"] = "MAX_ROOT_ITERS"
        _record_stop(state, runtime, trace_path)
        return False

    mode = _normalize_mode(task)
    program = _validate_program(task, mode)
    cursor = int(state.get("cursor", 0))
    if cursor >= len(program):
        state["status"] = "LIMIT_REACHED"
        state["stop_reason"] = "PROGRAM_EXHAUSTED"
        _record_stop(state, runtime, trace_path)
        return False

    if mode == "subcalls":
        runtime.llm_query_handler = _build_llm_query_handler(task, state, trace_path, repo_root, runtime)
    else:
        runtime.llm_query_handler = None

    code = program[cursor]
    subcalls_before = int(state.get("subcalls_total", 0))
    result = runtime.step(code)
    subcalls_after = int(state.get("subcalls_total", 0))

    _record_step(
        result,
        code,
        cursor,
        trace_path,
        subcalls_this_iter=max(0, subcalls_after - subcalls_before),
        subcalls_total=subcalls_after,
    )

    state["cursor"] = cursor + 1

    if result.get("error"):
        state["status"] = "BLOCKED"
        state["stop_reason"] = "STEP_ERROR"
        _record_stop(state, runtime, trace_path)
        return False

    if bool(result.get("finalized")):
        state["status"] = "COMPLETED"
        state["stop_reason"] = "FINAL"
        state["final_artifact"] = _finalize_artifacts(task, result.get("final_payload"), repo_root)
        _record_stop(state, runtime, trace_path)
        return False

    if runtime.iteration >= max_root_iters:
        state["status"] = "LIMIT_REACHED"
        state["stop_reason"] = "MAX_ROOT_ITERS"
        _record_stop(state, runtime, trace_path)
        return False

    return True


def _summary(run_dir: Path, state: dict[str, Any], runtime: RLMRuntime) -> dict[str, Any]:
    payload = {
        "cache_mode": state.get("cache_mode"),
        "cache_path": state.get("cache_path"),
        "cursor": state.get("cursor"),
        "final_artifact": state.get("final_artifact"),
        "iteration": runtime.iteration,
        "mode": state.get("mode"),
        "run_dir": str(run_dir),
        "status": state.get("status"),
        "stop_reason": state.get("stop_reason"),
        "trace_path": state.get("trace_path"),
    }
    if state.get("mode") == "subcalls":
        payload["response_hashes"] = state.get("response_hashes", [])
        payload["subcalls_total"] = state.get("subcalls_total", 0)
    return payload


def _assert_cache_override_matches_state(requested: str | None, state: dict[str, Any]) -> None:
    if not requested:
        return
    requested_mode = str(requested).strip().lower()
    if requested_mode not in CACHE_MODES:
        allowed = "|".join(sorted(CACHE_MODES))
        raise RuntimeError(f"Cache mode must be one of: {allowed}.")
    state_mode = str(state.get("cache_mode", "")).strip().lower() or "off"
    if requested_mode != state_mode:
        raise RuntimeError(
            "Resume cache mode mismatch: "
            f"state cache mode is '{state_mode}', requested '{requested_mode}'."
        )


def cmd_run(args: argparse.Namespace) -> int:
    repo_root = REPO_ROOT
    task_path = _resolve_path(args.task, repo_root).resolve()
    task = _load_task(task_path)
    mode = _normalize_mode(task)

    requested_cache = _normalize_cache_mode(args.cache, mode=mode)

    run_dir = _resolve_path(args.run_dir, repo_root).resolve() if args.run_dir else _default_run_dir(task, repo_root)
    if args.fresh and run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = _bundle_dir_for_task(task, repo_root)
    trace_path = _resolve_path(str(task["trace"]["trace_path"]), repo_root)
    _prepare_new_run_artifacts(task, run_dir, trace_path, repo_root)

    state = _init_executor_state(task, task_path, bundle_dir, run_dir, trace_path, repo_root, requested_cache)
    _save_executor_state(run_dir, state)

    runtime = RLMRuntime(
        bundle_dir=bundle_dir,
        run_dir=run_dir,
        max_stdout_chars=int(state["max_stdout_chars"]),
    )

    while _step_once(task, state, runtime, trace_path, repo_root):
        _save_executor_state(run_dir, state)

    _save_executor_state(run_dir, state)
    print(json.dumps(_summary(run_dir, state, runtime), indent=2, sort_keys=True))
    return 0 if state.get("status") in {"COMPLETED", "LIMIT_REACHED"} else 1


def cmd_step(args: argparse.Namespace) -> int:
    repo_root = REPO_ROOT
    run_dir = _resolve_path(args.run_dir, repo_root).resolve()
    state = _load_executor_state(run_dir)
    _assert_cache_override_matches_state(args.cache, state)
    task, bundle_dir, trace_path = _validate_resume_state(state, run_dir, repo_root)

    runtime = RLMRuntime(
        bundle_dir=bundle_dir,
        run_dir=run_dir,
        max_stdout_chars=int(state["max_stdout_chars"]),
    )

    _step_once(task, state, runtime, trace_path, repo_root)
    _save_executor_state(run_dir, state)
    print(json.dumps(_summary(run_dir, state, runtime), indent=2, sort_keys=True))
    return 0 if state.get("status") in {"RUNNING", "COMPLETED", "LIMIT_REACHED"} else 1


def cmd_resume(args: argparse.Namespace) -> int:
    repo_root = REPO_ROOT
    run_dir = _resolve_path(args.run_dir, repo_root).resolve()
    state = _load_executor_state(run_dir)
    _assert_cache_override_matches_state(args.cache, state)
    task, bundle_dir, trace_path = _validate_resume_state(state, run_dir, repo_root)

    runtime = RLMRuntime(
        bundle_dir=bundle_dir,
        run_dir=run_dir,
        max_stdout_chars=int(state["max_stdout_chars"]),
    )

    while _step_once(task, state, runtime, trace_path, repo_root):
        _save_executor_state(run_dir, state)

    _save_executor_state(run_dir, state)
    print(json.dumps(_summary(run_dir, state, runtime), indent=2, sort_keys=True))
    return 0 if state.get("status") in {"COMPLETED", "LIMIT_REACHED"} else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RLM executor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_cmd = subparsers.add_parser("run", help="Create a run and execute until stop.")
    run_cmd.add_argument("--task", required=True, help="Task JSON path")
    run_cmd.add_argument("--run-dir", help="Override run directory")
    run_cmd.add_argument("--fresh", action="store_true", help="Delete existing run directory before start")
    run_cmd.add_argument(
        "--cache",
        choices=sorted(CACHE_MODES),
        help="Subcall cache mode. Required for mode=subcalls.",
    )
    run_cmd.set_defaults(func=cmd_run)

    step_cmd = subparsers.add_parser("step", help="Execute one iteration for an existing run.")
    step_cmd.add_argument("--run-dir", required=True, help="Existing run directory")
    step_cmd.add_argument(
        "--cache",
        choices=sorted(CACHE_MODES),
        help="Optional cache mode check for resume safety.",
    )
    step_cmd.set_defaults(func=cmd_step)

    resume_cmd = subparsers.add_parser("resume", help="Resume an existing run until stop.")
    resume_cmd.add_argument("--run-dir", required=True, help="Existing run directory")
    resume_cmd.add_argument(
        "--cache",
        choices=sorted(CACHE_MODES),
        help="Optional cache mode check for resume safety.",
    )
    resume_cmd.set_defaults(func=cmd_resume)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.func(args))
    except (RuntimeError, RuntimeErrorState, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
