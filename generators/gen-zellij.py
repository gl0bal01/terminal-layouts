#!/usr/bin/env python3
"""gen-zellij.py — generate a Zellij KDL layout from a manifest workflow.

Usage:
    python3 generators/gen-zellij.py <workflow_id> [> dist/zellij/<workflow_id>.kdl]

Zellij natively supports nested pane trees via split_direction:
- manifest `direction: row`     → zellij `split_direction="vertical"`   (panes left|right)
- manifest `direction: column`  → zellij `split_direction="horizontal"` (panes top|bottom)

(In Zellij, the divider line is perpendicular to the split direction name.)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

INDENT = "    "  # 4 spaces


def kdl_str(s: str) -> str:
    """Quote a KDL string literal."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def split_dir(direction: str) -> str:
    return "vertical" if direction == "row" else "horizontal"


def emit_leaf(pane: dict, depth: int) -> list[str]:
    pad = INDENT * depth
    name = common.pane_name(pane)
    parts: list[str] = [f'pane name={kdl_str(name)}']

    cmd = pane.get("command") or ""
    if cmd:
        # Split command into program + args (simple split; user can use args[] for control)
        import shlex
        try:
            tokens = shlex.split(cmd)
        except ValueError:
            tokens = [cmd]
        parts.append(f'command={kdl_str(tokens[0])}')
        if len(tokens) > 1:
            parts.append("close_on_exit=false")
            line = f"{pad}{' '.join(parts)} {{"
            lines = [line]
            args_line = f"{pad}{INDENT}args " + " ".join(kdl_str(t) for t in tokens[1:])
            lines.append(args_line)
            lines.append(f"{pad}}}")
            return lines
        parts.append("close_on_exit=false")
    if pane.get("focus"):
        parts.append("focus=true")
    size = pane.get("size")
    if size is not None:
        parts.append(f'size={kdl_str(common.normalize_size(size))}')
    return [f"{pad}{' '.join(parts)}"]


def emit_container(pane: dict, depth: int) -> list[str]:
    pad = INDENT * depth
    direction = pane.get("direction", "row")
    parts = [f'pane split_direction={kdl_str(split_dir(direction))}']
    size = pane.get("size")
    if size is not None:
        parts.append(f'size={kdl_str(common.normalize_size(size))}')
    if pane.get("focus"):
        parts.append("focus=true")
    lines = [f"{pad}{' '.join(parts)} {{"]
    for child in pane.get("children", []):
        if common.pane_is_leaf(child):
            lines.extend(emit_leaf(child, depth + 1))
        else:
            lines.extend(emit_container(child, depth + 1))
    lines.append(f"{pad}}}")
    return lines


def emit_tab(tab: dict, depth: int) -> list[str]:
    pad = INDENT * depth
    emoji = tab.get("emoji", "")
    name = tab.get("name", tab["id"])
    label = f"{emoji} {name}" if emoji else name
    parts = [f'tab name={kdl_str(label)}']
    if tab.get("focus"):
        parts.append("focus=true")
    tab_cwd = tab.get("cwd")
    if tab_cwd:
        parts.append(f'cwd={kdl_str(tab_cwd)}')
    lines = [f"{pad}{' '.join(parts)} {{"]
    for pane in tab.get("panes", []):
        if common.pane_is_leaf(pane):
            lines.extend(emit_leaf(pane, depth + 1))
        else:
            lines.extend(emit_container(pane, depth + 1))
    lines.append(f"{pad}}}")
    return lines


def emit_zellij(wf: dict, defaults: dict) -> str:
    lines: list[str] = []
    lines.append(f"// dist/zellij/{wf['id']}.kdl")
    lines.append("// Auto-generated from manifest/workflows/%s.yaml — do not edit." % wf["id"])
    lines.append("// Launch: zellij -n %s -s %s" % (wf["id"], wf["id"]))
    lines.append("")
    lines.append("layout {")
    lines.append("")
    # status bar template
    show_sb = defaults.get("defaults", {}).get("show_statusbar", True)
    lines.append(f"{INDENT}default_tab_template {{")
    lines.append(f"{INDENT}{INDENT}pane size=1 borderless=true {{")
    lines.append(f'{INDENT}{INDENT}{INDENT}plugin location="zellij:tab-bar"')
    lines.append(f"{INDENT}{INDENT}}}")
    lines.append(f"{INDENT}{INDENT}children")
    if show_sb:
        lines.append(f"{INDENT}{INDENT}pane size=2 borderless=true {{")
        lines.append(f'{INDENT}{INDENT}{INDENT}plugin location="zellij:status-bar"')
        lines.append(f"{INDENT}{INDENT}}}")
    lines.append(f"{INDENT}}}")
    lines.append("")

    for tab in wf.get("tabs", []):
        if tab.get("tmux_only", False):
            continue
        lines.extend(emit_tab(tab, 1))
        lines.append("")

    lines.append("}")
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit("usage: gen-zellij.py <workflow_id>")
    wf_id = sys.argv[1]
    defaults = common.load_defaults()
    wf = common.load_workflow(wf_id)
    sys.stdout.write(emit_zellij(wf, defaults))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
