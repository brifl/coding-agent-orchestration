# RLM agent entrypoints

The `rlm-tools` skill packages deterministic RLM tooling for supported agents.

## Entrypoints

Use the wrapper script from repo root:

- `python3 skills/rlm-tools/rlm.py validate <task.json>`
- `python3 skills/rlm-tools/rlm.py bundle --task <task.json> [--output-root .vibe/rlm/bundles]`
- `python3 skills/rlm-tools/rlm.py run --task <task.json> [--cache readwrite|readonly|off] [--fresh]`
- `python3 skills/rlm-tools/rlm.py step --run-dir <run_dir> [--cache readwrite|readonly|off]`
- `python3 skills/rlm-tools/rlm.py resume --run-dir <run_dir> [--cache readwrite|readonly|off]`
- `python3 skills/rlm-tools/rlm.py providers [--provider all|openai|anthropic|google|triton]`

## Notes

- Subcall tasks (`mode=subcalls`) require explicit `--cache` on `run`.
- `provider_policy` selection is deterministic: `primary`, then ordered `fallback`, then remaining `allowed`.
- Use `python3 tools/rlm/replay.py` to compare replay traces and final artifacts.
