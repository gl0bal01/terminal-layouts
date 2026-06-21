#!/usr/bin/env python3
"""parity-check.py — verify a tmux YAML and zellij KDL match a manifest workflow.

Usage: parity-check.py <manifest.yaml> <dist/tmux/<wf>.yaml> <dist/zellij/<wf>.kdl>

Exits non-zero on any mismatch.
"""
from __future__ import annotations

import re
import sys

import yaml


def is_leaf(p: dict) -> bool:
    return "id" in p


def walk(panes: list, out: list) -> None:
    for p in panes:
        if is_leaf(p):
            out.append(p.get("name") or p["id"])
        else:
            walk(p.get("children", []), out)


def main() -> int:
    if len(sys.argv) != 4:
        sys.exit("usage: parity-check.py <manifest> <tmux.yaml> <zellij.kdl>")
    wf_path, tmux_path, zellij_path = sys.argv[1:4]

    wf = yaml.safe_load(open(wf_path))

    expected_tmux_tabs = [t for t in wf["tabs"] if not t.get("zellij_only", False)]
    expected_zellij_tabs = [t for t in wf["tabs"] if not t.get("tmux_only", False)]

    # ── tmux side ────────────────────────────────────────────────────────
    tmux_yaml = yaml.safe_load(open(tmux_path))
    tmux_windows = tmux_yaml.get("windows", [])
    if len(tmux_windows) != len(expected_tmux_tabs):
        sys.exit(
            f"tmux: expected {len(expected_tmux_tabs)} windows, got {len(tmux_windows)}"
        )
    for exp_tab, win in zip(expected_tmux_tabs, tmux_windows):
        win_name = win.get("window_name", "")
        # Strip emoji prefix from window_name (emoji + space + name)
        exp_name = exp_tab.get("name", exp_tab["id"])
        if not win_name.endswith(exp_name):
            sys.exit(f"tmux: window_name {win_name!r} does not end with {exp_name!r}")
        # Count panes
        exp_leaves: list[str] = []
        walk(exp_tab.get("panes", []), exp_leaves)
        win_panes = win.get("panes", [])
        if len(win_panes) != len(exp_leaves):
            sys.exit(
                f"tmux tab {exp_tab['id']}: expected {len(exp_leaves)} panes, "
                f"got {len(win_panes)}"
            )

    # ── zellij side ──────────────────────────────────────────────────────
    zellij_kdl = open(zellij_path).read()
    # Count top-level `tab name="..."` lines (inside `layout { ... }` but not nested)
    # We count lines starting with optional whitespace + `tab name=` at exactly 4 spaces.
    zellij_tab_lines = re.findall(r"^    tab name=", zellij_kdl, re.MULTILINE)
    if len(zellij_tab_lines) != len(expected_zellij_tabs):
        sys.exit(
            f"zellij: expected {len(expected_zellij_tabs)} tabs, "
            f"got {len(zellij_tab_lines)}"
        )

    # Verify each expected tab name appears in the KDL
    for exp_tab in expected_zellij_tabs:
        exp_name = exp_tab.get("name", exp_tab["id"])
        if f'tab name="' not in zellij_kdl:
            sys.exit("zellij: malformed KDL — no tab declarations found")
        # The tab name in KDL is "emoji name" or just "name"
        # Check that the name appears in some tab declaration
        pattern = rf'tab name="[^"]*{re.escape(exp_name)}"'
        if not re.search(pattern, zellij_kdl):
            sys.exit(f"zellij: tab name {exp_name!r} not found in KDL")

    print(
        f"  {wf['id']}: tmux={len(tmux_windows)} windows, "
        f"zellij={len(zellij_tab_lines)} tabs — OK"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
