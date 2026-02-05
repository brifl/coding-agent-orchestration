#!/usr/bin/env python3
"""
vibe_mark_done.py

Deterministically update .vibe/STATE.md status after a review decision.

Usage:
  python vibe_mark_done.py --repo-root . --pass
  python vibe_mark_done.py --repo-root . --fail
Optional:
  --blocked   (with --fail) sets BLOCKED instead of IN_PROGRESS
  --note "..." appends a short work-log line
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from datetime import date


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _set_status(text: str, new_status: str) -> tuple[str, bool]:
    # Replace the first "- Status: XYZ" under "## Current focus"
    pat = re.compile(r"(?im)^(\s*-\s*Status\s*:\s*)([A-Z_]+)(\b.*)$")
    m = pat.search(text)
    if not m:
        return (text, False)
    updated = text[:m.start(2)] + new_status + text[m.end(2):]
    return (updated, True)


def _append_work_log(text: str, line: str) -> str:
    marker = "## Work log (current session)"
    idx = text.find(marker)
    if idx == -1:
        return text + "\n\n## Work log (current session)\n- " + line + "\n"
    # insert after marker line
    lines = text.splitlines()
    out = []
    inserted = False
    for i, ln in enumerate(lines):
        out.append(ln)
        if not inserted and ln.strip() == marker:
            out.append(f"- {line}")
            inserted = True
    return "\n".join(out) + ("\n" if not text.endswith("\n") else "")


def main() -> int:
    ap = argparse.ArgumentParser(prog="vibe_mark_done.py")
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pass", dest="passed", action="store_true", help="Mark review PASS => DONE")
    g.add_argument("--fail", dest="failed", action="store_true", help="Mark review FAIL => IN_PROGRESS (or BLOCKED)")
    ap.add_argument("--blocked", action="store_true", help="With --fail, set status to BLOCKED")
    ap.add_argument("--note", default="", help="Optional work-log note to append")
    args = ap.parse_args()

    repo = Path(args.repo_root).expanduser().resolve()
    state_path = repo / ".vibe" / "STATE.md"
    if not state_path.exists():
        print(f"ERROR: missing {state_path}", file=sys.stderr)
        return 2

    text = _read(state_path)

    if args.passed:
        new_status = "DONE"
        default_note = f"{date.today().isoformat()}: Review PASS → status set to DONE"
    else:
        new_status = "BLOCKED" if args.blocked else "IN_PROGRESS"
        default_note = f"{date.today().isoformat()}: Review FAIL → status set to {new_status}"

    text2, ok = _set_status(text, new_status)
    if not ok:
        print("ERROR: could not find a '- Status:' line to update in .vibe/STATE.md", file=sys.stderr)
        return 2

    note = args.note.strip() or default_note
    text3 = _append_work_log(text2, note)

    _write(state_path, text3)
    print(f"Updated {state_path}: Status -> {new_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
