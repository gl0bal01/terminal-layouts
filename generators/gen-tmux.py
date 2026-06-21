#!/usr/bin/env python3
"""gen-tmux.py — generate a tmuxp-compatible YAML layout from a manifest workflow.

Usage:
    python3 generators/gen-tmux.py <workflow_id> [> dist/tmux/<workflow_id>.yaml]

Strategy:
- A root `row` container with [leaf, column] maps to tmux `main-vertical`
  with `main-pane-width` set from the leaf's size. Side panes (the column's
  children) are stacked vertically on the right (tmux's default for
  main-vertical).
- Anything else falls back to `tiled` with leaves emitted in tree-walk order.
- Container panes are flattened; tmux does not support arbitrary nesting.
- Empty `command` emits the pane-title decoration pattern from the existing
  tmux-layouts repo (sets @mytitle + prints a hint line).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running without installation
sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402


def yaml_dq(s: str) -> str:
    """Double-quote a YAML string with minimal escaping."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def sh_sq(s: str) -> str:
    """Single-quote a string for safe shell insertion."""
    return "'" + s.replace("'", "'\\''") + "'"


def emit_decoration(pane: dict) -> str:
    """Emit the `tmux set @mytitle + printf` decoration for an empty pane."""
    name = common.pane_name(pane)
    desc = pane.get("description") or name
    return (
        f"tmux set -p -t \"$TMUX_PANE\" @mytitle {sh_sq(name)}; "
        f"printf '\\e[H\\e[2J\\e[2;36m▎ %s\\e[0m\\n\\n' {sh_sq(desc)}"
    )


def emit_pane_command(pane: dict) -> str:
    cmd = pane.get("command") or ""
    if not cmd:
        return emit_decoration(pane)
    # Non-empty command: set title, then run
    name = common.pane_name(pane)
    return f"tmux set -p -t \"$TMUX_PANE\" @mytitle {sh_sq(name)}; {cmd}"


def flatten_panes(panes: list) -> list:
    """Walk the pane tree and return a flat list of leaf panes in order."""
    out: list[dict] = []
    for p in panes:
        if common.pane_is_leaf(p):
            out.append(p)
        else:
            out.extend(flatten_panes(p.get("children", [])))
    return out


def detect_main_vertical(root_panes: list) -> tuple[dict, list] | None:
    """If root is a `row` with [leaf, column], return (main_leaf, side_leaves).

    Otherwise return None (caller falls back to tiled).
    """
    if len(root_panes) != 1:
        return None
    root = root_panes[0]
    if common.pane_is_leaf(root):
        return None
    if root.get("direction") != "row":
        return None
    children = root.get("children", [])
    if len(children) != 2:
        return None
    first, second = children
    if not common.pane_is_leaf(first):
        return None
    if common.pane_is_leaf(second):
        return None
    if second.get("direction") != "column":
        return None
    side_leaves = flatten_panes(second.get("children", []))
    return first, side_leaves


def emit_window(tab: dict, session_cwd: str | None) -> list[str]:
    lines: list[str] = []
    emoji = tab.get("emoji", "")
    name = tab.get("name", tab["id"])
    label = f"{emoji} {name}" if emoji else name
    lines.append(f"  - window_name: {yaml_dq(label)}")
    if tab.get("focus"):
        lines.append("    focus: true")
    tab_cwd = tab.get("cwd")
    if tab_cwd:
        lines.append(f"    start_directory: {yaml_dq(tab_cwd)}")

    panes = tab.get("panes", [])
    mv = detect_main_vertical(panes)
    if mv is not None:
        main_leaf, side_leaves = mv
        width = common.size_percent(main_leaf.get("size")) or 70
        lines.append("    layout: main-vertical")
        lines.append("    options:")
        lines.append(f'      main-pane-width: "{width}%"')
        lines.append("    panes:")
        # Main pane first
        focus_line = "      - focus: true" if main_leaf.get("focus") else "      -"
        lines.append(focus_line)
        lines.append("        shell_command:")
        lines.append(f"          - {emit_pane_command(main_leaf)}")
        for sp in side_leaves:
            lines.append("      - shell_command:")
            lines.append(f"          - {emit_pane_command(sp)}")
    else:
        leaves = flatten_panes(panes)
        lines.append("    layout: tiled")
        lines.append("    panes:")
        for leaf in leaves:
            focus_line = "      - focus: true" if leaf.get("focus") else "      -"
            lines.append(focus_line)
            lines.append("        shell_command:")
            lines.append(f"          - {emit_pane_command(leaf)}")
    return lines


def emit_tmux(wf: dict, defaults: dict) -> str:
    lines: list[str] = []
    lines.append(f"# dist/tmux/{wf['id']}.yaml")
    lines.append("# Auto-generated from manifest/workflows/%s.yaml — do not edit." % wf["id"])
    lines.append("# Launch: tmuxp load -y %s" % wf["id"])
    lines.append(f"session_name: {wf['id']}")
    cwd = common.resolve_cwd(wf, defaults)
    if cwd:
        lines.append(f"start_directory: {yaml_dq(cwd)}")
    show_sb = defaults.get("defaults", {}).get("show_statusbar", True)
    lines.append("options:")
    lines.append(f"  status: {'on' if show_sb else 'off'}")
    lines.append("windows:")
    for tab in wf.get("tabs", []):
        if tab.get("tmux_only", False) is False or tab.get("zellij_only", False):
            # emit if not zellij_only
            pass
        if tab.get("zellij_only", False):
            continue
        lines.extend(emit_window(tab, cwd))
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit("usage: gen-tmux.py <workflow_id>")
    wf_id = sys.argv[1]
    defaults = common.load_defaults()
    wf = common.load_workflow(wf_id)
    sys.stdout.write(emit_tmux(wf, defaults))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
