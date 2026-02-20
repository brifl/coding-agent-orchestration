#!/usr/bin/env python3
"""
clipper.py

Metadata-driven button UI for copying prompt bodies from skill resources.

- Uses tools/prompt_catalog.py parsing conventions.
- Buttons are keyed by stable IDs (e.g., prompt.onboarding).
- Button labels show human titles.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import List

from prompt_catalog import CatalogEntry, load_catalog  # type: ignore


def _repo_root_from_this_file() -> Path:
    # tools/clipper.py -> <repo_root>/tools/clipper.py
    return Path(__file__).resolve().parents[1]


def _default_catalog_path() -> Path:
    repo_root = _repo_root_from_this_file()
    return repo_root / ".codex" / "skills" / "vibe-prompts" / "resources" / "template_prompts.md"


class ClipperApp:
    def __init__(self, root: tk.Tk, catalog_path: Path) -> None:
        self.root = root
        self.catalog_path = catalog_path
        self.entries: List[CatalogEntry] = load_catalog(catalog_path)

        root.title(f"Vibe Clipper — {catalog_path.name}")

        # Layout
        outer = tk.Frame(root, padx=10, pady=10)
        outer.pack(fill=tk.BOTH, expand=True)

        # Buttons area (scrollable)
        canvas = tk.Canvas(outer, borderwidth=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.buttons_frame = tk.Frame(canvas)

        self.buttons_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.buttons_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Status line
        self.status = tk.StringVar(value=f"Loaded {len(self.entries)} prompts")
        status_lbl = tk.Label(root, textvariable=self.status, anchor="w", padx=10, pady=6)
        status_lbl.pack(fill=tk.X)

        self._build_buttons()

    def _copy_to_clipboard(self, text: str, label: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status.set(f"Copied: {label}")

    def _build_buttons(self) -> None:
        for e in self.entries:
            label = f"{e.key} — {e.title}"
            btn = tk.Button(
                self.buttons_frame,
                text=label,
                width=80,
                anchor="w",
                command=lambda body=e.body, lab=label: self._copy_to_clipboard(body, lab),
            )
            btn.pack(fill=tk.X, pady=2)


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(prog="clipper.py")
    p.add_argument(
        "--catalog",
        type=str,
        default=str(_default_catalog_path()),
        help="Path to template_prompts.md",
    )
    args = p.parse_args()
    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog not found: {catalog_path}")

    root = tk.Tk()
    ClipperApp(root, catalog_path)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
